from __future__ import annotations

import json
from pathlib import Path

import jsonschema


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "echo_manifest.schema.json"


def test_schema_accepts_minimal_payload() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = {
        "version": "1.0.0",
        "generated_at": "1970-01-01T00:00:00Z",
        "engines": [
            {
                "name": "echo.example",
                "path": "echo/example.py",
                "kind": "engine",
                "status": "active",
                "entrypoints": ["echo.example"],
                "tests": ["tests/test_example.py"],
            }
        ],
        "states": {
            "cycle": 1,
            "resonance": 1.0,
            "amplification": 1.0,
            "snapshots": [
                {
                    "timestamp": "1970-01-01T00:00:00Z",
                    "message": "initialised",
                    "hash": "deadbeef",
                }
            ],
        },
        "kits": [
            {
                "name": "akit",
                "path": "echo/akit",
                "api": "echo.akit",
                "capabilities": ["run"],
            }
        ],
        "artifacts": [
            {
                "type": "json",
                "path": "manifest/sample.json",
                "content_hash": "0123456789ab",
            }
        ],
        "ci": {"integration": ["ci"]},
        "meta": {"commit_sha": "HEAD", "branch": "main", "author": "Echo"},
    }
    jsonschema.Draft202012Validator(schema).validate(payload)
