from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from echo import manifest as manifest_module


ENGINE_TEXT = "print('engine')\n"
CLI_TEXT = "#!/usr/bin/env python3\nprint('cli')\n"
DOC_TEXT = "# Guide\n"
DATA_TEXT = '{"value": 1}\n'
STATE_TEXT = '{"pulse": "alive"}\n'


def _write(path: Path, content: str, *, timestamp: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf8")
    os.utime(path, (timestamp, timestamp))


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path
    codeowners = repo_root / ".github" / "CODEOWNERS"
    codeowners.parent.mkdir(parents=True, exist_ok=True)
    codeowners.write_text(
        """
* @all
/docs/** @docs
/docs/data/* @data-team
/echo/* @engineers
/scripts/* @cli-team
/pulse.json @state-team
""".strip()
        + "\n",
        encoding="utf8",
    )

    ts = datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()

    _write(repo_root / "echo" / "engine.py", ENGINE_TEXT, timestamp=ts)
    _write(repo_root / "scripts" / "echo_tool.py", CLI_TEXT, timestamp=ts)
    _write(repo_root / "docs" / "echo" / "guide.md", DOC_TEXT, timestamp=ts)
    _write(repo_root / "docs" / "data" / "sample.json", DATA_TEXT, timestamp=ts)
    _write(repo_root / "pulse.json", STATE_TEXT, timestamp=ts)

    return repo_root


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf8")).hexdigest()


def test_refresh_manifest_emits_golden_document(sample_repo: Path) -> None:
    manifest_path = sample_repo / "echo_manifest.json"
    manifest_module.refresh_manifest(
        root=sample_repo,
        manifest_path=manifest_path,
        generated_at="2024-01-01T00:00:00+00:00",
    )

    produced_text = manifest_path.read_text(encoding="utf8")
    produced = manifest_module.load_manifest(manifest_path)

    expected = {
        "schema_version": "1.0",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "artifact_total": 5,
        "categories": {
            "clis": [
                {
                    "path": "scripts/echo_tool.py",
                    "digest": {"sha256": _sha(CLI_TEXT)},
                    "size": len(CLI_TEXT.encode("utf8")),
                    "last_modified": "2024-01-01T00:00:00+00:00",
                    "version": "unknown",
                    "owners": ["@cli-team"],
                    "tags": [
                        "category:clis",
                        "ext:py",
                        "lang:python",
                        "top:scripts",
                    ],
                }
            ],
            "datasets": [
                {
                    "path": "docs/data/sample.json",
                    "digest": {"sha256": _sha(DATA_TEXT)},
                    "size": len(DATA_TEXT.encode("utf8")),
                    "last_modified": "2024-01-01T00:00:00+00:00",
                    "version": "unknown",
                    "owners": ["@data-team"],
                    "tags": [
                        "category:datasets",
                        "ext:json",
                        "format:json",
                        "top:docs",
                    ],
                }
            ],
            "docs": [
                {
                    "path": "docs/echo/guide.md",
                    "digest": {"sha256": _sha(DOC_TEXT)},
                    "size": len(DOC_TEXT.encode("utf8")),
                    "last_modified": "2024-01-01T00:00:00+00:00",
                    "version": "unknown",
                    "owners": ["@docs"],
                    "tags": [
                        "category:docs",
                        "ext:md",
                        "format:markdown",
                        "top:docs",
                    ],
                }
            ],
            "engines": [
                {
                    "path": "echo/engine.py",
                    "digest": {"sha256": _sha(ENGINE_TEXT)},
                    "size": len(ENGINE_TEXT.encode("utf8")),
                    "last_modified": "2024-01-01T00:00:00+00:00",
                    "version": "unknown",
                    "owners": ["@engineers"],
                    "tags": [
                        "category:engines",
                        "ext:py",
                        "lang:python",
                        "top:echo",
                    ],
                }
            ],
            "states": [
                {
                    "path": "pulse.json",
                    "digest": {"sha256": _sha(STATE_TEXT)},
                    "size": len(STATE_TEXT.encode("utf8")),
                    "last_modified": "2024-01-01T00:00:00+00:00",
                    "version": "unknown",
                    "owners": ["@state-team"],
                    "tags": [
                        "category:states",
                        "ext:json",
                        "format:json",
                        "top:root",
                    ],
                }
            ],
        },
    }

    assert produced == expected

    expected_serialised = json.dumps(expected, indent=2, ensure_ascii=False, sort_keys=True)
    assert produced_text == expected_serialised + "\n"


def test_verify_manifest_detects_tampering(sample_repo: Path) -> None:
    manifest_path = sample_repo / "echo_manifest.json"
    manifest_module.refresh_manifest(
        root=sample_repo,
        manifest_path=manifest_path,
        generated_at="2024-01-01T00:00:00+00:00",
    )

    target = sample_repo / "echo" / "engine.py"
    target.write_text("print('modified')\n", encoding="utf8")

    with pytest.raises(manifest_module.ManifestDriftError) as exc:
        manifest_module.verify_manifest(
            root=sample_repo,
            manifest_path=manifest_path,
            append_summary=False,
        )

    assert any("echo/engine.py" in mismatch for mismatch in exc.value.mismatches)
