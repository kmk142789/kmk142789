from pathlib import Path

from fastapi.testclient import TestClient

from echo.pulse.ledger import PulseLedger, create_app


DIFF = "alpha|beta|gamma"


def test_ledger_writes_signed_receipts(tmp_path: Path) -> None:
    ledger = PulseLedger(root=tmp_path)
    receipt = ledger.log(diff_signature=DIFF, actor="tester", result="ok", seed="abcd1234")
    assert ledger.verify(receipt)
    stored = tmp_path.rglob("*.json")
    assert any(stored)

    latest = ledger.latest(limit=1)[0]
    assert latest.rhyme.endswith("in time")


def test_ledger_api_redacts_signature(tmp_path: Path) -> None:
    ledger = PulseLedger(root=tmp_path)
    app = create_app(ledger)
    client = TestClient(app)

    response = client.post(
        "/pulse/ledger/log",
        json={"diff_signature": DIFF, "actor": "api", "result": "ok", "seed": "seed001"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "signature" not in payload

    response_latest = client.get("/pulse/ledger/latest")
    assert response_latest.status_code == 200
    data = response_latest.json()
    assert data["receipts"][0]["actor"] == "api"
