from __future__ import annotations

from concurrent import futures
from dataclasses import dataclass

import grpc

from travel_agency.exceptions import TravelAgencyError
from travel_agency.legacy_marketing import LegacyMarketingHub
from travel_agency.notifications import NotificationPublisher
from travel_agency.pricing import CompositeDiscountPolicy, GroupDiscountPolicy, LoyaltyDiscountPolicy, PriceCalculator
from travel_agency.repositories import InMemoryBookingRepository
from travel_agency.services import BookingService
from travel_agency.unit_of_work import InMemoryUnitOfWork

from . import travel_agency_pb2, travel_agency_pb2_grpc
from .exceptions import ReferenceServiceUnavailableError
from .grpc_status import abort_with_domain_error
from .reference_client import (
    GrpcClientRepositoryAdapter,
    GrpcTourRepositoryAdapter,
    ReferenceServiceChannel,
)
from .serializers import booking_to_proto, booking_view_to_proto, parse_reference_date
from .tracing import TraceServerInterceptor, configure_logging, get_trace_id

_REFERENCE_UNAVAILABLE_MESSAGE = (
    "Справочный сервис временно недоступен. Повторите попытку позже."
)


@dataclass(slots=True)
class CoreServiceContainer:
    booking_service: BookingService
    marketing_service: LegacyMarketingHub
    reference_channel: ReferenceServiceChannel


def build_core_container(reference_target: str) -> CoreServiceContainer:
    reference_channel = ReferenceServiceChannel(reference_target)
    client_repository = GrpcClientRepositoryAdapter(reference_channel)
    tour_repository = GrpcTourRepositoryAdapter(reference_channel)
    booking_repository = InMemoryBookingRepository()

    notification_publisher = NotificationPublisher()
    booking_service = BookingService(
        booking_repository=booking_repository,
        client_repository=client_repository,
        tour_repository=tour_repository,
        price_calculator=PriceCalculator(
            CompositeDiscountPolicy(
                policies=[LoyaltyDiscountPolicy(), GroupDiscountPolicy()]
            )
        ),
        unit_of_work_factory=InMemoryUnitOfWork,
        notification_publisher=notification_publisher,
    )

    marketing_service = LegacyMarketingHub(
        booking_repository=booking_repository,
        client_repository=client_repository,
        tour_repository=tour_repository,
    )
    return CoreServiceContainer(
        booking_service=booking_service,
        marketing_service=marketing_service,
        reference_channel=reference_channel,
    )


class CoreServiceServicer(travel_agency_pb2_grpc.CoreServiceServicer):
    def __init__(self, container: CoreServiceContainer, logger_name: str = "CoreService") -> None:
        self._container = container
        self._logger = configure_logging(logger_name)

    def CreateBooking(self, request, context):
        return self._booking_operation(
            lambda: self._container.booking_service.create_booking(
                request.client_id,
                request.tour_id,
                request.travelers_count,
                amount_paid=request.amount_paid or "0.00",
                hold_days=request.hold_days or 3,
            ),
            success_message="Бронирование создано",
            context=context,
        )

    def StartBookingProcessing(self, request, context):
        return self._booking_operation(
            lambda: self._container.booking_service.start_booking_processing(request.booking_id),
            success_message="Бронь переведена в работу",
            context=context,
        )

    def MarkBookingReady(self, request, context):
        return self._booking_operation(
            lambda: self._container.booking_service.mark_booking_ready(request.booking_id),
            success_message="Бронь отмечена готовой",
            context=context,
        )

    def IssueBooking(self, request, context):
        return self._booking_operation(
            lambda: self._container.booking_service.issue_booking(request.booking_id),
            success_message="Бронь выдана",
            context=context,
        )

    def CancelBooking(self, request, context):
        return self._booking_operation(
            lambda: self._container.booking_service.cancel_booking(request.booking_id),
            success_message="Бронь отменена",
            context=context,
        )

    def RecordPayment(self, request, context):
        return self._booking_operation(
            lambda: self._container.booking_service.record_payment(request.booking_id, request.amount),
            success_message="Оплата сохранена",
            context=context,
        )

    def ListBookings(self, request, context):
        del request
        try:
            bookings = self._container.booking_service.list_bookings()
            return travel_agency_pb2.BookingListResponse(
                success=True,
                message="OK",
                trace_id=get_trace_id(),
                bookings=[booking_view_to_proto(item) for item in bookings],
            )
        except ReferenceServiceUnavailableError as error:
            self._logger.info("ListBookings failed due to reference outage: %s", error)
            abort_with_domain_error(
                context,
                ReferenceServiceUnavailableError(_REFERENCE_UNAVAILABLE_MESSAGE),
            )
        except TravelAgencyError as error:
            self._logger.info("ListBookings failed: %s", error)
            abort_with_domain_error(context, error)

    def CheckExpiredBookings(self, request, context):
        try:
            reference_date = parse_reference_date(request.reference_date)
            bookings = self._container.booking_service.check_expired_bookings(reference_date)
            views = self._container.booking_service.list_bookings()
            expired_ids = {item.booking_id for item in bookings}
            filtered = [item for item in views if item.booking_id in expired_ids]
            return travel_agency_pb2.BookingListResponse(
                success=True,
                message="Проверка завершена",
                trace_id=get_trace_id(),
                bookings=[booking_view_to_proto(item) for item in filtered],
            )
        except ReferenceServiceUnavailableError as error:
            self._logger.info("CheckExpiredBookings failed due to reference outage: %s", error)
            abort_with_domain_error(
                context,
                ReferenceServiceUnavailableError(_REFERENCE_UNAVAILABLE_MESSAGE),
            )
        except TravelAgencyError as error:
            self._logger.info("CheckExpiredBookings failed: %s", error)
            abort_with_domain_error(context, error)

    def RenderMarketingReport(self, request, context):
        del request
        try:
            report = self._container.marketing_service.render_cli_report()
            return travel_agency_pb2.TextResponse(
                success=True,
                message="OK",
                trace_id=get_trace_id(),
                text=report,
            )
        except ReferenceServiceUnavailableError as error:
            self._logger.info("RenderMarketingReport failed due to reference outage: %s", error)
            abort_with_domain_error(
                context,
                ReferenceServiceUnavailableError(_REFERENCE_UNAVAILABLE_MESSAGE),
            )
        except TravelAgencyError as error:
            self._logger.info("RenderMarketingReport failed: %s", error)
            abort_with_domain_error(context, error)

    def _booking_operation(self, callback, success_message: str, context):
        try:
            booking = callback()
            return travel_agency_pb2.BookingOperationResponse(
                success=True,
                message=success_message,
                trace_id=get_trace_id(),
                booking=booking_to_proto(booking),
            )
        except ReferenceServiceUnavailableError as error:
            self._logger.info("Booking operation failed due to reference outage: %s", error)
            abort_with_domain_error(
                context,
                ReferenceServiceUnavailableError(_REFERENCE_UNAVAILABLE_MESSAGE),
            )
        except TravelAgencyError as error:
            self._logger.info("Booking operation failed: %s", error)
            abort_with_domain_error(context, error)


def create_core_server(
    address: str,
    reference_target: str,
    logger_name: str = "CoreService",
):
    logger = configure_logging(logger_name)
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[TraceServerInterceptor(logger)],
    )
    container = build_core_container(reference_target=reference_target)
    servicer = CoreServiceServicer(container=container, logger_name=logger_name)
    travel_agency_pb2_grpc.add_CoreServiceServicer_to_server(servicer, server)
    bound_port = server.add_insecure_port(address)
    return server, bound_port, container


def serve_core_service(
    address: str = "127.0.0.1:50051",
    reference_target: str = "127.0.0.1:50052",
    logger_name: str = "CoreService",
) -> None:
    server, _, _ = create_core_server(
        address=address,
        reference_target=reference_target,
        logger_name=logger_name,
    )
    logger = configure_logging(logger_name)
    server.start()
    logger.info("Core service started on %s, reference target is %s", address, reference_target)
    server.wait_for_termination()
