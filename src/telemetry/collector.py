"""Telemetry collection utilities enforcing privacy guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, MutableMapping, Optional

from .schema import ConsentState, TelemetryContext, TelemetryEvent
from .storage import TelemetryStorage


@dataclass
class TelemetryCollector:
    """Collects telemetry events when consent is granted."""

    storage: TelemetryStorage
    enabled: bool = True
    metadata: MutableMapping[str, str] = field(default_factory=dict)

    def record(
        self,
        *,
        event_type: str,
        context: TelemetryContext,
        payload: Optional[Mapping[str, object]] = None,
        allowed_fields: Optional[Iterable[str]] = None,
    ) -> Optional[TelemetryEvent]:
        """Record an event if telemetry is enabled and consent allows it."""

        if not self.enabled:
            return None
        if not context.consent_state.allows_collection:
            return None

        payload_mapping = dict(payload or {})
        event = TelemetryEvent(
            event_type=event_type,
            context=context,
            payload=payload_mapping,
        )
        if allowed_fields is not None:
            event = event.redact(set(allowed_fields))
        self.storage.write(event)
        return event

    def flush(self) -> None:
        """Flush buffered telemetry events to durable storage."""

        self.storage.flush()

    def annotate_session(self, context: TelemetryContext) -> TelemetryContext:
        """Attach metadata about the collector session to the context."""

        session_label = self.metadata.get("session_label")
        if session_label and context.session_label != session_label:
            return TelemetryContext(
                id=context.pseudonymous_id,
                consent_state=context.consent_state,
                consent_recorded_at=context.consent_recorded_at,
                session_label=session_label,
            )
        return context

    def consent_audit_entry(self, context: TelemetryContext) -> Mapping[str, object]:
        """Produce an auditable consent record for reporting."""

        return {
            "pseudonymous_id": context.pseudonymous_id,
            "consent_state": context.consent_state.value,
            "consent_recorded_at": (
                context.consent_recorded_at.astimezone(timezone.utc).isoformat()
                if context.consent_recorded_at
                else None
            ),
            "session_label": context.session_label,
            "collector_metadata": dict(self.metadata),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def disable(self) -> None:
        self.enabled = False

    def enable(self) -> None:
        self.enabled = True


__all__ = ["TelemetryCollector"]
