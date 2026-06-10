from __future__ import annotations

from decimal import Decimal

from .exceptions import InputError, TravelAgencyError
from .legacy_marketing import LegacyMarketingHub
from .pricing import (
    CompositeDiscountPolicy,
    GroupDiscountPolicy,
    LoyaltyDiscountPolicy,
    PriceCalculator,
)
from .repositories import (
    InMemoryBookingRepository,
    InMemoryClientRepository,
    InMemoryTourRepository,
)
from .services import BookingService, CatalogService, ClientService


class TravelAgencyCLI:
    def __init__(
        self,
        catalog_service: CatalogService,
        client_service: ClientService,
        booking_service: BookingService,
        marketing_service: LegacyMarketingHub,
    ) -> None:
        self._catalog_service = catalog_service
        self._client_service = client_service
        self._booking_service = booking_service
        self._marketing_service = marketing_service

    def run(self) -> None:
        actions = {
            "1": self._show_tours,
            "2": self._show_clients,
            "3": self._register_client,
            "4": self._create_booking,
            "5": self._show_bookings,
            "6": self._show_marketing_report,
            "0": self._exit_program,
        }

        while True:
            self._print_menu()
            choice = input("Выберите пункт меню: ").strip()
            action = actions.get(choice)
            if action is None:
                print("Неизвестная команда\n")
                continue

            try:
                action()
            except TravelAgencyError as error:
                print(f"Ошибка: {error}\n")

    def _print_menu(self) -> None:
        print("Туристическое агентство")
        print("1. Показать каталог туров")
        print("2. Показать клиентов")
        print("3. Зарегистрировать клиента")
        print("4. Забронировать тур")
        print("5. Показать бронирования")
        print("6. Показать маркетинговый отчет")
        print("0. Выход")

    def _show_tours(self) -> None:
        tours = self._catalog_service.list_tours()
        if not tours:
            print("Каталог пуст\n")
            return

        print("\nКаталог туров:")
        for tour in tours:
            print(
                f"[{tour.tour_id}] {tour.title} , {tour.destination}, "
                f"{tour.days} дн., {tour.base_price} руб., мест: {tour.available_seats}"
            )
        print()

    def _show_clients(self) -> None:
        clients = self._client_service.list_clients()
        if not clients:
            print("Список клиентов пуст\n")
            return

        print("\nКлиенты:")
        for client in clients:
            print(f"[{client.client_id}] {client.full_name}, статус: {client.loyalty_level}")
        print()

    def _register_client(self) -> None:
        full_name = input("Введите ФИО клиента: ").strip()
        loyalty_level = input(
            "Введите статус клиента (standard/silver/gold), по умолчанию standard: "
        ).strip()
        if not loyalty_level:
            loyalty_level = "standard"
        client = self._client_service.register_client(full_name, loyalty_level)
        print(f"Клиент зарегистрирован. ID клиента: {client.client_id}\n")

    def _create_booking(self) -> None:
        client_id = self._read_int("Введите ID клиента: ")
        tour_id = self._read_int("Введите ID тура: ")
        travelers_count = self._read_int("Введите количество путешественников: ")
        booking = self._booking_service.create_booking(client_id, tour_id, travelers_count)
        discount_percent = booking.discount_rate * Decimal("100")
        print(
            f"Бронирование создано, ID: {booking.booking_id}, "
            f"итоговая стоимость: {booking.total_price} руб., "
            f"скидка: {discount_percent}%.\n"
        )

    def _show_bookings(self) -> None:
        bookings = self._booking_service.list_bookings()
        if not bookings:
            print("Бронирований нет\n")
            return

        print("\nБронирования:")
        for booking in bookings:
            discount_percent = booking.discount_rate * Decimal("100")
            print(
                f"[{booking.booking_id}] {booking.client_name} -> {booking.tour_title} | "
                f"чел.: {booking.travelers_count} | сумма: {booking.total_price} руб. | "
                f"скидка: {discount_percent}%"
            )
        print()

    def _show_marketing_report(self) -> None:
        print()
        print(self._marketing_service.render_cli_report())
        print()

    def _exit_program(self) -> None:
        raise SystemExit

    def _read_int(self, prompt: str) -> int:
        raw_value = input(prompt).strip()
        try:
            return int(raw_value)
        except ValueError as error:
            raise InputError("Ожидалось целое число") from error


def build_demo_cli() -> TravelAgencyCLI:
    tour_repository = InMemoryTourRepository()
    client_repository = InMemoryClientRepository()
    booking_repository = InMemoryBookingRepository()

    catalog_service = CatalogService(tour_repository)
    client_service = ClientService(client_repository)

    discount_policy = CompositeDiscountPolicy(
        policies=[LoyaltyDiscountPolicy(), GroupDiscountPolicy()]
    )

    price_calculator = PriceCalculator(discount_policy)

    booking_service = BookingService(
        booking_repository=booking_repository,
        client_repository=client_repository,
        tour_repository=tour_repository,
        price_calculator=price_calculator,
    )
    marketing_service = LegacyMarketingHub(
        booking_repository=booking_repository,
        client_repository=client_repository,
        tour_repository=tour_repository,
    )

    catalog_service.add_tour("Сочи Лайт", "Сочи", 7, "35000", 10)
    catalog_service.add_tour("Алтай Актив", "Алтай", 10, "48000", 8)
    catalog_service.add_tour("Казань Weekend", "Казань", 3, "18000", 12)

    client_service.register_client("Иван Иванов", "standard")
    client_service.register_client("Петр Петров", "silver")
    client_service.register_client("Федор Федоров", "gold")

    return TravelAgencyCLI(catalog_service, client_service, booking_service, marketing_service)
