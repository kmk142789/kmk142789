import json
import subprocess
import sys

import pytest

from echo.echo_world_bootstrap import EchoWorldBootstrap, run_echoworld


def test_import_and_activation():
    bootstrap = EchoWorldBootstrap()
    status = bootstrap.activate(dry_run=True)

    assert set(status) >= {"innovation_suite", "outerlink_runtime", "mode"}
    assert status["mode"] == "dry_run"


def test_run_echoworld_returns_status():
    status = run_echoworld(dry_run=True)

    assert status["innovation_suite"]
    assert status["outerlink_runtime"]
    assert status["mode"] == "dry_run"


@pytest.mark.parametrize("flag", ["--json", "--dry-run", "--json --dry-run"])
def test_cli_invocation_smoke(tmp_path, flag):
    args = [sys.executable, "-m", "echo.echo_world_bootstrap"] + flag.split()
    result = subprocess.run(args, capture_output=True, text=True)

    assert result.returncode == 0
    payload = result.stdout.strip().splitlines()[-1]
    if "--json" in flag:
        parsed = json.loads(payload)
        assert parsed.get("mode")
    else:
        assert "mode" in payload
