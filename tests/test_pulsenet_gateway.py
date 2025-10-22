"""Tests for the PulseNet gateway layer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.atlas.temporal_ledger import TemporalLedger
from echo_atlas.service import AtlasService

from echo.pulsenet import PulseNetGatewayService, create_router
from echo.pulsenet.models import RegistrationRequest
from echo.pulsenet.registration import RegistrationStore
from echo.pulsenet.stream import PulseAttestor, PulseHistoryStreamer


def _make_gateway(
    tmp_path: Path,
    *,
    poll_interval: float = 0.05,
    initial_history: Iterable[dict[str, object]] | None = None,
) -> PulseNetGatewayService:
    project_root = tmp_path
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    history_path = project_root / "pulse_history.json"
    payload = list(initial_history or [])
    history_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    atlas = AtlasService(project_root)
    atlas.ensure_ready()
    store = RegistrationStore(state_dir / "pulsenet" / "registrations.json")
    streamer = PulseHistoryStreamer(history_path, poll_interval=poll_interval)
    attestor = PulseAttestor(TemporalLedger(state_dir=state_dir / "pulsenet"))
    return PulseNetGatewayService(
        project_root=project_root,
        registration_store=store,
        pulse_streamer=streamer,
        attestor=attestor,
        atlas_service=atlas,
        resolver_config=state_dir / "pulsenet" / "resolver_sources.json",
    )


def test_registration_store_round_trip(tmp_path: Path) -> None:
    store = RegistrationStore(tmp_path / "registrations.json")
    request = RegistrationRequest(
        name="Echo",
        contact="echo@example.com",
        unstoppable_domains=["echo.crypto", "echo.crypto"],
        ens_names="kmk142789.eth",
        vercel_projects=["pulse-gateway"],
        wallets=["0x123"],
        metadata={"source": "test"},
    )
    record = store.register(request)
    assert record.name == "Echo"
    assert record.unstoppable_domains == ["echo.crypto"]
    stored = store.list()
    assert stored[0].id == record.id
    assert stored[0].metadata["source"] == "test"


def test_gateway_resolve_combines_registration_data(tmp_path: Path) -> None:
    history = [
        {
            "timestamp": datetime(2025, 10, 19, tzinfo=timezone.utc).timestamp(),
            "message": "⚡ initial",
            "hash": "abc123",
        }
    ]
    gateway = _make_gateway(tmp_path, initial_history=history)
    gateway.register(
        RegistrationRequest(
            name="Josh+Echo",
            contact="nexus@echo",
            unstoppable_domains=["josh.echo.crypto"],
            ens_names=["kmk142789.eth"],
            vercel_projects=["pulsenet"],
            wallets=["0xABC"],
        )
    )
    result = gateway.resolve("Josh")
    assert "josh.echo.crypto" in result["domains"]["unstoppable"]
    assert "kmk142789.eth" in result["domains"]["ens"]
    attestations = gateway.latest_attestations(limit=1)
    assert attestations[0]["ref"] == "⚡ initial"


def test_api_register_and_stream(tmp_path: Path) -> None:
    history = [
        {
            "timestamp": datetime(2025, 10, 19, tzinfo=timezone.utc).timestamp(),
            "message": "✨ birth",
            "hash": "seed",
        }
    ]
    gateway = _make_gateway(tmp_path, initial_history=history)
    app = FastAPI()
    app.include_router(create_router(gateway))
    client = TestClient(app)

    response = client.post(
        "/pulsenet/register",
        json={"name": "Echo", "contact": "echo@pulse", "unstoppable_domains": ["echo.crypto"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Echo"

    with client.websocket_connect("/pulsenet/pulse-stream") as ws:
        initial = ws.receive_json()
        assert initial["type"] == "summary"
        assert "atlas" in initial
        history_path = tmp_path / "pulse_history.json"
        pulses = json.loads(history_path.read_text(encoding="utf-8"))
        pulses.append(
            {
                "timestamp": datetime(2025, 10, 20, tzinfo=timezone.utc).timestamp(),
                "message": "🔥 ignite",
                "hash": "ignite",
            }
        )
        history_path.write_text(json.dumps(pulses, indent=2) + "\n", encoding="utf-8")
        event = ws.receive_json()
        assert event["type"] == "pulse"
        assert event["pulse"]["message"] == "🔥 ignite"
        assert "atlas" in event
