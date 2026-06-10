from __future__ import annotations

import contextvars
import logging
import uuid

import grpc

TRACE_ID_HEADER = "trace-id"

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    return _trace_id_var.get()


def set_trace_id(trace_id: str) -> contextvars.Token[str]:
    return _trace_id_var.set(trace_id)


def ensure_trace_id(trace_id: str | None = None) -> str:
    candidate = trace_id or get_trace_id()
    if candidate and candidate != "-":
        return candidate
    generated = uuid.uuid4().hex
    _trace_id_var.set(generated)
    return generated


def build_metadata() -> list[tuple[str, str]]:
    return [(TRACE_ID_HEADER, ensure_trace_id())]


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def configure_logging(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(name)s [trace_id=%(trace_id)s] %(levelname)s %(message)s"
        )
    )
    handler.addFilter(TraceIdFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


class TraceServerInterceptor(grpc.ServerInterceptor):
    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None or handler.unary_unary is None:
            return handler

        metadata = dict(handler_call_details.invocation_metadata or [])
        method_name = handler_call_details.method

        def traced_unary_unary(request, context):
            trace_id = metadata.get(TRACE_ID_HEADER) or uuid.uuid4().hex
            token = set_trace_id(trace_id)
            try:
                self._logger.info("Started %s", method_name)
                response = handler.unary_unary(request, context)
                self._logger.info("Finished %s", method_name)
                return response
            finally:
                _trace_id_var.reset(token)

        return grpc.unary_unary_rpc_method_handler(
            traced_unary_unary,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
