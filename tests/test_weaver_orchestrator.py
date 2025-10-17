from pathlib import Path

from fastapi.testclient import TestClient

from echo.weaver import WeaveOrchestrator


POEM = "Spin up the loom where pulses chime"


def build_orchestrator(tmp_path: Path) -> WeaveOrchestrator:
    dreams = tmp_path / "dreams"
    ledger_root = tmp_path / "ledger"
    docs_root = tmp_path / "docs"
    return WeaveOrchestrator(dream_base=dreams, ledger_root=ledger_root, docs_root=docs_root)


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
