"""Coordinated PulseNet gateway service."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator, Mapping

from fastapi import WebSocket, WebSocketDisconnect

from echo_atlas.service import AtlasService

from .models import PulseHistoryEntry, RegistrationRecord, RegistrationRequest
from .registration import RegistrationStore
from .resolver import AtlasProvider, CrossDomainResolver
from .stream import PulseAttestor, PulseHistoryStreamer
from .atlas import AtlasAttestationResolver


class PulseNetGatewayService:
    """Glue layer combining registration, streaming, attestation, and resolution."""

    def __init__(
        self,
        *,
        project_root: Path,
        registration_store: RegistrationStore,
        pulse_streamer: PulseHistoryStreamer,
        attestor: PulseAttestor,
        atlas_service: AtlasService,
        resolver_config: Path | None = None,
        atlas_resolver: AtlasAttestationResolver | None = None,
    ) -> None:
        self._project_root = project_root
        self._store = registration_store
        self._streamer = pulse_streamer
        self._attestor = attestor
        self._atlas_service = atlas_service
        self._atlas_resolver = atlas_resolver
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
        self._attestor.ensure(existing)

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

    def atlas_wallets(self) -> list[Mapping[str, Any]]:
        if not self._atlas_resolver:
            return []
        return [dict(item) for item in self._atlas_resolver.wallets()]

    async def iter_pulses(self) -> AsyncIterator[Mapping[str, Any]]:
        async for entry in self._streamer.subscribe():
            attestation = self._attestor.attest(entry)
            yield self._build_event(entry, attestation)

    async def stream_pulses(self, websocket: WebSocket) -> None:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "summary",
                "data": self.pulse_summary(),
                "atlas": self.atlas_wallets(),
            }
        )
        try:
            async for event in self.iter_pulses():
                await websocket.send_json(
                    {
                        "type": "pulse",
                        **event,
                    }
                )
        except WebSocketDisconnect:  # pragma: no cover - fastapi handles disconnect semantics
            return
        except asyncio.CancelledError:  # pragma: no cover - connection closed abruptly
            return

    def _build_event(self, entry: PulseHistoryEntry, attestation: Mapping[str, Any]) -> Mapping[str, Any]:
        metadata = None
        if self._atlas_resolver:
            for key in (attestation.get("proof_id"), entry.hash, entry.message.split(":")[-1]):
                if isinstance(key, str):
                    resolved = self._atlas_resolver.lookup(key)
                    if resolved:
                        metadata = resolved.as_dict()
                        break
        return {
            "pulse": entry.to_dict(),
            "attestation": attestation,
            "summary": self.pulse_summary(),
            "atlas": metadata,
        }


__all__ = ["PulseNetGatewayService"]
