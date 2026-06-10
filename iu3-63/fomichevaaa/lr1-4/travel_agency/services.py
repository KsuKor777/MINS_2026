from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .exceptions import BookingError, TravelAgencyError
from .models import Booking, Client, Tour, to_money, validate_positive_int
from .notifications import NotificationEvent, NotificationPublisher, NotificationStatsObserver
from .pricing import PriceCalculator
from .repositories import (
    BookingRepository,
    ClientRepository,
    NotificationRepository,
    TourRepository,
)
from .unit_of_work import InMemoryUnitOfWork, UnitOfWork

UnitOfWorkFactory = Callable[[], UnitOfWork]


class IdGenerator:
    def __init__(self, start: int = 1) -> None:
        self._next_id = start

    def next_id(self) -> int:
        current_value = self._next_id
        self._next_id += 1
        return current_value


class CatalogService:
    def __init__(self, repository: TourRepository, id_generator: IdGenerator | None = None) -> None:
        self._repository = repository
        self._id_generator = id_generator or IdGenerator()

    def add_tour(
        self,
        title: str,
        destination: str,
        days: int,
        base_price: Decimal | int | float | str,
        available_seats: int,
    ) -> Tour:
        tour = Tour(
            tour_id=self._id_generator.next_id(),
            title=title,
            destination=destination,
            days=days,
            base_price=to_money(base_price),
            available_seats=available_seats,
        )
        self._repository.add(tour)
        return tour

    def list_tours(self) -> list[Tour]:
        return self._repository.list_all()

    def get_tour(self, tour_id: int) -> Tour:
        return self._repository.get_by_id(tour_id)


class ClientService:
    def __init__(self, repository: ClientRepository, id_generator: IdGenerator | None = None) -> None:
        self._repository = repository
        self._id_generator = id_generator or IdGenerator()

    def register_client(self, full_name: str, loyalty_level: str = "standard") -> Client:
        client = Client(
            client_id=self._id_generator.next_id(),
            full_name=full_name,
            loyalty_level=loyalty_level,
        )
        self._repository.add(client)
        return client

    def list_clients(self) -> list[Client]:
        return self._repository.list_all()

    def get_client(self, client_id: int) -> Client:
        return self._repository.get_by_id(client_id)


@dataclass(slots=True)
class BookingView:
    booking_id: int
    client_name: str
    tour_title: str
    travelers_count: int
    total_price: Decimal
    discount_rate: Decimal
    status: str
    amount_paid: Decimal
    outstanding_balance: Decimal
    hold_until: date


class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        client_repository: ClientRepository,
        tour_repository: TourRepository,
        price_calculator: PriceCalculator,
        id_generator: IdGenerator | None = None,
        unit_of_work_factory: UnitOfWorkFactory | None = None,
        notification_publisher: NotificationPublisher | None = None,
    ) -> None:
        self._booking_repository = booking_repository
        self._client_repository = client_repository
        self._tour_repository = tour_repository
        self._price_calculator = price_calculator
        self._id_generator = id_generator or IdGenerator()
        self._unit_of_work_factory = unit_of_work_factory or InMemoryUnitOfWork
        self._notification_publisher = notification_publisher or NotificationPublisher()

    def create_booking(
        self,
        client_id: int,
        tour_id: int,
        travelers_count: int,
        amount_paid: Decimal | int | float | str = Decimal("0.00"),
        hold_days: int = 3,
    ) -> Booking:
        validate_positive_int(hold_days, "hold_days")
        client = self._client_repository.get_by_id(client_id)
        tour = self._tour_repository.get_by_id(tour_id)
        total_price, discount_rate = self._price_calculator.calculate(tour, client, travelers_count)

        booking = Booking(
            booking_id=self._id_generator.next_id(),
            client_id=client_id,
            tour_id=tour_id,
            travelers_count=travelers_count,
            total_price=total_price,
            discount_rate=discount_rate,
            amount_paid=to_money(amount_paid),
            hold_until=date.today() + timedelta(days=hold_days),
        )

        try:
            with self._unit_of_work_factory() as unit_of_work:
                tour.reserve_seats(travelers_count)
                unit_of_work.register_rollback(lambda: self._rollback_reserved_seats(tour, travelers_count))
                self._tour_repository.update(tour)

                self._booking_repository.add(booking)
                unit_of_work.register_rollback(lambda: self._booking_repository.remove(booking.booking_id))

                unit_of_work.commit()
        except TravelAgencyError:
            raise
        except Exception as error:
            raise BookingError("Не удалось завершить бронирование безопасно") from error

        self._publish_status_notification(booking)
        self._publish_debt_notification_if_needed(booking)
        return booking

    def start_booking_processing(self, booking_id: int) -> Booking:
        return self._change_booking_status(booking_id, "start_processing")

    def mark_booking_ready(self, booking_id: int) -> Booking:
        return self._change_booking_status(booking_id, "mark_ready")

    def issue_booking(self, booking_id: int) -> Booking:
        return self._change_booking_status(booking_id, "issue")

    def cancel_booking(self, booking_id: int) -> Booking:
        booking = self._booking_repository.get_by_id(booking_id)
        previous_status = booking.status
        tour = self._tour_repository.get_by_id(booking.tour_id)

        try:
            with self._unit_of_work_factory() as unit_of_work:
                booking.cancel()
                unit_of_work.register_rollback(
                    lambda: self._restore_booking_status(booking, previous_status)
                )
                self._booking_repository.update(booking)

                tour.release_seats(booking.travelers_count)
                unit_of_work.register_rollback(
                    lambda: self._rollback_released_seats(tour, booking.travelers_count)
                )
                self._tour_repository.update(tour)

                unit_of_work.commit()
        except TravelAgencyError:
            raise
        except Exception as error:
            raise BookingError("Не удалось отменить бронирование безопасно") from error

        self._publish_status_notification(booking)
        return booking

    def record_payment(self, booking_id: int, amount: Decimal | int | float | str) -> Booking:
        booking = self._booking_repository.get_by_id(booking_id)
        booking.pay(amount)
        self._booking_repository.update(booking)
        self._notification_publisher.notify(
            NotificationEvent(
                event_type="payment_received",
                message=(
                    f"Получена оплата по брони {booking.booking_id}. "
                    f"Оплачено: {booking.amount_paid} руб., остаток: {booking.outstanding_balance} руб."
                ),
                booking_id=booking.booking_id,
            )
        )
        return booking

    def check_expired_bookings(self, reference_date: date | None = None) -> list[Booking]:
        current_date = reference_date or date.today()
        expired_bookings: list[Booking] = []

        for booking in self._booking_repository.list_all():
            if booking.deadline_notified:
                continue
            if not booking.state.is_active():
                continue
            if booking.hold_until >= current_date:
                continue

            booking.mark_deadline_notified()
            self._booking_repository.update(booking)
            self._notification_publisher.notify(
                NotificationEvent(
                    event_type="booking_expired",
                    message=(
                        f"Срок действия брони {booking.booking_id} истек "
                        f"{booking.hold_until.isoformat()}."
                    ),
                    booking_id=booking.booking_id,
                )
            )
            expired_bookings.append(booking)

        return expired_bookings

    def list_bookings(self) -> list[BookingView]:
        booking_views: list[BookingView] = []
        for booking in self._booking_repository.list_all():
            client = self._client_repository.get_by_id(booking.client_id)
            tour = self._tour_repository.get_by_id(booking.tour_id)
            booking_views.append(
                BookingView(
                    booking_id=booking.booking_id,
                    client_name=client.full_name,
                    tour_title=tour.title,
                    travelers_count=booking.travelers_count,
                    total_price=booking.total_price,
                    discount_rate=booking.discount_rate,
                    status=booking.status_label,
                    amount_paid=booking.amount_paid,
                    outstanding_balance=booking.outstanding_balance,
                    hold_until=booking.hold_until,
                )
            )
        return booking_views

    def _change_booking_status(self, booking_id: int, transition_method_name: str) -> Booking:
        booking = self._booking_repository.get_by_id(booking_id)
        transition = getattr(booking, transition_method_name)
        transition()
        self._booking_repository.update(booking)
        self._publish_status_notification(booking)
        return booking

    def _publish_status_notification(self, booking: Booking) -> None:
        self._notification_publisher.notify(
            NotificationEvent(
                event_type="status_changed",
                message=f"Бронь {booking.booking_id} переведена в статус '{booking.status_label}'.",
                booking_id=booking.booking_id,
            )
        )

    def _publish_debt_notification_if_needed(self, booking: Booking) -> None:
        if booking.outstanding_balance <= Decimal("0.00"):
            return
        self._notification_publisher.notify(
            NotificationEvent(
                event_type="debt_detected",
                message=(
                    f"По брони {booking.booking_id} есть задолженность "
                    f"{booking.outstanding_balance} руб."
                ),
                booking_id=booking.booking_id,
            )
        )

    def _rollback_reserved_seats(self, tour: Tour, seats: int) -> None:
        tour.release_seats(seats)
        self._tour_repository.update(tour)

    def _rollback_released_seats(self, tour: Tour, seats: int) -> None:
        tour.reserve_seats(seats)
        self._tour_repository.update(tour)

    def _restore_booking_status(self, booking: Booking, previous_status: str) -> None:
        booking.transition_to(previous_status)
        self._booking_repository.update(booking)


class NotificationService:
    def __init__(
        self,
        repository: NotificationRepository,
        stats_observer: NotificationStatsObserver | None = None,
    ) -> None:
        self._repository = repository
        self._stats_observer = stats_observer

    def list_notifications(self):
        return sorted(
            self._repository.list_all(),
            key=lambda notification: notification.notification_id,
            reverse=True,
        )

    def get_statistics(self) -> dict[str, int]:
        if self._stats_observer is None:
            return {}
        return self._stats_observer.snapshot()
