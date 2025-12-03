import json
import os

from verifier.echo_attest import build_attestation, persist_attestation


def test_build_attestation_with_override_timestamp():
    attestation = build_attestation("hello", signer_id="tester", ts=123)

    assert attestation["sha256"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert attestation["ts"] == 123
    assert attestation["signer_id"] == "tester"
    assert attestation["context"] == "hello"


def test_build_attestation_defaults_env(monkeypatch):
    monkeypatch.setenv("ECHO_SIGNER_ID", "env-attest")

    attestation = build_attestation("context")

    assert attestation["signer_id"] == "env-attest"


def test_persist_attestation_creates_file(tmp_path):
    attestation = build_attestation("persist-me", signer_id="writer", ts=999)

    path = persist_attestation(attestation, directory=tmp_path)

    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded == attestation
    assert os.path.basename(path) == "999_ccacc434.json"
