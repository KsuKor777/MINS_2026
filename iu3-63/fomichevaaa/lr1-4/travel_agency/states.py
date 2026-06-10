from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from .exceptions import PaymentError, StateTransitionError, ValidationError

if TYPE_CHECKING:
    from .models import Booking


class BookingState(ABC):
    code = "unknown"
    label = "Неизвестный"

    def start_processing(self, booking: Booking) -> None:
        self._deny("перевести в работу")

    def mark_ready(self, booking: Booking) -> None:
        self._deny("отметить готовой")

    def issue(self, booking: Booking) -> None:
        self._deny("выдать")

    def cancel(self, booking: Booking) -> None:
        self._deny("отменить")

    def is_active(self) -> bool:
        return self.code not in {"issued", "cancelled"}

    def _transition(self, booking: Booking, new_status: str) -> None:
        booking.transition_to(new_status)

    def _deny(self, action: str) -> None:
        raise StateTransitionError(f"Нельзя {action} бронь в статусе '{self.label}'.")


class NewBookingState(BookingState):
    code = "new"
    label = "Новая"

    def start_processing(self, booking: Booking) -> None:
        self._transition(booking, "in_progress")

    def cancel(self, booking: Booking) -> None:
        self._transition(booking, "cancelled")


class InProgressBookingState(BookingState):
    code = "in_progress"
    label = "В работе"

    def mark_ready(self, booking: Booking) -> None:
        self._transition(booking, "ready")

    def cancel(self, booking: Booking) -> None:
        self._transition(booking, "cancelled")


class ReadyBookingState(BookingState):
    code = "ready"
    label = "Готова"

    def issue(self, booking: Booking) -> None:
        if booking.outstanding_balance > 0:
            raise PaymentError("Нельзя выдать бронь при наличии задолженности")
        self._transition(booking, "issued")


class IssuedBookingState(BookingState):
    code = "issued"
    label = "Выдана"


class CancelledBookingState(BookingState):
    code = "cancelled"
    label = "Отменена"


_STATES: dict[str, BookingState] = {
    "new": NewBookingState(),
    "in_progress": InProgressBookingState(),
    "ready": ReadyBookingState(),
    "issued": IssuedBookingState(),
    "cancelled": CancelledBookingState(),
}


def get_booking_state(status: str) -> BookingState:
    try:
        return _STATES[status]
    except KeyError as error:
        raise ValidationError(f"Неизвестный статус брони: {status}") from error
