from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from hashlib import sha256

from echo.continuum_protocol import ContinuumProtocol, ContinuumTranscript


def _fixed_env() -> dict[str, str]:
    return {"system": "TestOS", "release": "1.0", "hostname": "nexus"}


def _clock_factory(start: datetime):
    counter = -1

    def clock() -> datetime:
        nonlocal counter
        counter += 1
        return start + timedelta(seconds=counter)

    return clock


def _id_factory():
    counter = 0

    def factory() -> UUID:
        nonlocal counter
        counter += 1
        return UUID(int=counter)

    return factory


def _protocol() -> ContinuumProtocol:
    return ContinuumProtocol(
        env_factory=_fixed_env,
        clock=_clock_factory(datetime(2024, 1, 1, tzinfo=timezone.utc)),
        id_factory=_id_factory(),
    )


def test_new_pulse_chain_hash_is_deterministic() -> None:
    protocol = _protocol()
    pulse = protocol.new_pulse("Test pulse")

    expected_payload = {
        "anchor": pulse.anchor,
        "author": pulse.author,
        "child": pulse.child,
        "env": pulse.env,
        "glyphs": pulse.glyphs,
        "id": pulse.id,
        "message": pulse.message,
        "parent_hash": pulse.parent_hash,
        "timestamp": pulse.timestamp,
    }
    raw = json.dumps(expected_payload, sort_keys=True, separators=(",", ":"))

    assert pulse.chain_hash == sha256(raw.encode("utf-8")).hexdigest()


def test_genesis_links_parent_hashes() -> None:
    protocol = _protocol()
    pulses = protocol.genesis(steps=3)

    assert len(pulses) == 3
    assert pulses[0].parent_hash is None
    for previous, current in zip(pulses, pulses[1:]):
        assert current.parent_hash == previous.chain_hash
        assert "Continuum step" in current.message


def test_append_and_transcript(tmp_path) -> None:
    protocol = _protocol()
    pulse = protocol.new_pulse("Archive me")
    path = tmp_path / "continuum.jsonl"

    protocol.append_pulse(path, pulse)
    protocol.append_pulse(path, protocol.new_pulse("Second"))

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payload = json.loads(lines[0])
    assert payload["id"] == pulse.id

    transcript = protocol.simulate_propagation(pulse)
    assert isinstance(transcript, ContinuumTranscript)
    assert "Simulation mode active" in transcript.notice
    assert len(transcript.events) == 4
    assert all(pulse.chain_hash[:12] in event for event in transcript.events)
