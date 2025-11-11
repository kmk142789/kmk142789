import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from atlas.cli.main import app


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_cli_storage_flow(tmp_path: Path, runner: CliRunner, monkeypatch):
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_CONFIG", str(tmp_path / "atlas.yaml"))
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "config" / "atlas.yaml").write_text("{}", encoding="utf-8")

    put = runner.invoke(app, ["storage", "put", "--driver", "fs", "--path", "demo", "--data", "hello"])
    assert put.exit_code == 0
    receipt = json.loads(put.output)
    receipt_path = tmp_path / "data" / "last_receipt.json"
    assert receipt_path.exists()

    get = runner.invoke(app, ["storage", "get", "--receipt", str(receipt_path)])
    assert "hello" in get.output


def test_cli_diag(tmp_path: Path, runner: CliRunner, monkeypatch):
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_CONFIG", str(tmp_path / "atlas.yaml"))
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "config" / "atlas.yaml").write_text("{}", encoding="utf-8")

    result = runner.invoke(app, ["diag", "config"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["data_dir"].endswith("data")
