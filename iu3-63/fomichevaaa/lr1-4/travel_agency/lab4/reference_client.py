from __future__ import annotations

import grpc

from travel_agency.exceptions import TravelAgencyError
from travel_agency.models import Client, Tour
from travel_agency.repositories import ClientRepository, TourRepository

from . import travel_agency_pb2, travel_agency_pb2_grpc
from .grpc_status import rpc_error_to_domain_error
from .serializers import client_from_proto, tour_from_proto, tour_to_proto
from .tracing import build_metadata

_REFERENCE_TIMEOUT_SECONDS = 2.0


def _ensure_success(success: bool, message: str) -> None:
    if success:
        return
    raise TravelAgencyError(message)


class ReferenceServiceChannel:
    def __init__(self, target: str) -> None:
        self._channel = grpc.insecure_channel(target)
        self._stub = travel_agency_pb2_grpc.ReferenceServiceStub(self._channel)

    @property
    def stub(self) -> travel_agency_pb2_grpc.ReferenceServiceStub:
        return self._stub

    def close(self) -> None:
        self._channel.close()


class GrpcClientRepositoryAdapter(ClientRepository):
    def __init__(self, reference_channel: ReferenceServiceChannel) -> None:
        self._channel = reference_channel

    def add(self, client: Client) -> None:
        request = travel_agency_pb2.RegisterClientRequest(
            full_name=client.full_name,
            loyalty_level=client.loyalty_level,
        )
        try:
            response = self._channel.stub.RegisterClient(
                request,
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("RegisterClient", error) from error
        _ensure_success(response.success, response.message)

    def get_by_id(self, client_id: int) -> Client:
        request = travel_agency_pb2.ClientIdRequest(client_id=client_id)
        try:
            response = self._channel.stub.GetClient(
                request,
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("GetClient", error) from error
        _ensure_success(response.success, response.message)
        return client_from_proto(response.client)

    def list_all(self) -> list[Client]:
        try:
            response = self._channel.stub.ListClients(
                travel_agency_pb2.Empty(),
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("ListClients", error) from error
        _ensure_success(response.success, response.message)
        return [client_from_proto(item) for item in response.clients]


class GrpcTourRepositoryAdapter(TourRepository):
    def __init__(self, reference_channel: ReferenceServiceChannel) -> None:
        self._channel = reference_channel

    def add(self, tour: Tour) -> None:
        request = travel_agency_pb2.AddTourRequest(
            title=tour.title,
            destination=tour.destination,
            days=tour.days,
            base_price=str(tour.base_price),
            available_seats=tour.available_seats,
        )
        try:
            response = self._channel.stub.AddTour(
                request,
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("AddTour", error) from error
        _ensure_success(response.success, response.message)

    def get_by_id(self, tour_id: int) -> Tour:
        request = travel_agency_pb2.TourIdRequest(tour_id=tour_id)
        try:
            response = self._channel.stub.GetTour(
                request,
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("GetTour", error) from error
        _ensure_success(response.success, response.message)
        return tour_from_proto(response.tour)

    def list_all(self) -> list[Tour]:
        try:
            response = self._channel.stub.ListTours(
                travel_agency_pb2.Empty(),
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("ListTours", error) from error
        _ensure_success(response.success, response.message)
        return [tour_from_proto(item) for item in response.tours]

    def update(self, tour: Tour) -> None:
        request = travel_agency_pb2.UpdateTourRequest(tour=tour_to_proto(tour))
        try:
            response = self._channel.stub.UpdateTour(
                request,
                timeout=_REFERENCE_TIMEOUT_SECONDS,
                metadata=build_metadata(),
            )
        except grpc.RpcError as error:
            raise rpc_error_to_domain_error("UpdateTour", error) from error
        _ensure_success(response.success, response.message)
