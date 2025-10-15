from __future__ import annotations

from pathlib import Path

import jsonschema

from tools.echo_manifest import generate_manifest_data, load_schema


def test_schema_loads() -> None:
    schema = load_schema()
    jsonschema.Draft202012Validator.check_schema(schema)


def test_generated_manifest_conforms(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "echo").mkdir()
    (repo_root / "echo" / "sample_engine.py").write_text(
        "def main():\n    return 'ok'\n",
        encoding="utf-8",
    )
    manifest = generate_manifest_data(repo_root).payload
    schema = load_schema()
    jsonschema.validate(manifest, schema)
