from __future__ import annotations

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
    assert "Pulse Weaver Rhyme" in captured.out


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
            "--proof",
            "cli-proof",
        ]
    )
    assert args.func(args) == 0
    captured = capsys.readouterr()
    assert "Recorded success" in captured.out

    service = PulseWeaverService(tmp_path)
    payload = service.snapshot().to_dict()
    assert payload["summary"]["total"] == 1
    assert payload["ledger"][0]["proof"] == "cli-proof"


def test_cli_monolith_console(tmp_path: Path, capsys) -> None:
    service = PulseWeaverService(tmp_path)
    service.record_success(key="monolith", message="Monolith spark", cycle="cycle-777")

    parser = cli.build_parser()
    args = parser.parse_args(["--root", str(tmp_path), "monolith"])
    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert "Pulse Weaver Monolith" in output
    assert "Monolith spark" in output

    args = parser.parse_args(["--root", str(tmp_path), "monolith", "--json"])
    assert args.func(args) == 0
    json_output = capsys.readouterr().out
    assert "\"pulse.weaver/monolith-v1\"" in json_output
