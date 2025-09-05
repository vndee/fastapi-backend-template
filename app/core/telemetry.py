import logging
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    pass

from opentelemetry import _logs, trace
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer

from app.core.settings import settings

TRACER_SCOPE = "application"


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(settings, "LOG_LEVEL", "INFO"))

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(settings, "LOG_LEVEL", "INFO"))
        formatter = logging.Formatter(settings.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)


def setup_telemetry(
    service_name: str = settings.OTEL_SERVICE_NAME,
    service_version: str = settings.APP_VERSION,
) -> Tuple[Tracer, TracerProvider]:
    """Initialize OpenTelemetry for HyperDX"""
    setup_logging()

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    headers = _parse_headers(settings.OTEL_EXPORTER_OTLP_HEADERS)

    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        headers=headers,
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    logger_provider = LoggerProvider(resource=resource)
    _logs.set_logger_provider(logger_provider)

    log_exporter = OTLPLogExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        headers=headers,
    )

    log_processor = BatchLogRecordProcessor(log_exporter)
    logger_provider.add_log_record_processor(log_processor)

    otel_handler = LoggingHandler(
        level=logging.NOTSET,
        logger_provider=logger_provider,
    )

    root_logger = logging.getLogger()
    if not any(isinstance(h, LoggingHandler) for h in root_logger.handlers):
        root_logger.addHandler(otel_handler)

    if not hasattr(LoggingInstrumentor, "_instrumented"):
        LoggingInstrumentor().instrument(set_logging_format=False)
        LoggingInstrumentor._instrumented = True

    tracer = trace.get_tracer(TRACER_SCOPE)

    return tracer, tracer_provider


def get_tracer(scope: str = TRACER_SCOPE) -> Tracer:
    """Get the consolidated tracer for the application"""
    return trace.get_tracer(scope)


def _parse_headers(headers_str: str) -> Tuple[Tuple[str, str], ...]:
    """Parse headers string into tuple format for gRPC"""
    headers = []
    if headers_str:
        for header in headers_str.split(","):
            if "=" in header:
                key, value = header.strip().split("=", 1)
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                headers.append((key, value))

    return tuple(headers)
