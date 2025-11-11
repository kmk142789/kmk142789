from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List

from .engine import run as run_engine
from .parser import discover_artifacts
from .parser.models import ArtifactType
from .schema_utils import validate_artifact, validate_crosslinks


def _print_validation_table(errors: Dict[str, List[str]]) -> None:
    headers = ["Artifact", "Status"]
    widths = [max(len(headers[0]), max((len(name) for name in errors.keys()), default=0)), len(headers[1])]
    print(f"{headers[0]:<{widths[0]}} | {headers[1]}")
    print(f"{'-' * widths[0]}-+-{'-' * len(headers[1])}")
    for name, issues in sorted(errors.items()):
        status = "OK" if not issues else "; ".join(issues)
        print(f"{name:<{widths[0]}} | {status}")


def command_validate(path: Path) -> int:
    artifacts, crosslinks = discover_artifacts(path)
    errors: Dict[str, List[str]] = {}
    for artifact_type, artifact in artifacts.items():
        errors[str(artifact_type.value)] = validate_artifact(artifact)
    crosslink_errors = validate_crosslinks([link.to_dict() for link in crosslinks])
    if crosslink_errors:
        errors["crosslinks"] = crosslink_errors
    else:
        errors.setdefault("crosslinks", [])
    _print_validation_table(errors)
    return 0 if all(not issue for issue in errors.values()) else 1


def command_report(path: Path, output_dir: Path) -> int:
    result = run_engine(path, output_dir)
    validations = {
        artifact_type.value: validate_artifact(artifact)
        for artifact_type, artifact in result.artifacts.items()
    }
    validations["crosslinks"] = validate_crosslinks([link.to_dict() for link in result.crosslinks])
    _print_validation_table(validations)
    print(f"Report written to {output_dir / 'CONTRADICTIONS.md'}")
    return 0


def command_site(path: Path, output_dir: Path) -> int:
    result = run_engine(path, output_dir)
    site_dir = output_dir / "site"
    site_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(output_dir / "matrix.json", site_dir / "matrix.json")
    print(f"Static site data refreshed in {site_dir}")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="asterc")
    parser.add_argument("command", help="Command to run: asterc:validate, asterc:report, asterc:site")
    parser.add_argument("path", nargs="?", default=".", help="Path containing identity artifacts")
    args = parser.parse_args(argv)

    command = args.command
    base_path = Path(args.path).resolve()
    output_dir = Path("reports").resolve()

    if command == "asterc:validate":
        return command_validate(base_path)
    if command == "asterc:report":
        return command_report(base_path, output_dir)
    if command == "asterc:site":
        return command_site(base_path, output_dir)
    parser.error(f"Unknown command {command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
