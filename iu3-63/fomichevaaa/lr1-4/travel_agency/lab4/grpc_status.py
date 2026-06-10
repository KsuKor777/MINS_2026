from __future__ import annotations

import grpc

from travel_agency.exceptions import (
    AvailabilityError,
    BookingError,
    DuplicateEntityError,
    EntityNotFoundError,
    InputError,
    PaymentError,
    PricingError,
    StateTransitionError,
    TravelAgencyError,
    UnitOfWorkError,
    ValidationError,
)

from .exceptions import ReferenceServiceUnavailableError
from .tracing import TRACE_ID_HEADER, get_trace_id


def exception_to_status_code(error: TravelAgencyError) -> grpc.StatusCode:
    if isinstance(error, (InputError, ValidationError, PricingError)):
        return grpc.StatusCode.INVALID_ARGUMENT
    if isinstance(error, EntityNotFoundError):
        return grpc.StatusCode.NOT_FOUND
    if isinstance(error, DuplicateEntityError):
        return grpc.StatusCode.ALREADY_EXISTS
    if isinstance(error, (AvailabilityError, PaymentError, StateTransitionError)):
        return grpc.StatusCode.FAILED_PRECONDITION
    if isinstance(error, ReferenceServiceUnavailableError):
        return grpc.StatusCode.UNAVAILABLE
    if isinstance(error, (BookingError, UnitOfWorkError)):
        return grpc.StatusCode.INTERNAL
    return grpc.StatusCode.FAILED_PRECONDITION


def abort_with_domain_error(context, error: TravelAgencyError) -> None:
    context.set_trailing_metadata(((TRACE_ID_HEADER, get_trace_id()),))
    context.abort(exception_to_status_code(error), str(error))


def extract_trace_id_from_rpc_error(error: grpc.RpcError) -> str | None:
    for metadata in (error.trailing_metadata(), error.initial_metadata()):
        if metadata is None:
            continue
        for key, value in metadata:
            if key == TRACE_ID_HEADER:
                return value
    return None


def rpc_error_to_domain_error(method_name: str, error: grpc.RpcError) -> TravelAgencyError:
    code = error.code()
    details = error.details() or f"RPC {method_name} завершился ошибкой"
    if code in {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED}:
        return ReferenceServiceUnavailableError(details)
    if code == grpc.StatusCode.INVALID_ARGUMENT:
        return ValidationError(details)
    if code == grpc.StatusCode.NOT_FOUND:
        return EntityNotFoundError(details)
    if code == grpc.StatusCode.ALREADY_EXISTS:
        return DuplicateEntityError(details)
    if code == grpc.StatusCode.FAILED_PRECONDITION:
        return TravelAgencyError(details)
    if code == grpc.StatusCode.INTERNAL:
        return BookingError(details)
    return TravelAgencyError(f"Ошибка сетевого вызова {method_name}: {details}")
