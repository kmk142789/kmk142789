import json
import pathlib

from echo.vNext.agents import governance_pulse


def test_record_creates_chain(tmp_path: pathlib.Path) -> None:
    log_path = tmp_path / "pulse.json"

    first_payload = {"task": "bootstrap"}
    first = governance_pulse.record("task", first_payload, path=log_path)
    assert first.previous_digest is None

    second_payload = {"task": "deploy", "status": "done"}
    second = governance_pulse.record("task", second_payload, path=log_path)
    assert second.previous_digest == first.digest

    entries = governance_pulse.load(path=log_path)
    assert [e.payload for e in entries] == [first_payload, second_payload]
    assert governance_pulse.verify(entries=entries)


def test_verify_fails_when_entry_tampered(tmp_path: pathlib.Path) -> None:
    log_path = tmp_path / "pulse.json"

    governance_pulse.record("task", {"task": "alpha"}, path=log_path)
    governance_pulse.record("task", {"task": "beta"}, path=log_path)

    raw = json.loads(log_path.read_text())
    raw[0]["payload"]["task"] = "tampered"
    log_path.write_text(json.dumps(raw))

    entries = governance_pulse.load(path=log_path)
    assert not governance_pulse.verify(entries=entries)


def test_using_log_context_manager(tmp_path: pathlib.Path) -> None:
    custom_log = tmp_path / "custom.json"

    with governance_pulse.using_log(custom_log):
        governance_pulse.record("event", {"key": "value"})

    assert governance_pulse.pulse_file == pathlib.Path("echo/vNext/agents/pulse_log.json")
    entries = governance_pulse.load(path=custom_log)
    assert len(entries) == 1
