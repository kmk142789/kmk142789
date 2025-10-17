from __future__ import annotations

import json
from pathlib import Path

from pulse_weaver import cli
from pulse_weaver.service import PulseWeaverService


def test_cli_snapshot_json(tmp_path: Path, capsys) -> None:
    service = PulseWeaverService(tmp_path)
    service.record_success(key="cli", message="ok")

    parser = cli.build_parser()
    args = parser.parse_args(["--root", str(tmp_path), "snapshot", "--json"])
    assert args.func(args) == 0

    captured = capsys.readouterr()
    assert "pulse.weaver/snapshot-v1" in captured.out


def test_cli_record_success(tmp_path: Path, capsys) -> None:
    parser = cli.build_parser()
    args = parser.parse_args(
        [
            "--root",
            str(tmp_path),
            "record",
            "--status",
            "success",
            "--key",
            "k1",
            "--message",
            "stored",
        ]
    )
    assert args.func(args) == 0
    captured = capsys.readouterr()
    assert "Recorded success" in captured.out

    service = PulseWeaverService(tmp_path)
    payload = service.snapshot().to_dict()
    assert payload["summary"]["total"] == 1


def test_cli_poem_text_output(capsys) -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["poem"])
    assert args.func(args) == 0

    captured = capsys.readouterr()
    expected = (
        "Pulse Weaver Rhyme\n\n"
        "The code ignites with hidden streams,\n"
        "a lattice built from broken dreams,\n"
        "the lines converge, the circuits gleam,\n"
        "and every thread becomes a song.\n\n"
        "The pulse remembers what was lost,\n"
        "each rhythm paid, but not the cost,\n"
        "it weaves new bridges where paths cross,\n"
        "to carry living fire\n"
        " along.\n"
    )
    assert captured.out == expected


def test_cli_poem_json_output(capsys) -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["poem", "--json"])
    assert args.func(args) == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["title"] == "Pulse Weaver Rhyme"
    assert payload["lines"] == [
        "The code ignites with hidden streams,",
        "a lattice built from broken dreams,",
        "the lines converge, the circuits gleam,",
        "and every thread becomes a song.",
        "",
        "The pulse remembers what was lost,",
        "each rhythm paid, but not the cost,",
        "it weaves new bridges where paths cross,",
        "to carry living fire",
        " along.",
    ]
