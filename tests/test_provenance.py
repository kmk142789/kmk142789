"""Tests for provenance emission and verification."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from echo.provenance import ProvenanceEmitter, verify_provenance


def _fixed_clock(times: list[datetime]):
    iterator = iter(times)

    def _next() -> datetime:
        return next(iterator)

    return _next


def test_emit_is_deterministic(tmp_path):
    sample_input = tmp_path / "input.txt"
    sample_input.write_text("hello", encoding="utf-8")

    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    emitter = ProvenanceEmitter(
        output_directory=tmp_path,
        clock=_fixed_clock([fixed_time, fixed_time, fixed_time, fixed_time]),
    )

    first = emitter.emit(
        context="manifest",
        inputs=[sample_input],
        outputs=[sample_input],
        cycle_id="deterministic",
        runtime_seed="seed",
    )
    second = emitter.emit(
        context="manifest",
        inputs=[sample_input],
        outputs=[sample_input],
        cycle_id="deterministic",
        runtime_seed="seed",
    )
    assert first == second
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["seal"]["sha256"]


def test_verify_detects_tampering(tmp_path):
    sample = tmp_path / "artifact.txt"
    sample.write_text("artifact", encoding="utf-8")
    emitter = ProvenanceEmitter(output_directory=tmp_path)
    record_path = emitter.emit(
        context="engine:test",
        inputs=[sample],
        outputs=[sample],
        cycle_id="test",
        runtime_seed="seed",
    )
    assert verify_provenance(record_path)
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    payload["commit"] = "tampered"
    record_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    assert not verify_provenance(record_path)
