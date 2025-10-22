"""Coordinated PulseNet gateway service."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Mapping

from fastapi import WebSocket, WebSocketDisconnect

from echo_atlas.service import AtlasService

from .models import RegistrationRecord, RegistrationRequest
from .persistence import PulseEventStore
from .registration import RegistrationStore
from .resolver import AtlasProvider, CrossDomainResolver
from .stream import PulseAttestor, PulseHistoryStreamer


class PulseNetGatewayService:
    """Glue layer combining registration, streaming, attestation, and resolution."""

    def __init__(
        self,
        *,
        project_root: Path,
        registration_store: RegistrationStore,
        event_store: PulseEventStore,
        pulse_streamer: PulseHistoryStreamer,
        attestor: PulseAttestor,
        atlas_service: AtlasService,
        resolver_config: Path | None = None,
    ) -> None:
        self._project_root = project_root
        self._store = registration_store
        self._events = event_store
        self._streamer = pulse_streamer
        self._attestor = attestor
        self._atlas_service = atlas_service
        self._resolver = CrossDomainResolver(
            AtlasProvider(atlas_service),
            registration_store.list(),
            config_path=resolver_config,
        )
        self._bootstrap()

    # ------------------------------------------------------------------
    # Bootstrap helpers
    # ------------------------------------------------------------------
    def _bootstrap(self) -> None:
        existing = self._streamer.load_entries()
        self._streamer.mark_seen(existing)
        attestations = self._attestor.ensure(existing)
        for entry, attestation in zip(existing, attestations):
            self._events.record(entry, attestation)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self, request: RegistrationRequest) -> Mapping[str, Any]:
        record = self._store.register(request)
        self._resolver.update_registrations(self._store.list())
        return record.as_dict()

    def registrations(self) -> list[Mapping[str, Any]]:
        return [record.as_dict() for record in self._store.list()]

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------
    def resolve(self, query: str) -> Mapping[str, Any]:
        return self._resolver.resolve(query).model_dump()

    # ------------------------------------------------------------------
    # Attestation + pulse reporting
    # ------------------------------------------------------------------
    def latest_attestations(self, *, limit: int = 10) -> list[Mapping[str, Any]]:
        return self._attestor.latest(limit=limit)

    def pulse_summary(self) -> Mapping[str, Any]:
        summary = self._streamer.daily_summary()
        return {
            "total_days": summary.total_days,
            "total_entries": summary.total_entries,
            "busiest_day": summary.busiest_day.__dict__ if summary.busiest_day else None,
            "quietest_day": summary.quietest_day.__dict__ if summary.quietest_day else None,
            "activity": [item.__dict__ for item in summary.activity],
        }

    def replay(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
        xpub: str | None = None,
        fingerprint: str | None = None,
        attestation_id: str | None = None,
    ) -> list[Mapping[str, Any]]:
        records = self._events.replay(
            limit=limit,
            offset=offset,
            xpub=xpub,
            fingerprint=fingerprint,
            attestation_id=attestation_id,
        )
        return [record.to_dict() for record in records]

    async def stream_pulses(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json({"type": "summary", "data": self.pulse_summary()})
        try:
            async for entry in self._streamer.subscribe():
                attestation = self._attestor.attest(entry)
                self._events.record(entry, attestation)
                await websocket.send_json(
                    {
                        "type": "pulse",
                        "pulse": entry.to_dict(),
                        "attestation": attestation,
                        "summary": self.pulse_summary(),
                    }
                )
        except WebSocketDisconnect:  # pragma: no cover - fastapi handles disconnect semantics
            return
        except asyncio.CancelledError:  # pragma: no cover - connection closed abruptly
            return


__all__ = ["PulseNetGatewayService"]
