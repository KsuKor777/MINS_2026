from __future__ import annotations

from datetime import date
from decimal import Decimal

from travel_agency.models import Booking, Client, Tour, to_money
from travel_agency.services import BookingView

from . import travel_agency_pb2


def client_to_proto(client: Client) -> travel_agency_pb2.ClientMessage:
    return travel_agency_pb2.ClientMessage(
        client_id=client.client_id,
        full_name=client.full_name,
        loyalty_level=client.loyalty_level,
    )


def client_from_proto(message: travel_agency_pb2.ClientMessage) -> Client:
    return Client(
        client_id=message.client_id,
        full_name=message.full_name,
        loyalty_level=message.loyalty_level,
    )


def tour_to_proto(tour: Tour) -> travel_agency_pb2.TourMessage:
    return travel_agency_pb2.TourMessage(
        tour_id=tour.tour_id,
        title=tour.title,
        destination=tour.destination,
        days=tour.days,
        base_price=str(tour.base_price),
        available_seats=tour.available_seats,
    )


def tour_from_proto(message: travel_agency_pb2.TourMessage) -> Tour:
    validated_seats = message.available_seats if message.available_seats > 0 else 1
    tour = Tour(
        tour_id=message.tour_id,
        title=message.title,
        destination=message.destination,
        days=message.days,
        base_price=to_money(message.base_price),
        available_seats=validated_seats,
    )
    tour.available_seats = message.available_seats
    return tour


def booking_to_proto(booking: Booking) -> travel_agency_pb2.BookingMessage:
    return travel_agency_pb2.BookingMessage(
        booking_id=booking.booking_id,
        client_id=booking.client_id,
        tour_id=booking.tour_id,
        travelers_count=booking.travelers_count,
        total_price=str(booking.total_price),
        discount_rate=str(booking.discount_rate),
        amount_paid=str(booking.amount_paid),
        status=booking.status,
        status_label=booking.status_label,
        hold_until=booking.hold_until.isoformat(),
        deadline_notified=booking.deadline_notified,
        outstanding_balance=str(booking.outstanding_balance),
    )


def booking_view_to_proto(view: BookingView) -> travel_agency_pb2.BookingViewMessage:
    return travel_agency_pb2.BookingViewMessage(
        booking_id=view.booking_id,
        client_name=view.client_name,
        tour_title=view.tour_title,
        travelers_count=view.travelers_count,
        total_price=str(view.total_price),
        discount_rate=str(view.discount_rate),
        status=view.status,
        amount_paid=str(view.amount_paid),
        outstanding_balance=str(view.outstanding_balance),
        hold_until=view.hold_until.isoformat(),
    )


def parse_reference_date(raw_value: str) -> date | None:
    if not raw_value:
        return None
    return date.fromisoformat(raw_value)


def decimal_to_string(value: Decimal | str) -> str:
    return str(value)
