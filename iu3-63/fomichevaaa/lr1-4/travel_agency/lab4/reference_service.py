from __future__ import annotations

from concurrent import futures
from dataclasses import dataclass

import grpc

from travel_agency.exceptions import TravelAgencyError
from travel_agency.models import to_money, validate_not_blank, validate_positive_int
from travel_agency.repositories import InMemoryClientRepository, InMemoryTourRepository
from travel_agency.services import CatalogService, ClientService

from . import travel_agency_pb2, travel_agency_pb2_grpc
from .serializers import client_to_proto, tour_to_proto
from .tracing import TraceServerInterceptor, configure_logging, get_trace_id


@dataclass(slots=True)
class ReferenceServiceContainer:
    catalog_service: CatalogService
    client_service: ClientService
    tour_repository: InMemoryTourRepository
    client_repository: InMemoryClientRepository


def build_reference_container(seed_demo_data: bool = True) -> ReferenceServiceContainer:
    tour_repository = InMemoryTourRepository()
    client_repository = InMemoryClientRepository()
    catalog_service = CatalogService(tour_repository)
    client_service = ClientService(client_repository)

    if seed_demo_data:
        catalog_service.add_tour("Сочи Лайт", "Сочи", 7, "35000", 10)
        catalog_service.add_tour("Алтай Актив", "Алтай", 10, "48000", 8)
        catalog_service.add_tour("Казань Weekend", "Казань", 3, "18000", 12)

        client_service.register_client("Иван Иванов", "standard")
        client_service.register_client("Петр Петров", "silver")
        client_service.register_client("Федор Федоров", "gold")

    return ReferenceServiceContainer(
        catalog_service=catalog_service,
        client_service=client_service,
        tour_repository=tour_repository,
        client_repository=client_repository,
    )


class ReferenceServiceServicer(travel_agency_pb2_grpc.ReferenceServiceServicer):
    def __init__(self, container: ReferenceServiceContainer, logger_name: str = "ReferenceService") -> None:
        self._container = container
        self._logger = configure_logging(logger_name)

    def AddTour(self, request, context): #grpc методы
        del context
        try:
            tour = self._container.catalog_service.add_tour(
                title=request.title,
                destination=request.destination,
                days=request.days,
                base_price=request.base_price,
                available_seats=request.available_seats,
            )
            return travel_agency_pb2.TourResponse(
                success=True,
                message="Тур добавлен",
                trace_id=get_trace_id(),
                tour=tour_to_proto(tour),
            )
        except TravelAgencyError as error:
            self._logger.info("AddTour failed: %s", error)
            return travel_agency_pb2.TourResponse(
                success=False,
                message=str(error),
                trace_id=get_trace_id(),
            )

    def UpdateTour(self, request, context):
        del context
        try:
            source = request.tour
            stored = self._container.tour_repository.get_by_id(source.tour_id)
            validate_positive_int(source.tour_id, "tour_id")
            validate_not_blank(source.title, "title")
            validate_not_blank(source.destination, "destination")
            validate_positive_int(source.days, "days")
            if source.available_seats < 0:
                raise TravelAgencyError("Количество мест не может быть отрицательным")

            stored.title = source.title
            stored.destination = source.destination
            stored.days = source.days
            stored.base_price = to_money(source.base_price)
            stored.available_seats = source.available_seats
            self._container.tour_repository.update(stored)
            return travel_agency_pb2.TourResponse(
                success=True,
                message="Тур обновлен",
                trace_id=get_trace_id(),
                tour=tour_to_proto(stored),
            )
        except TravelAgencyError as error:
            self._logger.info("UpdateTour failed: %s", error)
            return travel_agency_pb2.TourResponse(
                success=False,
                message=str(error),
                trace_id=get_trace_id(),
            )

    def GetTour(self, request, context):
        del context
        try:
            tour = self._container.catalog_service.get_tour(request.tour_id)
            return travel_agency_pb2.TourResponse(
                success=True,
                message="OK",
                trace_id=get_trace_id(),
                tour=tour_to_proto(tour),
            )
        except TravelAgencyError as error:
            self._logger.info("GetTour failed: %s", error)
            return travel_agency_pb2.TourResponse(
                success=False,
                message=str(error),
                trace_id=get_trace_id(),
            )

    def ListTours(self, request, context):
        del request
        del context
        tours = self._container.catalog_service.list_tours()
        return travel_agency_pb2.TourListResponse(
            success=True,
            message="OK",
            trace_id=get_trace_id(),
            tours=[tour_to_proto(item) for item in tours],
        )

    def RegisterClient(self, request, context):
        del context
        try:
            client = self._container.client_service.register_client(
                full_name=request.full_name,
                loyalty_level=request.loyalty_level or "standard",
            )
            return travel_agency_pb2.ClientResponse(
                success=True,
                message="Клиент зарегистрирован",
                trace_id=get_trace_id(),
                client=client_to_proto(client),
            )
        except TravelAgencyError as error:
            self._logger.info("RegisterClient failed: %s", error)
            return travel_agency_pb2.ClientResponse(
                success=False,
                message=str(error),
                trace_id=get_trace_id(),
            )

    def GetClient(self, request, context):
        del context
        try:
            client = self._container.client_service.get_client(request.client_id)
            return travel_agency_pb2.ClientResponse(
                success=True,
                message="OK",
                trace_id=get_trace_id(),
                client=client_to_proto(client),
            )
        except TravelAgencyError as error:
            self._logger.info("GetClient failed: %s", error)
            return travel_agency_pb2.ClientResponse(
                success=False,
                message=str(error),
                trace_id=get_trace_id(),
            )

    def ListClients(self, request, context):
        del request
        del context
        clients = self._container.client_service.list_clients()
        return travel_agency_pb2.ClientListResponse(
            success=True,
            message="OK",
            trace_id=get_trace_id(),
            clients=[client_to_proto(item) for item in clients],
        )


def create_reference_server(
    address: str,
    seed_demo_data: bool = True,
    logger_name: str = "ReferenceService",
):
    logger = configure_logging(logger_name)
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[TraceServerInterceptor(logger)],
    )
    container = build_reference_container(seed_demo_data=seed_demo_data)
    servicer = ReferenceServiceServicer(container=container, logger_name=logger_name)
    travel_agency_pb2_grpc.add_ReferenceServiceServicer_to_server(servicer, server)
    bound_port = server.add_insecure_port(address)
    return server, bound_port, container


def serve_reference_service(
    address: str = "127.0.0.1:50052",
    seed_demo_data: bool = True,
    logger_name: str = "ReferenceService",
) -> None:
    server, _, _ = create_reference_server(
        address=address,
        seed_demo_data=seed_demo_data,
        logger_name=logger_name,
    )
    logger = configure_logging(logger_name)
    server.start()
    logger.info("Reference service started on %s", address)
    server.wait_for_termination()
