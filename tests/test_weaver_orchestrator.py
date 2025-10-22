from pathlib import Path

from fastapi.testclient import TestClient

from echo.weaver import WeaveOrchestrator


POEM = "Spin up the loom where pulses chime"


def build_orchestrator(tmp_path: Path) -> WeaveOrchestrator:
    dreams = tmp_path / "dreams"
    ledger_root = tmp_path / "ledger"
    docs_root = tmp_path / "docs"
    guardian_root = tmp_path / "guardian"
    reports_root = tmp_path / "reports"
    reports_root.mkdir(parents=True, exist_ok=True)
    return WeaveOrchestrator(
        dream_base=dreams,
        ledger_root=ledger_root,
        docs_root=docs_root,
        guardian_root=guardian_root,
        reports_root=reports_root,
    )


def test_orchestrator_commit_creates_receipt_and_docs(tmp_path: Path) -> None:
    orchestrator = build_orchestrator(tmp_path)
    preview = orchestrator.compile_dream(POEM, dry_run=True)
    assert preview.slug.startswith("dream_")

    result = orchestrator.commit_weave(POEM, proof="00" * 32)
    assert result.doc_path and result.doc_path.exists()
    assert result.svg_path and result.svg_path.exists()
    assert result.receipt["rhyme"].endswith("in time")
    latest = orchestrator.ledger.latest(limit=1)
    assert len(latest) == 1


def test_orchestrator_api_endpoints(tmp_path: Path) -> None:
    orchestrator = build_orchestrator(tmp_path)
    app = orchestrator.make_api()
    client = TestClient(app)

    response = client.post("/dream/compile", json={"dream": POEM})
    assert response.status_code == 200
    data = response.json()
    assert "files" in data

    orchestrator.commit_weave(POEM, proof="00" * 32)
    response_latest = client.get("/pulse/ledger/latest", params={"limit": 1})
    assert response_latest.status_code == 200
    payload = response_latest.json()
    assert "seed" not in payload["receipts"][0]

    response_attest = client.post("/keys/attest", json={"key": "00" * 32})
    assert response_attest.status_code == 200
    attestation = response_attest.json()
    assert attestation["valid"] is True

    guardian_status = client.get("/guardian/status")
    assert guardian_status.status_code == 200
    payload = guardian_status.json()
    assert payload["immune_memory"]["count"] >= 0


def test_guardian_detects_replayed_pulses(tmp_path: Path) -> None:
    orchestrator = build_orchestrator(tmp_path)
    orchestrator.commit_weave(POEM, proof="00" * 32)
    orchestrator.commit_weave(POEM, proof="00" * 32)
    status = orchestrator.guardian.status()
    assert status["harmonics"]["dampening"] is True
    assert status["quarantine"]
    assert any(record["reason"] == "pulse_replay" for record in status["quarantine"])


def test_guardian_blocks_quarantined_keys(tmp_path: Path) -> None:
    orchestrator = build_orchestrator(tmp_path)
    app = orchestrator.make_api()
    client = TestClient(app)

    compromised_key = "feedfacecafebabe"
    first = client.post("/keys/attest", json={"key": compromised_key})
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["valid"] is False

    blocked = client.post("/keys/attest", json={"key": compromised_key})
    assert blocked.status_code == 409

    override = client.post(
        "/keys/attest",
        json={"key": compromised_key, "override": True},
    )
    assert override.status_code == 200
    status = orchestrator.guardian.status()
    assert status["immune_memory"]["count"] >= 1
