from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.orchestrator.api import create_router
from echo.orchestrator.core import OrchestratorCore


class StubPulseNet:
    def __init__(
        self,
        summary: dict,
        attestations: list[dict],
        wallets: list[dict] | None = None,
        registrations: list[dict] | None = None,
        fail: bool = False,
    ) -> None:
        self._summary = summary
        self._attestations = attestations
        self._wallets = wallets or []
        self._registrations = registrations or []
        self._fail = fail

    def pulse_summary(self) -> dict:
        if self._fail:
            raise RuntimeError("pulsenet offline")
        return self._summary

    def latest_attestations(self, *, limit: int = 10) -> list[dict]:
        if self._fail:
            raise RuntimeError("pulsenet offline")
        return self._attestations[:limit]

    def atlas_wallets(self) -> list[dict]:
        if self._fail:
            raise RuntimeError("pulsenet offline")
        return list(self._wallets)

    def registrations(self) -> list[dict]:
        if self._fail:
            raise RuntimeError("pulsenet offline")
        return list(self._registrations)


class StubEvolver:
    def __init__(self, digest: dict) -> None:
        self._digest = digest

    def cycle_digest(self, *, persist_artifact: bool = True) -> dict:
        return self._digest


class StubResonance:
    def __init__(self, score: float, message: str = "") -> None:
        self._score = score
        self._message = message or "harmonics steady"

    def respond(self, text: str) -> SimpleNamespace:
        return SimpleNamespace(harmonic_score=self._score, message=self._message, pattern=None)


def _make_summary(total_entries: int = 6, total_days: int = 2) -> dict:
    return {
        "total_days": total_days,
        "total_entries": total_entries,
        "busiest_day": {"date": "2024-05-10", "count": total_entries // 2 or 1},
        "quietest_day": {"date": "2024-05-09", "count": max(total_entries - 1, 0)},
        "activity": [
            {"date": "2024-05-09", "count": max(total_entries - 1, 0)},
            {"date": "2024-05-10", "count": total_entries // 2 or 1},
        ],
    }


def _make_digest(progress: float = 0.4) -> dict:
    return {
        "cycle": 3,
        "progress": progress,
        "completed_steps": ["advance_cycle"],
        "remaining_steps": ["mutate_code"],
        "next_step": "Next step: seed mutate_code() to stage the resonance mutation",
        "steps": [
            {"step": "advance_cycle", "description": "advance", "completed": True},
            {"step": "mutate_code", "description": "mutate", "completed": False},
        ],
        "timestamp_ns": 123456789,
    }


def _make_attestations(message: str = "coherent harmonic") -> list[dict]:
    return [
        {
            "pulse": {"message": message, "hash": "abc123"},
            "attestation": {"proof_id": "abc123"},
            "ref": message,
        }
    ]


def test_orchestrator_core_persists_manifest(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(
        _make_summary(),
        _make_attestations(),
        wallets=[{"fingerprint": "abc"}],
        registrations=[{"unstoppable_domains": ["echo.crypto"]}],
    )
    evolver = StubEvolver(_make_digest())
    resonance = StubResonance(score=800.0)

    service = OrchestratorCore(
        state_dir=tmp_path,
        pulsenet=pulsenet,
        evolver=evolver,  # type: ignore[arg-type]
        resonance_engine=resonance,
        atlas_resolver=None,
        manifest_limit=5,
    )

    decision = service.orchestrate()

    manifest_dir = service.manifest_directory
    manifests = list(manifest_dir.glob("orchestration_*.json"))
    assert manifests, "orchestrator should persist a manifest file"
    payload = json.loads(manifests[0].read_text())
    assert payload["graph"]["nodes"][0]["id"] == "orchestrator"

    weights = decision["weights"]
    assert weights["pulsenet"] >= 0.25
    assert weights["atlas"] >= 0.2
    assert "momentum" in decision
    assert decision["momentum"]["triggers"] == []


def test_orchestrator_adaptive_weighting_dampens_noise(tmp_path: Path) -> None:
    clean_pulsenet = StubPulseNet(
        _make_summary(12, 3),
        _make_attestations("harmonic cascade"),
        registrations=[{"vercel_projects": ["pulse-clean"]}],
    )
    noisy_pulsenet = StubPulseNet(_make_summary(12, 3), [])
    evolver = StubEvolver(_make_digest())

    clean_service = OrchestratorCore(
        state_dir=tmp_path / "clean",
        pulsenet=clean_pulsenet,
        evolver=evolver,  # type: ignore[arg-type]
        resonance_engine=StubResonance(900.0),
        atlas_resolver=None,
    )
    noisy_service = OrchestratorCore(
        state_dir=tmp_path / "noisy",
        pulsenet=noisy_pulsenet,
        evolver=evolver,  # type: ignore[arg-type]
        resonance_engine=StubResonance(200.0),
        atlas_resolver=None,
    )

    clean_weight = clean_service.orchestrate()["weights"]["pulsenet"]
    noisy_weight = noisy_service.orchestrate()["weights"]["pulsenet"]

    assert noisy_weight < clean_weight
    assert noisy_service.latest_decision is not None


def test_orchestrator_momentum_triggers_track_progress(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(_make_summary(6, 2), _make_attestations())
    evolver = StubEvolver(_make_digest(0.1))
    resonance = StubResonance(4000.0)

    service = OrchestratorCore(
        state_dir=tmp_path,
        pulsenet=pulsenet,
        evolver=evolver,  # type: ignore[arg-type]
        resonance_engine=resonance,
        atlas_resolver=None,
    )

    first = service.orchestrate()
    assert first["momentum"]["triggers"] == []

    evolver._digest = _make_digest(0.85)
    resonance._score = 9000.0
    surge = service.orchestrate()
    surge_triggers = surge["momentum"]["triggers"]
    assert surge_triggers, "surge should produce momentum triggers"
    assert any(trigger["action"] == "accelerate_cycle" for trigger in surge_triggers)
    assert surge.get("triggers") == surge_triggers

    pulsenet._attestations = []  # type: ignore[attr-defined]
    evolver._digest = _make_digest(0.05)
    resonance._score = 200.0
    slump = service.orchestrate()
    slump_triggers = slump["momentum"]["triggers"]
    assert slump_triggers, "slump should produce momentum stabilisation triggers"
    assert any(trigger["action"] == "stabilise_cycle" for trigger in slump_triggers)
    assert slump.get("triggers") == slump_triggers


def test_orchestrator_flow_endpoint(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(
        _make_summary(),
        _make_attestations(),
        registrations=[{"unstoppable_domains": ["echo.crypto"]}],
    )
    service = OrchestratorCore(
        state_dir=tmp_path,
        pulsenet=pulsenet,
        evolver=StubEvolver(_make_digest()),  # type: ignore[arg-type]
        resonance_engine=StubResonance(600.0),
        atlas_resolver=None,
    )

    app = FastAPI()
    app.include_router(create_router(service))
    client = TestClient(app)

    response = client.get("/orchestrator/flow")
    assert response.status_code == 200
    data = response.json()
    assert data["graph"]["nodes"]
    assert "manifest" in data


class StubBridgeService:
    def __init__(self) -> None:
        self.calls: list[Mapping[str, Any]] = []
        self.log_path = Path("/tmp/log.jsonl")

    def sync(self, decision: Mapping[str, Any]) -> list[dict[str, Any]]:
        self.calls.append(decision)
        cycle = (
            str(decision.get("inputs", {}).get("cycle_digest", {}).get("cycle", ""))
            if isinstance(decision, Mapping)
            else ""
        )
        return [
            {
                "id": "stub",
                "timestamp": "2024-01-01T00:00:00+00:00",
                "connector": "stub",
                "action": "noop",
                "status": "ok",
                "detail": "stub event",
                "cycle": cycle,
                "coherence": 0.5,
                "manifest_path": "manifest.json",
                "payload": {},
            }
        ]


def test_orchestrator_records_bridge_sync(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(_make_summary(), _make_attestations())
    bridge = StubBridgeService()
    service = OrchestratorCore(
        state_dir=tmp_path,
        pulsenet=pulsenet,
        evolver=StubEvolver(_make_digest()),  # type: ignore[arg-type]
        resonance_engine=StubResonance(600.0),
        atlas_resolver=None,
        bridge_service=bridge,
    )

    decision = service.orchestrate()

    assert bridge.calls, "Bridge service should be invoked"
    assert "bridge_sync" in decision
    assert decision["bridge_sync"]["operations"][0]["connector"] == "stub"


def test_orchestrator_offline_cache_persists_state(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(_make_summary(), _make_attestations())
    evolver = StubEvolver(_make_digest())
    resonance = StubResonance(500.0)

    service = OrchestratorCore(
        state_dir=tmp_path,
        pulsenet=pulsenet,
        evolver=evolver,  # type: ignore[arg-type]
        resonance_engine=resonance,
        atlas_resolver=None,
    )
    service._store.set_policy("policy-001-min-safety", version=3, signed_by="AI_GOV_LEAD")

    online = service.orchestrate()
    assert online["offline_mode"] is False
    assert online["active_policy_version"] == "policy-001-min-safety@v3"

    pulsenet._fail = True  # type: ignore[attr-defined]
    offline = service.orchestrate()

    assert offline["offline_mode"] is True
    assert offline["inputs"]["pulse_summary"] == online["inputs"]["pulse_summary"]
    details = offline.get("offline_details", {})
    assert details.get("cached_at")
    assert details.get("cache_path")
    assert isinstance(details.get("cache_age_seconds"), (int, float))
    assert details.get("offline_policy_version") == "policy-001-min-safety@v3"
    assert details.get("offline_reason")
    assert details.get("offline_source")
    assert details.get("policy_snapshot")


def test_orchestrator_logs_decisions_and_metrics(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(_make_summary(), _make_attestations())
    evolver = StubEvolver(_make_digest())
    resonance = StubResonance(700.0)

    service = OrchestratorCore(
        state_dir=tmp_path,
        pulsenet=pulsenet,
        evolver=evolver,  # type: ignore[arg-type]
        resonance_engine=resonance,
        atlas_resolver=None,
    )
    service._store.set_policy("policy-002-governance", version=1, signed_by="AI_GOV_LEAD")

    decision = service.orchestrate()
    assert decision["active_policy_version"] == "policy-002-governance@v1"

    conn = sqlite3.connect(tmp_path / "orchestrator_state.db")
    cursor = conn.execute(
        "SELECT decision, offline_mode, offline_policy_version FROM decisions ORDER BY id DESC LIMIT 1"
    )
    row = cursor.fetchone()
    assert row is not None
    persisted_decision, offline_mode, offline_policy_version = row
    payload = json.loads(persisted_decision)
    assert payload["active_policy_version"] == "policy-002-governance@v1"
    assert offline_mode == 0
    assert offline_policy_version == "policy-002-governance@v1"

    metric_cursor = conn.execute("SELECT name, value, metadata FROM metrics ORDER BY id DESC LIMIT 1")
    metric_row = metric_cursor.fetchone()
    assert metric_row is not None
    name, value, metadata = metric_row
    assert name == "coherence_score"
    assert isinstance(value, float)
    assert "offline" in json.loads(metadata)
    conn.close()
