"""Auto-release utilities for Echo."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .graph import build_graph


@dataclass
class ReleaseArtifacts:
    version: str
    changelog: str
    sbom_path: Path
    signatures: List[Dict[str, str]]


def _semver_tuple(version: str) -> Tuple[int, int, int]:
    major, minor, patch = (int(part) for part in version.split("."))
    return major, minor, patch


def bump_version(current: str, bump: str) -> str:
    major, minor, patch = _semver_tuple(current)
    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


def _list_names(entries: Iterable[dict]) -> List[str]:
    return sorted(item["name"] for item in entries if isinstance(item, dict) and "name" in item)


def _state_entries(manifest: dict) -> List[dict]:
    states = manifest.get("states", [])
    if isinstance(states, dict):
        return [{"name": f"cycle-{states.get('cycle', 0)}"}]
    return [entry for entry in states if isinstance(entry, dict)]


def _kit_entries(manifest: dict) -> List[dict]:
    kits = manifest.get("kits")
    if isinstance(kits, list):
        return [entry for entry in kits if isinstance(entry, dict)]
    legacy = manifest.get("assistant_kits", [])
    if isinstance(legacy, list):
        return [entry for entry in legacy if isinstance(entry, dict)]
    return []


def determine_bump(previous: dict, current: dict) -> str:
    if _list_names(previous.get("engines", [])) != _list_names(current.get("engines", [])):
        return "major"
    if _list_names(_state_entries(previous)) != _list_names(_state_entries(current)):
        return "minor"
    return "patch"


def generate_changelog(diff: dict, commits: Iterable[str], impact: Iterable[str]) -> str:
    lines = ["## Changes"]
    for section, values in diff.items():
        lines.append(f"- {section}: {', '.join(values) if values else 'no changes'}")
    commit_list = list(commits)
    if commit_list:
        lines.append("## Commits")
        lines.extend(f"- {commit}" for commit in commit_list)
    impact_list = list(impact)
    if impact_list:
        lines.append("## Impact")
        lines.extend(f"- {item}" for item in impact_list)
    return "\n".join(lines)


def build_diff(previous: dict, current: dict) -> dict:
    return {
        "engines": sorted(
            set(_list_names(current.get("engines", []))) - set(_list_names(previous.get("engines", [])))
        ),
        "states": sorted(
            set(_list_names(_state_entries(current))) - set(_list_names(_state_entries(previous)))
        ),
        "kits": sorted(
            set(_list_names(_kit_entries(current))) - set(_list_names(_kit_entries(previous)))
        ),
    }


def generate_sbom(manifest: dict, version: str) -> dict:
    components = []
    for entry in manifest.get("engines", []):
        if isinstance(entry, dict) and "name" in entry:
            components.append({"type": "engine", "name": entry["name"], "version": version})
    for entry in _state_entries(manifest):
        components.append({"type": "state", "name": entry["name"], "version": version})
    for entry in _kit_entries(manifest):
        if "name" in entry:
            components.append({"type": "kit", "name": entry["name"], "version": version})
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "metadata": {"component": {"name": "echo", "version": version}},
        "components": components,
    }


def sign_artifact(path: Path) -> Dict[str, str]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"path": str(path), "sha256": digest}


def prepare_release(
    *,
    current_manifest: Path,
    previous_manifest: Path,
    current_version: str,
    commits: Iterable[str],
) -> ReleaseArtifacts:
    previous = json.loads(previous_manifest.read_text(encoding="utf-8"))
    current = json.loads(current_manifest.read_text(encoding="utf-8"))
    bump = determine_bump(previous, current)
    next_version = bump_version(current_version, bump)
    diff = build_diff(previous, current)
    graph = build_graph(manifest=current)
    changelog = generate_changelog(diff, commits, impact=graph.nodes.keys())
    sbom = generate_sbom(current, next_version)
    sbom_path = current_manifest.parent / f"sbom-{next_version}.json"
    sbom_path.write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    signature = sign_artifact(sbom_path)
    return ReleaseArtifacts(version=next_version, changelog=changelog, sbom_path=sbom_path, signatures=[signature])


def _cmd_prepare(args: argparse.Namespace) -> int:
    artifacts = prepare_release(
        current_manifest=Path(args.manifest),
        previous_manifest=Path(args.previous),
        current_version=args.version,
        commits=args.commit,
    )
    payload = {
        "version": artifacts.version,
        "changelog": artifacts.changelog,
        "sbom": str(artifacts.sbom_path),
        "signatures": artifacts.signatures,
    }
    print(json.dumps(payload, indent=2))
    return 0


def build_parser(subparsers: argparse._SubParsersAction) -> None:
    release_parser = subparsers.add_parser("release", help="Release automation")
    release_sub = release_parser.add_subparsers(dest="release_command", required=True)

    prepare_parser = release_sub.add_parser("prepare", help="Prepare release artifacts")
    prepare_parser.add_argument("--manifest", required=True, help="Current manifest path")
    prepare_parser.add_argument("--previous", required=True, help="Previous manifest path")
    prepare_parser.add_argument("--version", required=True, help="Current version")
    prepare_parser.add_argument("--commit", action="append", default=[], help="Commit messages")
    prepare_parser.set_defaults(func=_cmd_prepare)


__all__ = [
    "ReleaseArtifacts",
    "build_diff",
    "build_parser",
    "bump_version",
    "determine_bump",
    "generate_changelog",
    "generate_sbom",
    "prepare_release",
    "sign_artifact",
]

