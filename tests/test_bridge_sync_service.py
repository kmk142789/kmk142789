from __future__ import annotations

from pathlib import Path
from typing import Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.bridge import BridgeSyncService, EchoBridgeAPI
from echo.bridge.router import create_router
from echo.bridge.service import BridgeConnector, SyncEvent


class DummyConnector:
    name = "dummy"
    action = "emit"

    def __init__(self) -> None:
        self.calls = 0

    def build_event(self, decision: Mapping[str, object]) -> SyncEvent | None:
        self.calls += 1
        cycle = None
        if isinstance(decision, Mapping):
            inputs = decision.get("inputs")
            if isinstance(inputs, Mapping):
                digest = inputs.get("cycle_digest")
                if isinstance(digest, Mapping):
                    cycle = digest.get("cycle")
        payload = {"cycle": cycle}
        return SyncEvent(
            connector=self.name,
            action=self.action,
            status="ok",
            detail="dummy",
            payload=payload,
        )


def _decision_payload() -> Mapping[str, object]:
    return {
        "inputs": {"cycle_digest": {"cycle": 7}},
        "coherence": {"score": 0.42},
        "manifest": {"path": "manifest.json"},
    }


def test_bridge_sync_service_writes_history(tmp_path: Path) -> None:
    connector: BridgeConnector = DummyConnector()
    service = BridgeSyncService(state_dir=tmp_path, connectors=[connector])

    operations = service.sync(_decision_payload())

    assert operations
    assert operations[0]["connector"] == "dummy"

    history = service.history()
    assert history
    assert history[-1]["connector"] == "dummy"
    assert history[-1]["cycle"] == "7"


def test_bridge_sync_endpoint_returns_operations(tmp_path: Path) -> None:
    connector: BridgeConnector = DummyConnector()
    service = BridgeSyncService(state_dir=tmp_path, connectors=[connector])
    service.sync(_decision_payload())

    app = FastAPI()
    app.include_router(create_router(api=EchoBridgeAPI(), sync_service=service))
    client = TestClient(app)

    response = client.get("/bridge/sync")
    assert response.status_code == 200
    data = response.json()
    assert data["operations"]
    assert data["operations"][0]["connector"] == "dummy"
