"""OpenTelemetry bootstrap utilities shared across services."""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Mapping, MutableMapping

from opentelemetry import _logs, metrics, trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as GrpcMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as GrpcSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter as GrpcLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as HttpMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HttpSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter as HttpLogExporter


def _is_grpc_endpoint(endpoint: str) -> bool:
    """Determine whether the OTLP endpoint expects gRPC or HTTP."""

    return not endpoint.endswith(":4318") and not endpoint.startswith("http://") and not endpoint.startswith("https://")


def _normalise_endpoint(endpoint: str) -> str:
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        return endpoint
    return f"http://{endpoint}"


def _resource(service_name: str, **attrs: str) -> Resource:
    base: MutableMapping[str, str] = {
        "service.name": service_name,
        "service.namespace": attrs.pop("service_namespace", "echo"),
        "service.version": attrs.pop("service_version", os.getenv("SERVICE_VERSION", "0.1.0")),
        "deployment.environment": attrs.pop(
            "deployment_environment", os.getenv("DEPLOYMENT_ENVIRONMENT", "development")
        ),
    }
    for key, value in attrs.items():
        if value:
            base[key] = value
    user_attrs = os.getenv("OTEL_RESOURCE_ATTRIBUTES")
    if user_attrs:
        for chunk in user_attrs.split(","):
            if "=" in chunk:
                key, value = chunk.split("=", 1)
                base[key.strip()] = value.strip()
    return Resource.create(base)


@lru_cache(maxsize=None)
def _exporter_endpoints() -> Mapping[str, str]:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector:4317")
    return {
        "traces": os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", endpoint),
        "metrics": os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", endpoint),
        "logs": os.getenv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", endpoint),
    }


_CONFIGURED = False


def configure_otel(
    service_name: str,
    *,
    service_namespace: str | None = None,
    service_version: str | None = None,
    deployment_environment: str | None = None,
    auto_attach_logger: bool = True,
) -> None:
    """Initialise OTLP exporters for traces, metrics, and logs.

    The configuration honours standard OTEL_* environment variables.  The first
    call wires providers and exporters; subsequent invocations become no-ops so
    modules can safely invoke :func:`configure_otel` during import.
    """

    global _CONFIGURED
    if _CONFIGURED:
        return

    resource = _resource(
        service_name,
        service_namespace=service_namespace or "echo",
        service_version=service_version,
        deployment_environment=deployment_environment,
    )

    endpoints = _exporter_endpoints()

    traces_endpoint = endpoints["traces"]
    metrics_endpoint = endpoints["metrics"]
    logs_endpoint = endpoints["logs"]

    insecure = os.getenv("OTEL_EXPORTER_OTLP_INSECURE", "true").lower() == "true"

    tracer_provider = TracerProvider(resource=resource)
    if _is_grpc_endpoint(traces_endpoint):
        tracer_provider.add_span_processor(
            BatchSpanProcessor(GrpcSpanExporter(endpoint=traces_endpoint, insecure=insecure))
        )
    else:
        tracer_provider.add_span_processor(
            BatchSpanProcessor(HttpSpanExporter(endpoint=_normalise_endpoint(traces_endpoint), insecure=insecure))
        )
    trace.set_tracer_provider(tracer_provider)

    if _is_grpc_endpoint(metrics_endpoint):
        metric_exporter = GrpcMetricExporter(endpoint=metrics_endpoint, insecure=insecure)
    else:
        metric_exporter = HttpMetricExporter(endpoint=_normalise_endpoint(metrics_endpoint), insecure=insecure)

    reader = PeriodicExportingMetricReader(metric_exporter)
    meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(meter_provider)

    if _is_grpc_endpoint(logs_endpoint):
        log_exporter = GrpcLogExporter(endpoint=logs_endpoint, insecure=insecure)
    else:
        log_exporter = HttpLogExporter(endpoint=_normalise_endpoint(logs_endpoint), insecure=insecure)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    _logs.set_logger_provider(logger_provider)

    if auto_attach_logger:
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
        root = logging.getLogger()
        root.addHandler(handler)

    _CONFIGURED = True


__all__ = ["configure_otel"]
