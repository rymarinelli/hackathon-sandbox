from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import TracerProvider as TracerProviderType

from gateway.settings import Settings


def configure_tracing(settings: Settings) -> Optional[TracerProviderType]:
    """Configure OpenTelemetry tracing when an OTLP endpoint is provided."""

    if not settings.otlp_endpoint:
        return None

    resource = Resource.create({"service.name": settings.otel_service_name})
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint, insecure=settings.otlp_insecure)
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    trace.set_tracer_provider(tracer_provider)
    return tracer_provider
