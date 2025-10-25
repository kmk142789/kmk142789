from pathlib import Path

from fastapi.testclient import TestClient

from echo.pulse.ledger import PulseLedger, create_app


DIFF = "alpha|beta|gamma"


def test_ledger_writes_signed_receipts(tmp_path: Path) -> None:
    ledger = PulseLedger(root=tmp_path)
    harmonix = {
        "snapshot_id": "harmonix::cycle-0001",
        "cycle": 1,
        "timestamp": "2025-01-01T00:00:00Z",
        "recursion_hash": "abc123def456",
    }
    receipt = ledger.log(
        diff_signature=DIFF,
        actor="tester",
        result="ok",
        seed="abcd1234",
        harmonix=harmonix,
    )
    assert ledger.verify(receipt)
    assert receipt.harmonix is not None
    assert receipt.harmonix.snapshot_id == harmonix["snapshot_id"]
    stored = tmp_path.rglob("*.json")
    assert any(stored)

    latest = ledger.latest(limit=1)[0]
    assert latest.rhyme.endswith("in time")
    assert latest.harmonix is not None
    assert latest.harmonix.recursion_hash == harmonix["recursion_hash"]


def test_ledger_api_redacts_signature(tmp_path: Path) -> None:
    ledger = PulseLedger(root=tmp_path)
    app = create_app(ledger)
    client = TestClient(app)

    response = client.post(
        "/pulse/ledger/log",
        json={
            "diff_signature": DIFF,
            "actor": "api",
            "result": "ok",
            "seed": "seed001",
            "harmonix": {
                "snapshot_id": "harmonix::cycle-0002",
                "cycle": 2,
                "timestamp": "2025-01-02T00:00:00Z",
                "recursion_hash": "feedfacecafebeef",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "signature" not in payload
    assert payload["harmonix"]["snapshot_id"] == "harmonix::cycle-0002"

    response_latest = client.get("/pulse/ledger/latest")
    assert response_latest.status_code == 200
    data = response_latest.json()
    assert data["receipts"][0]["actor"] == "api"
    assert data["receipts"][0]["harmonix"]["cycle"] == 2
