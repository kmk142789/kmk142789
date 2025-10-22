from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from echo.orchestrator.api import create_router
from echo.orchestrator.core import OrchestratorCore


class StubPulseNet:
    def __init__(self, summary: dict, attestations: list[dict], wallets: list[dict] | None = None) -> None:
        self._summary = summary
        self._attestations = attestations
        self._wallets = wallets or []

    def pulse_summary(self) -> dict:
        return self._summary

    def latest_attestations(self, *, limit: int = 10) -> list[dict]:
        return self._attestations[:limit]

    def atlas_wallets(self) -> list[dict]:
        return list(self._wallets)


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
    pulsenet = StubPulseNet(_make_summary(), _make_attestations(), wallets=[{"fingerprint": "abc"}])
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


def test_orchestrator_adaptive_weighting_dampens_noise(tmp_path: Path) -> None:
    clean_pulsenet = StubPulseNet(_make_summary(12, 3), _make_attestations("harmonic cascade"))
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


def test_orchestrator_flow_endpoint(tmp_path: Path) -> None:
    pulsenet = StubPulseNet(_make_summary(), _make_attestations())
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
