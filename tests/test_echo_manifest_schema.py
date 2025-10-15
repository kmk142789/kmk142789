"""Schema validation tests for echo_manifest."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from tools.echo_manifest import EchoManifestGenerator


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schema" / "echo_manifest.schema.json"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_schema_is_valid() -> None:
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)


def test_generated_manifest_matches_schema(tmp_path: Path) -> None:
    (tmp_path / "echo").mkdir()
    (tmp_path / "modules").mkdir()
    (tmp_path / "tests").mkdir()

    engine_path = tmp_path / "echo" / "alpha_engine.py"
    engine_path.write_text(
        """def main():\n    return 'alpha'\n""",
        encoding="utf-8",
    )

    test_path = tmp_path / "tests" / "test_alpha.py"
    test_path.write_text(
        """def test_alpha():\n    assert True\n""",
        encoding="utf-8",
    )

    schema = load_schema()
    generator = EchoManifestGenerator(tmp_path)
    manifest = generator.build(generated_at="2024-01-01T00:00:00Z")

    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(manifest))
    assert not errors, f"Schema validation errors: {[error.message for error in errors]}"
