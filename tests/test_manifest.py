from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate
from nacl.signing import SigningKey

from echo.manifest import build_manifest, fingerprint, verify_manifest
from echo.provenance import canonical_json, sign_manifest, verify_signature


def _write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def test_manifest_is_deterministic(tmp_path: Path) -> None:
    manifest_one = build_manifest()
    manifest_two = build_manifest()
    assert manifest_one == manifest_two
    assert manifest_one["fingerprint"] == fingerprint(manifest_one)

    manifest_path = tmp_path / "echo_manifest.json"
    _write_manifest(manifest_path, manifest_one)
    assert verify_manifest(manifest_path) == 0


def test_manifest_drift_detection(tmp_path: Path) -> None:
    manifest = build_manifest()
    manifest_path = tmp_path / "echo_manifest.json"
    _write_manifest(manifest_path, manifest)
    assert verify_manifest(manifest_path) == 0

    manifest["components"][0]["version"] = "0.0-test"
    _write_manifest(manifest_path, manifest)
    assert verify_manifest(manifest_path) == 1


def test_manifest_schema_validation() -> None:
    manifest = build_manifest()
    schema_path = Path("attestations/schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validate(instance=manifest, schema=schema)


def test_manifest_schema_rejects_unknown_fields() -> None:
    manifest = build_manifest()
    schema_path = Path("attestations/schema.json")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest["components"][0]["unexpected"] = "value"
    with pytest.raises(ValidationError):
        validate(instance=manifest, schema=schema)


def test_signature_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    signing_key = SigningKey.generate()
    monkeypatch.setenv("ECHO_SIGN_KEY", signing_key.encode().hex())
    manifest = build_manifest()
    canonical = canonical_json(manifest)
    bundle = sign_manifest(canonical)
    assert bundle.public_key is not None
    assert verify_signature(manifest, bundle.signature, bundle.public_key, algorithm=bundle.algorithm)


def test_hmac_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    key_material = base64.b64encode(b"test-secret-key").decode()
    monkeypatch.setenv("ECHO_SIGN_KEY", key_material)
    manifest = build_manifest()
    canonical = canonical_json(manifest)
    bundle = sign_manifest(canonical)
    assert bundle.algorithm == "hmac-sha256"
    assert bundle.public_key is not None
    assert verify_signature(manifest, bundle.signature, bundle.public_key, algorithm=bundle.algorithm)
