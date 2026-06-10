from __future__ import annotations

from datetime import date, timedelta
import unittest

from travel_agency.exceptions import BookingError, StateTransitionError
from travel_agency.legacy_marketing import LegacyMarketingHub
from travel_agency.notifications import (
    NotificationLogObserver,
    NotificationPublisher,
    NotificationStatsObserver,
)
from travel_agency.pricing import (
    CompositeDiscountPolicy,
    GroupDiscountPolicy,
    LoyaltyDiscountPolicy,
    PriceCalculator,
)
from travel_agency.repositories import (
    InMemoryBookingRepository,
    InMemoryClientRepository,
    InMemoryNotificationRepository,
    InMemoryTourRepository,
)
from travel_agency.services import (
    BookingService,
    CatalogService,
    ClientService,
    IdGenerator,
    NotificationService,
)
from travel_agency.unit_of_work import InMemoryUnitOfWork


class FailingBookingRepository(InMemoryBookingRepository):
    def add(self, booking) -> None:  # type: ignore[override]
        raise RuntimeError("Имитация сбоя при сохранении брони")


class TravelAgencyPatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tour_repository = InMemoryTourRepository()
        self.client_repository = InMemoryClientRepository()
        self.booking_repository = InMemoryBookingRepository()
        self.notification_repository = InMemoryNotificationRepository()

        self.catalog_service = CatalogService(self.tour_repository)
        self.client_service = ClientService(self.client_repository)

        notification_publisher = NotificationPublisher()
        self.notification_stats_observer = NotificationStatsObserver()
        notification_publisher.attach(
            NotificationLogObserver(
                repository=self.notification_repository,
                id_generator=IdGenerator(),
            )
        )
        notification_publisher.attach(self.notification_stats_observer)

        self.booking_service = BookingService(
            booking_repository=self.booking_repository,
            client_repository=self.client_repository,
            tour_repository=self.tour_repository,
            price_calculator=PriceCalculator(
                CompositeDiscountPolicy(
                    policies=[LoyaltyDiscountPolicy(), GroupDiscountPolicy()]
                )
            ),
            unit_of_work_factory=InMemoryUnitOfWork,
            notification_publisher=notification_publisher,
        )
        self.notification_service = NotificationService(
            repository=self.notification_repository,
            stats_observer=self.notification_stats_observer,
        )
        self.legacy_marketing = LegacyMarketingHub(
            booking_repository=self.booking_repository,
            client_repository=self.client_repository,
            tour_repository=self.tour_repository,
        )

        self.tour = self.catalog_service.add_tour("Тестовый тур", "Казань", 5, "10000", 5)
        self.client = self.client_service.register_client("Тестовый клиент", "gold")

    def test_state_transitions_and_notifications(self) -> None:
        booking = self.booking_service.create_booking(
            self.client.client_id,
            self.tour.tour_id,
            2,
            amount_paid="0",
            hold_days=3,
        )

        booking = self.booking_service.start_booking_processing(booking.booking_id)
        booking = self.booking_service.mark_booking_ready(booking.booking_id)
        booking = self.booking_service.record_payment(booking.booking_id, "17400")
        booking = self.booking_service.issue_booking(booking.booking_id)

        self.assertEqual(booking.status, "issued")

        event_types = [
            notification.event_type for notification in self.notification_service.list_notifications()
        ]
        self.assertIn("status_changed", event_types)
        self.assertIn("debt_detected", event_types)
        self.assertIn("payment_received", event_types)

    def test_cancel_after_ready_is_forbidden(self) -> None:
        booking = self.booking_service.create_booking(
            self.client.client_id,
            self.tour.tour_id,
            1,
            amount_paid="9000",
            hold_days=3,
        )
        self.booking_service.start_booking_processing(booking.booking_id)
        self.booking_service.mark_booking_ready(booking.booking_id)

        with self.assertRaises(StateTransitionError):
            self.booking_service.cancel_booking(booking.booking_id)

    def test_unit_of_work_rolls_back_reserved_seats(self) -> None:
        failing_service = BookingService(
            booking_repository=FailingBookingRepository(),
            client_repository=self.client_repository,
            tour_repository=self.tour_repository,
            price_calculator=PriceCalculator(
                CompositeDiscountPolicy(
                    policies=[LoyaltyDiscountPolicy(), GroupDiscountPolicy()]
                )
            ),
            unit_of_work_factory=InMemoryUnitOfWork,
        )

        with self.assertRaises(BookingError):
            failing_service.create_booking(self.client.client_id, self.tour.tour_id, 2)

        self.assertEqual(self.catalog_service.get_tour(self.tour.tour_id).available_seats, 5)

    def test_expired_booking_notifies_once(self) -> None:
        booking = self.booking_service.create_booking(
            self.client.client_id,
            self.tour.tour_id,
            1,
            amount_paid="0",
            hold_days=1,
        )

        expired = self.booking_service.check_expired_bookings(
            reference_date=date.today() + timedelta(days=2)
        )
        expired_again = self.booking_service.check_expired_bookings(
            reference_date=date.today() + timedelta(days=2)
        )

        self.assertEqual([item.booking_id for item in expired], [booking.booking_id])
        self.assertEqual(expired_again, [])

    def test_legacy_marketing_module_generates_isolated_report(self) -> None:
        welcome_client = self.client_service.register_client("Новый клиент", "standard")
        self.booking_service.create_booking(
            self.client.client_id,
            self.tour.tour_id,
            2,
            amount_paid="0",
            hold_days=3,
        )

        vip_offer = self.legacy_marketing.build_personal_offer(
            self.client.client_id,
            reference_date=date.today(),
        )
        welcome_offer = self.legacy_marketing.build_personal_offer(
            welcome_client.client_id,
            reference_date=date.today(),
        )
        report = self.legacy_marketing.render_cli_report(reference_date=date.today())

        self.assertEqual(vip_offer["segment"], "vip")
        self.assertEqual(vip_offer["recommended_tour"], "Тестовый тур")
        self.assertEqual(welcome_offer["segment"], "welcome")
        self.assertIn("Тестовый клиент", report)
        self.assertIn("Новый клиент", report)
        self.assertIn("Итог кампании", report)
        self.assertEqual(len(self.booking_service.list_bookings()), 1)


if __name__ == "__main__":
    unittest.main()
