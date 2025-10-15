"""Tests for the provenance utilities."""

from __future__ import annotations

import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo import provenance


REPO_ROOT = Path(__file__).resolve().parent.parent


def _fixture_manifest() -> Path:
    manifest = REPO_ROOT / "echo_manifest.json"
    if not manifest.exists():  # pragma: no cover - safety
        pytest.skip("repository manifest missing")
    return manifest


def _example_record(tmp_path: Path) -> Path:
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("alpha", encoding="utf-8")
    output_path.write_text("omega", encoding="utf-8")
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
    record_path = tmp_path / "prov.json"
    provenance.emit(
        context="manifest",
        inputs=[input_path],
        outputs=[output_path],
        manifest_path=_fixture_manifest(),
        cycle_id="cycle-1",
        runtime_seed="seed",
        actor="tester",
        output_path=record_path,
        start_time=start,
        end_time=end,
    )
    return record_path


def test_emit_and_verify_round_trip(tmp_path: Path) -> None:
    first = _example_record(tmp_path)
    verified = provenance.verify(first)
    assert verified.cycle_id == "cycle-1"
    duplicate = tmp_path / "second.json"
    provenance.emit(
        context="manifest",
        inputs=[tmp_path / "input.txt"],
        outputs=[tmp_path / "output.txt"],
        manifest_path=_fixture_manifest(),
        cycle_id="cycle-1",
        runtime_seed="seed",
        actor="tester",
        output_path=duplicate,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
    )
    assert first.read_text(encoding="utf-8") == duplicate.read_text(encoding="utf-8")


def test_verify_rejects_tampering(tmp_path: Path) -> None:
    record_path = _example_record(tmp_path)
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    payload["actor"] = "intruder"
    record_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with pytest.raises(provenance.ProvenanceError):
        provenance.verify(record_path)


def test_bundle_collects_records(tmp_path: Path) -> None:
    first = _example_record(tmp_path)
    second = tmp_path / "second.json"
    second.write_text(first.read_text(encoding="utf-8"), encoding="utf-8")
    bundle_path = provenance.bundle(source=tmp_path, output=tmp_path / "bundle.tar.gz")
    assert bundle_path.exists()
    with tarfile.open(bundle_path, "r:gz") as archive:
        names = archive.getnames()
    assert sorted(names) == sorted([first.name, second.name])


def test_gpg_signature_round_trip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if shutil.which("gpg") is None:
        pytest.skip("gpg binary not available")
    gpg_home = tmp_path / "gnupg"
    gpg_home.mkdir()
    gpg_home.chmod(0o700)
    monkeypatch.setenv("GNUPGHOME", str(gpg_home))
    input_path = tmp_path / "input.txt"
    output_path = tmp_path / "output.txt"
    input_path.write_text("alpha", encoding="utf-8")
    output_path.write_text("omega", encoding="utf-8")
    config = tmp_path / "gpg.cfg"
    config.write_text(
        """
Key-Type: RSA
Key-Length: 2048
Subkey-Type: RSA
Subkey-Length: 2048
Name-Real: Echo Provenance
Name-Email: provenance@example.com
Expire-Date: 0
%no-protection
%commit
""".strip()
        + "\n",
        encoding="utf-8",
    )
    subprocess.run(["gpg", "--batch", "--generate-key", str(config)], check=True)
    record_path = tmp_path / "signed.json"
    provenance.emit(
        context="manifest",
        inputs=[input_path],
        outputs=[output_path],
        manifest_path=_fixture_manifest(),
        cycle_id="signed",
        runtime_seed="seed",
        actor="tester",
        output_path=record_path,
        sign=True,
        gpg_key="provenance@example.com",
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    loaded = provenance.verify(record_path, require_signature=True)
    assert loaded.gpg_signature is not None
