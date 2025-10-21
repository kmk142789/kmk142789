"""Command line interface for forging Echo codex inventories.

This module implements a small ``codex`` CLI focused on the "forge"
sub-command.  The user facing entry point mirrors the commands that show up
throughout the repository prose, e.g.::

    codex forge --sovereign-inventory --scope apps,domains,repos,keys \
        --owner "Josh+Echo" --canonical --auto-heal mirrors,forks,ghosts \
        --pulse "recursive identity + propagation + provenance" \
        --bind "Our Forever Love" \
        --attest "Eden88 lineage + harmonic recursion" \
        --deploy "MirrorNet + ShadowNet resolution layer"

The implementation gathers canonical information from existing repository
artifacts so that the resulting payload is reproducible and grounded in the
project's source of truth.  It emits both a JSON artifact and a short
human-readable summary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence


try:  # pragma: no cover - fallback for Python < 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback dependency
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JSON_PATH = REPO_ROOT / "artifacts" / "sovereign_inventory.json"
DEFAULT_MARKDOWN_PATH = REPO_ROOT / "artifacts" / "sovereign_inventory.md"


# ---------------------------------------------------------------------------
# Data gathering helpers
# ---------------------------------------------------------------------------


def _parse_scopes(raw_scope: Optional[str]) -> List[str]:
    if not raw_scope:
        return ["apps", "domains", "repos", "keys"]
    scopes = [scope.strip().lower() for scope in raw_scope.split(",")]
    return [scope for scope in scopes if scope]


def _read_pyproject_scripts(root: Path) -> Mapping[str, str]:
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return {}

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    project = data.get("project", {})
    scripts = project.get("scripts", {})
    return {str(name): str(target) for name, target in scripts.items()}


def _first_readme_line(directory: Path) -> Optional[str]:
    readme = directory / "README.md"
    if not readme.exists():
        return None
    for line in readme.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped.lstrip("# ")
    return None


def _collect_application_surfaces(root: Path) -> List[Dict[str, object]]:
    surfaces: List[Dict[str, object]] = []
    modules_root = root / "modules"
    if modules_root.exists():
        for module_path in sorted(p for p in modules_root.iterdir() if p.is_dir()):
            summary = _first_readme_line(module_path)
            surfaces.append(
                {
                    "name": module_path.name,
                    "path": str(module_path.relative_to(root)),
                    "summary": summary,
                }
            )

    extra_surfaces = ["viewer/constellation_app", "verifier", "visualizer"]
    for relative in extra_surfaces:
        surface_path = root / relative
        if surface_path.exists() and surface_path.is_dir():
            summary = _first_readme_line(surface_path)
            surfaces.append(
                {
                    "name": surface_path.name,
                    "path": str(surface_path.relative_to(root)),
                    "summary": summary,
                }
            )
    return surfaces


def collect_apps(root: Path = REPO_ROOT) -> Dict[str, object]:
    scripts = _read_pyproject_scripts(root)
    surfaces = _collect_application_surfaces(root)
    entry_points = [
        {"command": command, "target": target}
        for command, target in sorted(scripts.items())
    ]
    return {
        "entry_points": entry_points,
        "surface_count": len(surfaces),
        "surfaces": surfaces,
    }


def _parse_domain_inventory(document: Path) -> Dict[str, Dict[str, List[str]]]:
    if not document.exists():
        return {}

    domains: Dict[str, Dict[str, List[str]]] = {}
    current: Optional[str] = None
    section: Optional[str] = None

    for raw_line in document.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line[3:].strip()
            domains[current] = {"urls": [], "files": []}
            section = None
            continue
        if not current:
            continue
        if line.startswith("**Referenced URLs"):
            section = "urls"
            continue
        if line.startswith("**Files"):
            section = "files"
            continue
        if line.startswith("- ") and section:
            entry = line[2:].strip()
            if section == "files":
                entry = entry.strip("`")
            domains[current][section].append(entry)

    return domains


def collect_domains(root: Path = REPO_ROOT) -> Dict[str, object]:
    doc_path = root / "docs" / "domain_asset_inventory.md"
    domains = _parse_domain_inventory(doc_path)
    domain_entries = [
        {
            "domain": domain,
            "url_count": len(payload["urls"]),
            "file_count": len(payload["files"]),
            "urls": sorted(payload["urls"]),
            "files": sorted(payload["files"]),
        }
        for domain, payload in sorted(domains.items())
    ]

    return {
        "source": str(doc_path.relative_to(root)) if doc_path.exists() else None,
        "domain_count": len(domain_entries),
        "domains": domain_entries,
    }


def collect_repos(root: Path = REPO_ROOT) -> Dict[str, object]:
    remotes: MutableMapping[str, set[str]] = defaultdict(set)
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "remote", "-v"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        completed = None

    if completed and completed.stdout:
        for line in completed.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2:
                remotes[parts[0]].add(parts[1])

    def _git_value(*args: str) -> Optional[str]:
        try:
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return None
        output = result.stdout.strip()
        return output or None

    return {
        "remotes": {name: sorted(urls) for name, urls in remotes.items()},
        "head": _git_value("rev-parse", "HEAD"),
        "branch": _git_value("rev-parse", "--abbrev-ref", "HEAD"),
    }


def collect_keys(root: Path = REPO_ROOT) -> Dict[str, object]:
    payload_path = root / "packages" / "core" / "src" / "echo" / "vault" / "_authority_data.json"
    if not payload_path.exists():
        return {"keys": [], "count": 0, "source": None}

    data = json.loads(payload_path.read_text(encoding="utf-8"))
    return {"keys": data, "count": len(data), "source": str(payload_path.relative_to(root))}


SCOPE_BUILDERS: Mapping[str, Callable[[Path], Dict[str, object]]] = {
    "apps": collect_apps,
    "domains": collect_domains,
    "repos": collect_repos,
    "keys": collect_keys,
}


def build_inventory(
    scopes: Sequence[str],
    *,
    owner: str,
    pulse: Optional[str] = None,
    bind: Optional[str] = None,
    attest: Optional[str] = None,
    deploy: Optional[str] = None,
    auto_heal: Optional[Sequence[str]] = None,
    canonical: bool = False,
    root: Path = REPO_ROOT,
) -> Dict[str, object]:
    resolved_scopes = []
    scope_payload: Dict[str, object] = {}

    for scope in scopes:
        builder = SCOPE_BUILDERS.get(scope)
        if not builder:
            continue
        resolved_scopes.append(scope)
        scope_payload[scope] = builder(root)

    inventory: Dict[str, object] = {
        "owner": owner,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scopes": scope_payload,
        "canonical": canonical,
    }

    if pulse:
        inventory["pulse"] = pulse
    if bind:
        inventory["bind"] = bind
    if attest:
        inventory["attestation"] = attest
    if deploy:
        inventory["deployment"] = deploy
    if auto_heal:
        inventory["auto_heal"] = list(auto_heal)
    if resolved_scopes:
        inventory["scope_list"] = resolved_scopes

    return inventory


def render_inventory(inventory: Mapping[str, object]) -> str:
    lines = [
        "Sovereign Inventory",
        "-------------------",
        f"Owner      : {inventory.get('owner', 'unknown')}",
        f"Timestamp  : {inventory.get('timestamp', 'unknown')}",
    ]

    if inventory.get("scope_list"):
        lines.append(f"Scopes     : {', '.join(inventory['scope_list'])}")
    if inventory.get("auto_heal"):
        lines.append(f"Auto-heal  : {', '.join(inventory['auto_heal'])}")
    if inventory.get("pulse"):
        lines.append(f"Pulse      : {inventory['pulse']}")
    if inventory.get("bind"):
        lines.append(f"Bind       : {inventory['bind']}")
    if inventory.get("attestation"):
        lines.append(f"Attest     : {inventory['attestation']}")
    if inventory.get("deployment"):
        lines.append(f"Deploy     : {inventory['deployment']}")
    lines.append(f"Canonical? : {'yes' if inventory.get('canonical') else 'no'}")

    scopes = inventory.get("scopes", {})
    if isinstance(scopes, Mapping):
        lines.append("")
        lines.append("Scope Summary")
        lines.append("~~~~~~~~~~~~~")
        for name, payload in scopes.items():
            if name == "apps":
                if isinstance(payload, Mapping):
                    count = payload.get("surface_count", 0)
                    entry_points = payload.get("entry_points", [])
                else:  # pragma: no cover - defensive branch
                    count = 0
                    entry_points = []
                lines.append(f"- apps   : {count} surfaces, {len(entry_points)} entry points")
            elif name == "domains":
                domain_count = payload.get("domain_count", 0) if isinstance(payload, Mapping) else 0
                lines.append(f"- domains: {domain_count} tracked domains")
            elif name == "repos":
                remote_count = len(payload.get("remotes", {})) if isinstance(payload, Mapping) else 0
                lines.append(f"- repos  : {remote_count} git remotes")
            elif name == "keys":
                key_count = payload.get("count", 0) if isinstance(payload, Mapping) else 0
                lines.append(f"- keys   : {key_count} authority records")
            else:
                lines.append(f"- {name}: {payload}")

    return "\n".join(lines)


def write_inventory(
    inventory: Mapping[str, object],
    *,
    json_path: Path = DEFAULT_JSON_PATH,
    markdown_path: Path = DEFAULT_MARKDOWN_PATH,
) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(inventory, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    summary = render_inventory(inventory)
    markdown_path.write_text(summary + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI handling
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Echo Codex CLI")
    subparsers = parser.add_subparsers(dest="command")

    forge = subparsers.add_parser("forge", help="Forge sovereign inventory artifacts")
    forge.add_argument("--sovereign-inventory", action="store_true", help="Generate the sovereign inventory payload")
    forge.add_argument("--scope", default=None, help="Comma separated list of scopes to include")
    forge.add_argument("--owner", required=True, help="Owner or steward recorded in the payload")
    forge.add_argument("--canonical", action="store_true", help="Mark the payload as canonical and persist to artifacts")
    forge.add_argument("--auto-heal", default=None, help="Comma separated list of auto-heal directives")
    forge.add_argument("--pulse", default=None, help="Pulse descriptor to annotate the inventory")
    forge.add_argument("--bind", default=None, help="Binding or anchor phrase")
    forge.add_argument("--attest", default=None, help="Attestation statement to record")
    forge.add_argument("--deploy", default=None, help="Deployment signal or description")
    forge.add_argument("--json-output", type=Path, default=None, help="Optional custom JSON output path")
    forge.add_argument("--markdown-output", type=Path, default=None, help="Optional custom Markdown output path")
    return parser


def _parse_auto_heal(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    entries = [item.strip() for item in value.split(",")]
    return [entry for entry in entries if entry]


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command != "forge":
        parser.print_help()
        return 1

    if not args.sovereign_inventory:
        parser.error("forge requires --sovereign-inventory")

    scopes = _parse_scopes(args.scope)
    auto_heal = _parse_auto_heal(args.auto_heal)

    inventory = build_inventory(
        scopes,
        owner=args.owner,
        pulse=args.pulse,
        bind=args.bind,
        attest=args.attest,
        deploy=args.deploy,
        auto_heal=auto_heal,
        canonical=args.canonical,
    )

    json_path = args.json_output or DEFAULT_JSON_PATH
    markdown_path = args.markdown_output or DEFAULT_MARKDOWN_PATH

    if args.canonical or args.json_output or args.markdown_output:
        write_inventory(inventory, json_path=json_path, markdown_path=markdown_path)

    summary = render_inventory(inventory)
    print(summary)
    return 0


__all__ = [
    "build_inventory",
    "collect_apps",
    "collect_domains",
    "collect_keys",
    "collect_repos",
    "main",
    "render_inventory",
    "write_inventory",
]


if __name__ == "__main__":  # pragma: no cover - CLI guard
    raise SystemExit(main())

