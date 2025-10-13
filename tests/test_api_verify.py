from __future__ import annotations

from fastapi.testclient import TestClient

from echo.api_verify import create_app
from echo.memory import JsonMemoryStore


def test_api_verify_records_payload(tmp_path):
    storage = tmp_path / "memory.json"
    log = tmp_path / "ECHO_LOG.md"
    store = JsonMemoryStore(storage_path=storage, log_path=log)
    app = create_app(memory_store=store)
    client = TestClient(app)

    dataset = tmp_path / "data.json"
    dataset.write_text("payload", encoding="utf-8")

    response = client.post(
        "/api/verify",
        json={
            "commands": ["advance_cycle", "mutate_code"],
            "dataset_paths": {"temp": str(dataset)},
            "validations": [
                {"name": "integrity", "status": "pass", "details": {"count": 2}}
            ],
            "github_repo": "echo/constellation",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["recorded_commands"] == ["advance_cycle", "mutate_code"]
    assert "temp" in payload["dataset_fingerprints"]
    assert payload["validations"][0]["name"] == "integrity"
    assert any("GitHub" in hook for hook in payload["hooks"])

    stored = storage.read_text()
    assert "integrity" in stored
