from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from .exceptions import AvailabilityError, PaymentError, ValidationError
from .states import get_booking_state

MONEY_PRECISION = Decimal("0.01")
VALID_LOYALTY_LEVELS = {"standard", "silver", "gold"}


def to_money(value: Decimal | int | float | str) -> Decimal:
    try:
        return Decimal(str(value)).quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as error:
        raise ValidationError(f"Некорректное денежное значение: {value}") from error


def validate_positive_int(value: int, field_name: str) -> None:
    if value <= 0:
        raise ValidationError(f"Поле '{field_name}' должно быть положительным числом")


def validate_not_blank(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValidationError(f"Поле '{field_name}' не должно быть пустым")


@dataclass(slots=True)
class Tour:
    tour_id: int
    title: str
    destination: str
    days: int
    base_price: Decimal
    available_seats: int

    def __post_init__(self) -> None:
        validate_positive_int(self.tour_id, "tour_id")
        validate_not_blank(self.title, "title")
        validate_not_blank(self.destination, "destination")
        validate_positive_int(self.days, "days")
        validate_positive_int(self.available_seats, "available_seats")
        self.base_price = to_money(self.base_price)
        if self.base_price <= Decimal("0"):
            raise ValidationError("Начальная стоимость тура должна быть больше нуля")

    def reserve_seats(self, seats: int) -> None:
        validate_positive_int(seats, "seats")
        if seats > self.available_seats:
            raise AvailabilityError(
                f"Недостаточно мест для тура '{self.title}'. Доступно: {self.available_seats}"
            )
        self.available_seats -= seats

    def release_seats(self, seats: int) -> None:
        validate_positive_int(seats, "seats")
        self.available_seats += seats


@dataclass(slots=True)
class Client:
    client_id: int
    full_name: str
    loyalty_level: str = "standard"

    def __post_init__(self) -> None:
        validate_positive_int(self.client_id, "client_id")
        validate_not_blank(self.full_name, "full_name")
        normalized_loyalty_level = self.loyalty_level.strip().lower()
        if normalized_loyalty_level not in VALID_LOYALTY_LEVELS:
            raise ValidationError(
                "Уровень лояльности должен быть одним из значений: standard, silver, gold"
            )
        self.loyalty_level = normalized_loyalty_level


@dataclass(slots=True)
class Booking:
    booking_id: int
    client_id: int
    tour_id: int
    travelers_count: int
    total_price: Decimal
    discount_rate: Decimal
    amount_paid: Decimal = Decimal("0.00")
    status: str = "new"
    hold_until: date = field(default_factory=lambda: date.today() + timedelta(days=3))
    deadline_notified: bool = False

    def __post_init__(self) -> None:
        validate_positive_int(self.booking_id, "booking_id")
        validate_positive_int(self.client_id, "client_id")
        validate_positive_int(self.tour_id, "tour_id")
        validate_positive_int(self.travelers_count, "travelers_count")
        self.total_price = to_money(self.total_price)
        self.discount_rate = Decimal(str(self.discount_rate))
        self.amount_paid = to_money(self.amount_paid)
        if self.total_price <= Decimal("0"):
            raise ValidationError("Стоимость бронирования должна быть больше нуля")
        if not Decimal("0") <= self.discount_rate <= Decimal("1"):
            raise ValidationError("Скидка должна находиться в диапазоне от 0 до 1")
        if self.amount_paid < Decimal("0"):
            raise PaymentError("Оплаченная сумма не может быть отрицательной")
        if self.amount_paid > self.total_price:
            raise PaymentError("Оплаченная сумма не может превышать стоимость бронирования")
        if not isinstance(self.hold_until, date):
            raise ValidationError("Срок действия брони должен быть объектом date")
        get_booking_state(self.status)

    @property
    def state(self):
        return get_booking_state(self.status)

    @property
    def status_label(self) -> str:
        return self.state.label

    @property
    def outstanding_balance(self) -> Decimal:
        return to_money(self.total_price - self.amount_paid)

    def transition_to(self, new_status: str) -> None:
        get_booking_state(new_status)
        self.status = new_status

    def pay(self, amount: Decimal | int | float | str) -> None:
        payment_amount = to_money(amount)
        if payment_amount <= Decimal("0"):
            raise PaymentError("Сумма оплаты должна быть больше нуля")
        new_amount_paid = to_money(self.amount_paid + payment_amount)
        if new_amount_paid > self.total_price:
            raise PaymentError("Сумма оплаты не должна превышать стоимость бронирования")
        self.amount_paid = new_amount_paid

    def start_processing(self) -> None:
        self.state.start_processing(self)

    def mark_ready(self) -> None:
        self.state.mark_ready(self)

    def issue(self) -> None:
        self.state.issue(self)

    def cancel(self) -> None:
        self.state.cancel(self)

    def mark_deadline_notified(self) -> None:
        self.deadline_notified = True
