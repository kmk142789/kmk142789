from __future__ import annotations

from pathlib import Path
from typing import Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.bridge import BridgeSyncService, EchoBridgeAPI
from echo.bridge.router import create_router
from echo.bridge.service import (
    BridgeConnector,
    DomainInventoryConnector,
    SyncEvent,
    UnstoppableDomainConnector,
    VercelDeployConnector,
)


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


class AlternateConnector(DummyConnector):
    name = "alternate"


def _decision_payload(
    *,
    cycle: str | int = 7,
    coherence: float = 0.42,
    manifest_path: str = "manifest.json",
    registrations: list[Mapping[str, object]] | None = None,
) -> Mapping[str, object]:
    inputs: dict[str, object] = {"cycle_digest": {"cycle": cycle}}
    if registrations is not None:
        inputs["registrations"] = registrations
    return {
        "inputs": inputs,
        "coherence": {"score": coherence},
        "manifest": {"path": manifest_path},
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


def test_bridge_sync_service_filters_history_by_connector(tmp_path: Path) -> None:
    connectors: list[BridgeConnector] = [DummyConnector(), AlternateConnector()]
    service = BridgeSyncService(state_dir=tmp_path, connectors=connectors)
    service.sync(_decision_payload())

    dummy_only = service.history(connector="dummy")
    assert dummy_only
    assert all(entry["connector"] == "dummy" for entry in dummy_only)

    none = service.history(connector="missing")
    assert none == []


def test_bridge_sync_endpoint_supports_connector_filter(tmp_path: Path) -> None:
    connectors: list[BridgeConnector] = [DummyConnector(), AlternateConnector()]
    service = BridgeSyncService(state_dir=tmp_path, connectors=connectors)
    service.sync(_decision_payload())

    app = FastAPI()
    app.include_router(create_router(api=EchoBridgeAPI(), sync_service=service))
    client = TestClient(app)

    response = client.get("/bridge/sync", params={"connector": "alternate"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["operations"]
    assert payload["operations"][0]["connector"] == "alternate"

    response = client.get("/bridge/sync", params={"connector": "missing"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["operations"] == []
    assert payload["cycle"] is None


def test_unstoppable_connector_merges_registrations_and_defaults() -> None:
    connector = UnstoppableDomainConnector(default_domains=["echo.crypto", "nexus.crypto"])

    decision = _decision_payload(
        cycle="88",
        coherence=0.731,
        manifest_path="manifests/cycle-88.json",
        registrations=[
            {"unstoppable_domains": ["wildfire.crypto", "echo.crypto", ""]},
            {"unstoppable_domains": ["aurora.crypto"]},
        ],
    )

    event = connector.build_event(decision)
    assert event is not None
    assert event.connector == "unstoppable"
    assert event.payload["domains"] == [
        "aurora.crypto",
        "echo.crypto",
        "nexus.crypto",
        "wildfire.crypto",
    ]
    records = event.payload["records"]
    assert records["echo.cycle"] == "88"
    assert records["echo.coherence"] == 0.731
    assert records["echo.manifest"] == "manifests/cycle-88.json"
    assert "4 Unstoppable domain" in event.detail


def test_domain_connector_merges_static_and_inventory_file(tmp_path: Path) -> None:
    inventory = tmp_path / "domains.txt"
    inventory.write_text("example.com\n# comment\nechosphere.net\n", encoding="utf-8")
    connector = DomainInventoryConnector(
        static_domains=["sovereigntrust.io"],
        inventory_path=inventory,
    )

    event = connector.build_event(
        _decision_payload(cycle="21", coherence=0.515, manifest_path="manifest/c21.json")
    )

    assert event is not None
    assert event.connector == "domains"
    assert event.payload["domains"] == [
        "echosphere.net",
        "example.com",
        "sovereigntrust.io",
    ]
    assert event.payload["manifest_path"] == "manifest/c21.json"
    assert "DNS anchor" in event.detail


def test_vercel_connector_tracks_projects_and_cycle() -> None:
    connector = VercelDeployConnector(default_projects=["echo-dashboard"])

    decision = _decision_payload(
        cycle="09",
        coherence=0.96,
        registrations=[
            {"vercel_projects": ["pulse-console", ""]},
            {"vercel_projects": ["echo-dashboard", "nexus-hub"]},
        ],
    )

    event = connector.build_event(decision)
    assert event is not None
    assert event.connector == "vercel"
    assert event.payload["projects"] == [
        "echo-dashboard",
        "nexus-hub",
        "pulse-console",
    ]
    assert event.payload["cycle"] == "09"
    assert event.payload["coherence"] == 0.96
    assert "3 project" in event.detail


def test_bridge_sync_service_from_environment_configures_connectors(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ECHO_BRIDGE_UNSTOPPABLE_DOMAINS", "echo.crypto,nexus.crypto")
    monkeypatch.setenv("ECHO_BRIDGE_VERCEL_PROJECTS", "echo-dashboard,pulse-console")
    inventory = tmp_path / "domains.txt"
    inventory.write_text("example.com", encoding="utf-8")
    monkeypatch.setenv("ECHO_BRIDGE_DOMAINS_FILE", str(inventory))
    monkeypatch.setenv("ECHO_BRIDGE_DOMAINS", "sovereigntrust.io,echovault.ai")

    service = BridgeSyncService.from_environment(
        state_dir=tmp_path,
        github_repository="EchoOrg/sovereign",
    )

    connectors = service._connectors  # noqa: SLF001 - inspection for test coverage
    domains = [c for c in connectors if isinstance(c, DomainInventoryConnector)]
    unstoppable = [c for c in connectors if isinstance(c, UnstoppableDomainConnector)]
    vercel = [c for c in connectors if isinstance(c, VercelDeployConnector)]
    assert domains and sorted(domains[0].static_domains or []) == [
        "echovault.ai",
        "sovereigntrust.io",
    ]
    assert domains[0].inventory_path == inventory
    assert unstoppable and unstoppable[0].default_domains == [
        "echo.crypto",
        "nexus.crypto",
    ]
    assert vercel and vercel[0].default_projects == [
        "echo-dashboard",
        "pulse-console",
    ]
    assert service.log_path == tmp_path / "sync-log.jsonl"
