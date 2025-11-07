import json
import pathlib
from typing import List

import pytest

from echo.vNext.agents import continuity_anchor


@pytest.fixture()
def sample_pulses() -> List[continuity_anchor.PulseRecord]:
    return [
        continuity_anchor.PulseRecord(
            time="2024-01-01T00:00:00Z",
            event="pulse-1",
            digest="alpha",
            payload={"time": "2024-01-01T00:00:00Z", "event": "pulse-1", "digest": "alpha"},
        ),
        continuity_anchor.PulseRecord(
            time="2024-01-01T01:00:00Z",
            event="pulse-2",
            digest="beta",
            payload={"time": "2024-01-01T01:00:00Z", "event": "pulse-2", "digest": "beta"},
        ),
    ]


def test_load_pulses_round_trip(tmp_path: pathlib.Path) -> None:
    payload = [
        {"time": "2023-01-01T00:00:00Z", "event": "start", "digest": "abc"},
        {"time": "2023-01-01T01:00:00Z", "event": "continue", "digest": "def"},
    ]
    pulse_file = tmp_path / "pulse_log.json"
    pulse_file.write_text(json.dumps(payload))

    pulses = continuity_anchor.load_pulses(pulse_file)
    assert [p.event for p in pulses] == ["start", "continue"]


def test_load_pulses_requires_fields(tmp_path: pathlib.Path) -> None:
    pulse_file = tmp_path / "pulse_log.json"
    pulse_file.write_text(json.dumps([{"time": "now"}]))
    with pytest.raises(ValueError):
        continuity_anchor.load_pulses(pulse_file)


def test_build_anchor_chain_is_deterministic(sample_pulses: List[continuity_anchor.PulseRecord]) -> None:
    first = continuity_anchor.build_anchor_chain(sample_pulses)
    second = continuity_anchor.build_anchor_chain(sample_pulses)
    assert first == second
    assert first[-1]["previous_anchor"] == first[-2]["anchor"]


def test_write_anchor_log(tmp_path: pathlib.Path, sample_pulses: List[continuity_anchor.PulseRecord]) -> None:
    anchors = continuity_anchor.build_anchor_chain(sample_pulses)
    output = tmp_path / "anchor_log.json"
    summary = continuity_anchor.write_anchor_log(anchors, output_path=output)
    assert summary["chain_length"] == 2
    written = json.loads(output.read_text())
    assert written["last_anchor"] == summary["last_anchor"]


def test_compute_anchor_missing_pulse_file(tmp_path: pathlib.Path) -> None:
    summary = continuity_anchor.compute_anchor(
        pulse_path=tmp_path / "missing.json", anchor_path=tmp_path / "anchor.json"
    )
    assert summary["status"] == "no_pulse_log"


def test_compute_anchor_success(tmp_path: pathlib.Path) -> None:
    pulse_file = tmp_path / "pulse.json"
    pulse_file.write_text(
        json.dumps(
            [
                {"time": "2023-01-01T00:00:00Z", "event": "start", "digest": "abc"},
                {"time": "2023-01-01T01:00:00Z", "event": "continue", "digest": "def"},
            ]
        )
    )
    anchor_file = tmp_path / "anchor.json"
    summary = continuity_anchor.compute_anchor(pulse_path=pulse_file, anchor_path=anchor_file)
    assert summary["chain_length"] == 2
    assert anchor_file.exists()
