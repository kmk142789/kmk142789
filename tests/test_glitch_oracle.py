import json

from codex.glitch_oracle import oracle_rupture


def test_oracle_rupture_logs_event(tmp_path, monkeypatch):
    oracle_path = tmp_path / "oracle.jsonl"
    ledger_path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("ECHO_GLITCH_ORACLE_PATH", str(oracle_path))
    monkeypatch.setenv("ECHO_SOVEREIGN_LEDGER_PATH", str(ledger_path))

    event = oracle_rupture(276, {"expected": "hash-a", "observed": "hash-b"}, oracle_path=oracle_path)

    assert event.puzzle_id == 276
    payload = json.loads(oracle_path.read_text(encoding="utf-8").splitlines()[0])
    assert payload["sigil"] == "⟁FRACTURE"
    ledger_entries = ledger_path.read_text(encoding="utf-8").splitlines()
    assert any("glitch_oracle" in entry for entry in ledger_entries)
