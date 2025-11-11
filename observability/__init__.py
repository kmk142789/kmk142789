"""Helpers for configuring telemetry across Echo services."""

from .otel import configure_otel

__all__ = ["configure_otel"]
