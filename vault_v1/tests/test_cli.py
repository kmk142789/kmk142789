from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from jwcrypto import jwk, jws

from vault.cli.main import cli


def test_keygen_ingest_fetch_and_proof(tmp_path, monkeypatch):
    runner = CliRunner()
    key_path = tmp_path / "keys" / "signing.json"

    result = runner.invoke(cli, ["keygen", "--out", str(key_path)])
    assert result.exit_code == 0
    assert key_path.exists()

    key_data = json.loads(key_path.read_text())
    assert key_data["kty"] == "EC"

    monkeypatch.setenv("VAULT_SIGNING_KEY", str(key_path))

    data_file = tmp_path / "payload.txt"
    data_file.write_text("vault cli test data")

    ingest_result = runner.invoke(
        cli,
        ["ingest", str(data_file), "--chunk-size", "512", "--sign"],
        env={"VAULT_SIGNING_KEY": str(key_path)},
    )
    assert ingest_result.exit_code == 0
    ingest_output = json.loads(ingest_result.output)
    cid = ingest_output["cid"]

    key = jwk.JWK.from_json(key_path.read_text())
    token = jws.JWS()
    token.deserialize(ingest_output["receipt"]["signature"], key=key)

    out_path = tmp_path / "restored.txt"
    fetch_result = runner.invoke(
        cli,
        ["fetch", cid, "--out", str(out_path), "--sign"],
        env={"VAULT_SIGNING_KEY": str(key_path)},
    )
    assert fetch_result.exit_code == 0
    fetch_payload = json.loads(fetch_result.output)
    assert Path(fetch_payload["path"]).read_text() == data_file.read_text()

    proof_result = runner.invoke(cli, ["proof", cid, "--sign"], env={"VAULT_SIGNING_KEY": str(key_path)})
    assert proof_result.exit_code == 0
    proof_payload = json.loads(proof_result.output)
    assert proof_payload["verified"] is True
    assert "receipt" in proof_payload
