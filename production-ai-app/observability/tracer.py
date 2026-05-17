from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.config import settings


def setup_tracing() -> None:
    resource = Resource.create(
        {"service.name": settings.app_name, "deployment.environment": settings.environment}
    )
    provider = TracerProvider(resource=resource)

    if settings.otel_exporter_otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
        )
    elif settings.environment == "development":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)


def get_tracer(name: str = __name__) -> trace.Tracer:
    return trace.get_tracer(name)


@contextmanager
def span(name: str, attributes: dict[str, Any] | None = None):
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as s:
        if attributes:
            for k, v in attributes.items():
                s.set_attribute(k, str(v))
        yield s
