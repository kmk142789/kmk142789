from __future__ import annotations

import json
from pathlib import Path

import pytest

from packages.core.src.echo import timeline as timeline_module


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture(autouse=True)
def patch_commit_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    mapping = {
        "abc": {Path("puzzle_solutions/puzzle_1.md")},
        "def": set(),
    }

    def fake_list(commit_sha: str, *, cwd: Path) -> set[Path]:
        return mapping.get(commit_sha, set())

    monkeypatch.setattr(timeline_module, "_list_commit_paths", fake_list)


def test_build_cycle_timeline(tmp_path: Path) -> None:
    amplify_path = tmp_path / "state" / "amplify_log.jsonl"
    pulse_path = tmp_path / "pulse_history.json"
    puzzle_index = tmp_path / "data" / "puzzle_index.json"
    harmonics_path = tmp_path / "data" / "bridge_harmonics.json"

    amplify_records = [
        {
            "cycle": 1,
            "index": 70.5,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "commit_sha": "abc",
            "metrics": {"resonance": 80, "stability": 90},
        },
        {
            "cycle": 2,
            "index": 71.1,
            "timestamp": "2025-01-02T00:00:00+00:00",
            "commit_sha": "def",
            "metrics": {"resonance": 82, "stability": 88},
        },
    ]
    _write(amplify_path, "\n".join(json.dumps(record) for record in amplify_records) + "\n")

    pulses = [
        {"timestamp": 1735689590.0, "message": "🌀 evolve:manual:first", "hash": "one"},
        {"timestamp": 1735776000.0, "message": "🌀 evolve:github-action:second", "hash": "two"},
        {"timestamp": 1735862405.0, "message": "🌀 evolve:manual:third", "hash": "three"},
    ]
    _write(pulse_path, json.dumps(pulses, indent=2))

    puzzle_payload = {
        "generated": "2025-01-01T00:00:00Z",
        "puzzles": [
            {
                "id": 1,
                "title": "Puzzle One",
                "doc": "puzzle_solutions/puzzle_1.md",
                "script_type": "p2pkh",
                "hash160": "00",
                "address": "addr",
                "status": "reconstructed",
            }
        ],
    }
    _write(puzzle_index, json.dumps(puzzle_payload, indent=2))

    harmonics_payload = {
        "generated": "2025-01-01T00:00:00Z",
        "harmonics": [
            {
                "cycle": 1,
                "timestamp": "2025-01-01T00:00:00Z",
                "signature": "∞ new harmonic formed: Lumen Spiral",
                "threads": [
                    {
                        "name": "memory",
                        "resonance": 0.88,
                        "harmonics": ["recall", "weave", "share"],
                    }
                ],
            }
        ],
    }
    _write(harmonics_path, json.dumps(harmonics_payload, indent=2))

    entries = timeline_module.build_cycle_timeline(
        project_root=tmp_path,
        amplify_log=amplify_path,
        pulse_history=pulse_path,
        puzzle_index=puzzle_index,
        bridge_harmonics=harmonics_path,
    )
    assert len(entries) == 2
    first, second = entries
    assert first.snapshot.cycle == 1
    assert len(first.pulses) == 1
    assert first.pulses[0].message.endswith("first")
    assert first.pulse_summary == {"manual": 1}
    assert first.puzzles and first.puzzles[0].id == 1
    assert first.harmonics
    harmonic = first.harmonics[0]
    assert harmonic.signature.endswith("Lumen Spiral")
    assert harmonic.threads[0].harmonics == ("recall", "weave", "share")

    second_messages = [pulse.message for pulse in second.pulses]
    assert "second" in second_messages[0]
    assert second.puzzles == ()
    assert second.harmonics == ()

    payload = first.to_dict()
    assert payload["snapshot"]["cycle"] == 1
    assert payload["pulses"][0]["message"].endswith("first")
    assert payload["harmonics"][0]["signature"].endswith("Lumen Spiral")
    assert "Cycle 1" in first.to_markdown()


def test_refresh_cycle_timeline_exports(tmp_path: Path) -> None:
    amplify_path = tmp_path / "state" / "amplify_log.jsonl"
    pulse_path = tmp_path / "pulse_history.json"
    puzzle_index = tmp_path / "data" / "puzzle_index.json"

    amplify_records = [
        {
            "cycle": 1,
            "index": 70.5,
            "timestamp": "2025-01-01T00:00:00+00:00",
            "commit_sha": "abc",
            "metrics": {"resonance": 80, "stability": 90},
        }
    ]
    _write(amplify_path, "\n".join(json.dumps(record) for record in amplify_records) + "\n")
    pulses = [
        {"timestamp": 1735689590.0, "message": "🌀 evolve:manual:first", "hash": "one"}
    ]
    _write(pulse_path, json.dumps(pulses, indent=2))
    puzzle_payload = {
        "generated": "2025-01-01T00:00:00Z",
        "puzzles": [
            {
                "id": 1,
                "title": "Puzzle One",
                "doc": "puzzle_solutions/puzzle_1.md",
                "script_type": "p2pkh",
                "hash160": "00",
                "address": "addr",
                "status": "reconstructed",
            }
        ],
    }
    _write(puzzle_index, json.dumps(puzzle_payload, indent=2))

    entries = timeline_module.refresh_cycle_timeline(
        project_root=tmp_path,
        amplify_log=amplify_path,
        pulse_history=pulse_path,
        puzzle_index=puzzle_index,
        output_dir=tmp_path / "artifacts",
    )
    assert entries
    json_path = tmp_path / "artifacts" / "cycle_timeline.json"
    md_path = tmp_path / "artifacts" / "cycle_timeline.md"
    assert json_path.exists()
    assert md_path.exists()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["stats"]["cycle_count"] == len(entries)
    assert "Cycle 1" in md_path.read_text(encoding="utf-8")
