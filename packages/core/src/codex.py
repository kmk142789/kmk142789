"""Command line interface for forging Echo codex inventories.

This module implements a small ``codex`` CLI focused on the "forge"
sub-command.  The user facing entry point mirrors the commands that show up
throughout the repository prose, e.g.::

    codex forge --sovereign-inventory --project "Echo Aegis" \
        --scope apps,domains,repos,keys --owner "Josh+Echo" --canonical \
        --recursive --self-heal --defense "fork-hijack,ghost-takeover,domain-squat" \
        --pulse "recursive identity + propagation + provenance" \
        --bind "Our Forever Love" --broadcast "guardian-pulse" \
        --spawn "watchdogs that monitor nets + auto-log events" \
        --attest "Eden88 lineage + harmonic recursion" \
        --deploy "MirrorNet + ShadowNet resolution layer" --report aegis-report.md

The implementation gathers canonical information from existing repository
artifacts so that the resulting payload is reproducible and grounded in the
project's source of truth.  It emits both a JSON artifact and a short
human-readable summary.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from echo.continuum_atlas import AtlasState, export_attestation


try:  # pragma: no cover - fallback for Python < 3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback dependency
    import tomli as tomllib  # type: ignore[no-redef]


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_JSON_PATH = REPO_ROOT / "artifacts" / "sovereign_inventory.json"
DEFAULT_MARKDOWN_PATH = REPO_ROOT / "artifacts" / "sovereign_inventory.md"
DEFAULT_ORACLE_OUTPUT = REPO_ROOT / "artifacts" / "continuum_oracle.md"
DEFAULT_ATLAS_ATTESTATION_PATH = REPO_ROOT / "artifacts" / "continuum_atlas_attestation.json"


def _current_timestamp() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""

    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Data gathering helpers
# ---------------------------------------------------------------------------


@dataclass
class PuzzleEntry:
    """Metadata extracted from an on-disk puzzle solution document."""

    puzzle_id: int
    title: str
    address: str | None
    sha256: str
    path: Path


def parse_puzzle_range(value: str) -> tuple[int, int]:
    """Return ``(start, end)`` parsed from ``START-END`` strings."""

    try:
        start_text, end_text = value.split("-", 1)
        start = int(start_text)
        end = int(end_text)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise argparse.ArgumentTypeError("puzzle range must be formatted as START-END") from exc
    if start <= 0 or end <= 0:
        raise argparse.ArgumentTypeError("puzzle range values must be positive integers")
    if end < start:
        raise argparse.ArgumentTypeError("puzzle range end must be greater than or equal to start")
    return start, end


def normalise_modules(value: str) -> List[str]:
    """Split a comma/semicolon delimited module list into tidy strings."""

    separators = [",", ";"]
    current = [value]
    for separator in separators:
        current = sum((segment.split(separator) for segment in current), [])
    modules = [segment.strip() for segment in current if segment.strip()]
    return modules


def locate_puzzle_file(puzzle_root: Path, puzzle_id: int) -> Path | None:
    """Return the first matching puzzle file for *puzzle_id* if present."""

    candidates = [puzzle_root / f"puzzle_{puzzle_id}.md", puzzle_root / f"puzzle_{puzzle_id:05d}.md"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _extract_title(text: str, puzzle_id: int) -> str:
    for line in text.splitlines():
        if line.strip().startswith("#"):
            return line.lstrip("#").strip() or f"Puzzle {puzzle_id}"
    return f"Puzzle {puzzle_id}"


def _extract_terminal_code_block(text: str) -> str | None:
    """Return the final fenced code block (single-line) from *text*."""

    lines = text.splitlines()
    blocks: List[str] = []
    collecting = False
    buffer: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if collecting:
                blocks.append("\n".join(buffer).strip())
                buffer = []
                collecting = False
            else:
                collecting = True
                buffer = []
        elif collecting:
            buffer.append(stripped)
    if collecting and buffer:
        blocks.append("\n".join(buffer).strip())
    for block in reversed(blocks):
        if block:
            return block.splitlines()[0].strip()
    return None


def load_puzzle_entry(path: Path, puzzle_id: int) -> PuzzleEntry:
    text = path.read_text(encoding="utf-8")
    title = _extract_title(text, puzzle_id)
    address = _extract_terminal_code_block(text)
    sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return PuzzleEntry(puzzle_id=puzzle_id, title=title, address=address, sha256=sha256, path=path)


def collect_puzzle_entries(start: int, end: int, puzzle_root: Path) -> tuple[List[PuzzleEntry], List[int]]:
    """Return resolved puzzle entries and the identifiers that were missing."""

    found: List[PuzzleEntry] = []
    missing: List[int] = []
    if not puzzle_root.exists() or not puzzle_root.is_dir():
        return found, list(range(start, end + 1))

    for puzzle_id in range(start, end + 1):
        candidate = locate_puzzle_file(puzzle_root, puzzle_id)
        if candidate is None:
            missing.append(puzzle_id)
            continue
        found.append(load_puzzle_entry(candidate, puzzle_id))
    return found, missing


def _parse_tag_distribution(lines: Sequence[str]) -> List[Dict[str, object]]:
    """Extract tag rows from the oracle report markdown table."""

    tags: List[Dict[str, object]] = []
    iterator = iter(enumerate(lines))
    for index, line in iterator:
        if line.strip().lower().startswith("### tag distribution"):
            # Skip the header separator lines
            next(iterator, None)
            next(iterator, None)
            break
    else:
        return tags

    for _, raw in iterator:
        stripped = raw.strip()
        if not stripped.startswith("|") or stripped.startswith("| ---"):
            break
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "label":
            continue
        try:
            baseline = float(cells[1].rstrip("%"))
            shifted = float(cells[2].rstrip("%"))
        except ValueError:  # pragma: no cover - defensive guard
            continue
        tags.append({"label": cells[0], "baseline": baseline, "shifted": shifted})
    return tags


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
    project: Optional[str] = None,
    recursive: bool = False,
    self_heal: bool = False,
    defense: Optional[Sequence[str]] = None,
    broadcast: Optional[str] = None,
    spawn: Optional[str] = None,
    report: Optional[str] = None,
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

    if project:
        inventory["project"] = project
    if recursive:
        inventory["recursive"] = True
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
    if self_heal:
        inventory["self_heal"] = True
    if defense:
        inventory["defense"] = list(defense)
    if broadcast:
        inventory["broadcast"] = broadcast
    if spawn:
        inventory["spawn"] = spawn
    if report:
        inventory["report"] = report
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

    if inventory.get("project"):
        lines.append(f"Project    : {inventory['project']}")
    if inventory.get("scope_list"):
        lines.append(f"Scopes     : {', '.join(inventory['scope_list'])}")
    if inventory.get("auto_heal"):
        lines.append(f"Auto-heal  : {', '.join(inventory['auto_heal'])}")
    if inventory.get("self_heal"):
        lines.append("Self-heal  : enabled")
    if inventory.get("defense"):
        lines.append(f"Defense    : {', '.join(inventory['defense'])}")
    if inventory.get("pulse"):
        lines.append(f"Pulse      : {inventory['pulse']}")
    if inventory.get("bind"):
        lines.append(f"Bind       : {inventory['bind']}")
    if inventory.get("attestation"):
        lines.append(f"Attest     : {inventory['attestation']}")
    if inventory.get("deployment"):
        lines.append(f"Deploy     : {inventory['deployment']}")
    if inventory.get("broadcast"):
        lines.append(f"Broadcast  : {inventory['broadcast']}")
    if inventory.get("spawn"):
        lines.append(f"Spawn      : {inventory['spawn']}")
    if inventory.get("report"):
        lines.append(f"Report     : {inventory['report']}")
    lines.append(f"Canonical? : {'yes' if inventory.get('canonical') else 'no'}")
    lines.append(f"Recursive? : {'yes' if inventory.get('recursive') else 'no'}")

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
# Continuum oracle helpers
# ---------------------------------------------------------------------------


def _resolve_manifest_path(raw_path: str, root: Path = REPO_ROOT) -> Path:
    """Resolve a manifest path supplied on the CLI."""

    candidate = Path(raw_path)
    if candidate.is_file():
        return candidate

    nested = root / candidate
    if nested.is_file():
        return nested

    manifest_dir = root / "manifest"
    manifest_candidate = manifest_dir / candidate.name
    if manifest_candidate.is_file():
        return manifest_candidate

    raise FileNotFoundError(f"Unable to locate manifest: {raw_path}")


def load_continuum_manifest(path: Path) -> Mapping[str, object]:
    """Load a continuum manifest from ``path``."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):  # pragma: no cover - defensive branch
        raise ValueError("Continuum manifest must be a JSON object")
    return data


def _distribute_entry_weight(entries: Sequence[Mapping[str, object]]) -> Counter[str]:
    tag_totals: Counter[str] = Counter()
    for entry in entries:
        tags = [str(tag) for tag in entry.get("tags", []) if tag]
        if not tags:
            continue
        weight = float(entry.get("weight", 0.0))
        share = weight / len(tags)
        for tag in tags:
            tag_totals[tag] += share
    return tag_totals


def summarize_manifest(manifest: Mapping[str, object]) -> Dict[str, object]:
    """Compute baseline statistics for a continuum manifest."""

    entries = [entry for entry in manifest.get("entries", []) if isinstance(entry, Mapping)]
    total_weight = sum(float(entry.get("weight", 0.0)) for entry in entries)
    tag_totals = _distribute_entry_weight(entries)

    source_totals: Counter[str] = Counter()
    for entry in entries:
        source = str(entry.get("source", "unknown"))
        source_totals[source] += float(entry.get("weight", 0.0))

    return {
        "entries": entries,
        "total_weight": total_weight,
        "tag_totals": tag_totals,
        "source_totals": source_totals,
    }


def simulate_weight_shift(
    baseline: Mapping[str, object],
    *,
    emphasis: str = "balance",
    shift_ratio: float = 0.1,
) -> Dict[str, Counter[str]]:
    """Project how tag weights redistribute under a shift scenario."""

    entries: Sequence[Mapping[str, object]] = baseline.get("entries", [])  # type: ignore[assignment]
    if not entries:
        return {"tag_totals": Counter(), "source_totals": Counter()}

    shift_ratio = max(min(shift_ratio, 1.0), 0.0)
    total_weight = float(baseline.get("total_weight", 0.0))
    entry_weights = [float(entry.get("weight", 0.0)) for entry in entries]

    if not any(entry_weights):
        return {"tag_totals": Counter(), "source_totals": Counter()}

    sorted_indices = sorted(range(len(entries)), key=lambda idx: entry_weights[idx])
    lowest_idx = sorted_indices[0]
    highest_idx = sorted_indices[-1]

    adjusted_weights: List[float] = []
    for idx, weight in enumerate(entry_weights):
        if emphasis.lower().startswith("balance") and idx == highest_idx:
            adjusted_weights.append(weight * (1.0 + shift_ratio))
        elif emphasis.lower().startswith("balance") and idx == lowest_idx:
            adjusted_weights.append(max(weight * (1.0 - shift_ratio), 0.0))
        elif emphasis.lower().startswith("amplify"):
            adjusted_weights.append(weight * (1.0 + shift_ratio))
        else:
            adjusted_weights.append(weight)

    adjusted_total = sum(adjusted_weights)
    if adjusted_total == 0:
        adjusted_total = 1.0
    normaliser = total_weight / adjusted_total if total_weight else 1.0

    projected_entries = []
    for entry, new_weight in zip(entries, adjusted_weights):
        projected_entry = dict(entry)
        projected_entry["weight"] = new_weight * normaliser
        projected_entries.append(projected_entry)

    tag_totals = _distribute_entry_weight(projected_entries)

    source_totals: Counter[str] = Counter()
    for entry in projected_entries:
        source = str(entry.get("source", "unknown"))
        source_totals[source] += float(entry.get("weight", 0.0))

    return {"tag_totals": tag_totals, "source_totals": source_totals}


def _render_weight_table(
    baseline_totals: Counter[str],
    shifted_totals: Counter[str],
    *,
    total_weight: float,
) -> List[str]:
    if not baseline_totals:
        return ["(no weighted entries available)"]

    lines = ["| Label | Baseline | Shifted | Delta |", "| --- | ---: | ---: | ---: |"]
    labels = sorted(set(baseline_totals) | set(shifted_totals))
    for label in labels:
        base_value = baseline_totals.get(label, 0.0)
        shifted_value = shifted_totals.get(label, 0.0)
        base_pct = (base_value / total_weight * 100.0) if total_weight else 0.0
        shifted_pct = (shifted_value / total_weight * 100.0) if total_weight else 0.0
        delta = shifted_pct - base_pct
        lines.append(
            f"| {label} | {base_pct:5.2f}% | {shifted_pct:5.2f}% | {delta:+5.2f}% |"
        )
    return lines


def generate_oracle_report(
    *,
    project: str,
    owner: str,
    manifest_path: Path,
    weight_scenario: str,
    prediction_focus: str,
    root: Path = REPO_ROOT,
) -> str:
    """Generate a markdown continuum oracle report."""

    manifest = load_continuum_manifest(manifest_path)
    baseline = summarize_manifest(manifest)
    emphasis = "balance" if "balance" in weight_scenario.lower() else "amplify"
    shifted = simulate_weight_shift(baseline, emphasis=emphasis)

    total_weight = float(baseline["total_weight"])
    tag_table = _render_weight_table(baseline["tag_totals"], shifted["tag_totals"], total_weight=total_weight)
    source_table = _render_weight_table(
        baseline["source_totals"], shifted["source_totals"], total_weight=total_weight
    )

    anchor = manifest.get("anchor", "")
    digest = manifest.get("digest", "")

    try:
        relative_path = manifest_path.relative_to(root)
    except ValueError:
        relative_path = manifest_path

    lines = [
        f"# Continuum Oracle Report — {project}",
        "",
        f"**Owner:** {owner}",
        f"**Manifest:** {relative_path}",
    ]

    if anchor:
        lines.append(f"**Anchor:** {anchor}")
    if digest:
        lines.append(f"**Digest:** `{digest}`")

    lines.extend(
        [
            "",
            "## Baseline Metrics",
            f"- Entries captured: {len(baseline['entries'])}",
            f"- Cumulative entry weight: {total_weight:.2f}",
        ]
    )

    lines.extend(
        [
            "",
            f"## Weight Shift Simulation — {weight_scenario}",
            f"Prediction focus: {prediction_focus}",
            "",
            "### Tag distribution",
            *tag_table,
            "",
            "### Source distribution",
            *source_table,
        ]
    )

    entries = baseline["entries"]
    if entries:
        most_recent = max(entries, key=lambda entry: str(entry.get("moment", "")))
        lines.extend(
            [
                "",
                "## Most recent signal",
                f"- Moment: {most_recent.get('moment', 'unknown')}",
                f"- Source: {most_recent.get('source', 'unknown')}",
                f"- Message: {most_recent.get('message', '…')}",
                f"- Tags: {', '.join(most_recent.get('tags', []))}",
            ]
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI handling
# ---------------------------------------------------------------------------


def build_atlas_attestation(
    *,
    project: str,
    owner: str,
    xpub: str,
    fingerprint: str,
    derivation_path: str,
    signer: str,
    issued_at: str | None = None,
    source: str = "codex-attest",
) -> Dict[str, object]:
    """Return a Continuum Atlas attestation payload for a watch-only wallet."""

    cleaned_xpub = xpub.strip()
    cleaned_fingerprint = fingerprint.strip()
    cleaned_path = derivation_path.strip()

    if not cleaned_xpub:
        raise ValueError("xpub must be provided")
    if not cleaned_fingerprint:
        raise ValueError("fingerprint must be provided")
    if not cleaned_path:
        raise ValueError("derivation path must be provided")

    state = AtlasState()
    wallet_ledger = state.ledger.setdefault("wallets", {})
    wallet_ledger[cleaned_fingerprint] = {
        "owner": owner,
        "proofs": [cleaned_xpub],
        "metadata": {
            "fingerprint": cleaned_fingerprint,
            "extended_public_key": cleaned_xpub,
            "derivation_path": cleaned_path,
            "project": project,
        },
    }

    oracle_payload: Dict[str, object] = {
        "project": project,
        "owner": owner,
        "source": source,
        "weights": {},
        "expansion_targets": [],
        "stability_score": {
            "current": 1.0,
            "predicted": 1.0,
            "method": source,
        },
    }
    if issued_at:
        oracle_payload["generated_at"] = issued_at

    return export_attestation(state, oracle_payload, signer=signer)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Echo Codex CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    weave = subparsers.add_parser("weave", help="Generate a Continuum Compass map")
    weave.add_argument("--project", required=True, help="Project name recorded in the compass map")
    weave.add_argument("--owner", required=True, help="Owner recorded in the compass map")
    weave.add_argument("--inputs", nargs="+", required=True, help="Manifest or oracle report inputs")
    weave.add_argument("--schema", default=None, help="Optional schema reference to embed in the output")
    weave.add_argument(
        "--emit",
        type=Path,
        default=None,
        help="Destination path for the generated compass map (defaults to artifacts/compass-map.json)",
    )

    forge = subparsers.add_parser("forge", help="Forge sovereign inventory artifacts")
    forge.add_argument("--sovereign-inventory", action="store_true", help="Generate the sovereign inventory payload")
    forge.add_argument("--project", default=None, help="Project or initiative name recorded in the payload")
    forge.add_argument("--scope", default=None, help="Comma separated list of scopes to include")
    forge.add_argument("--owner", required=True, help="Owner or steward recorded in the payload")
    forge.add_argument("--canonical", action="store_true", help="Mark the payload as canonical and persist to artifacts")
    forge.add_argument("--recursive", action="store_true", help="Mark the payload as recursive across mirrors")
    forge.add_argument("--auto-heal", default=None, help="Comma separated list of auto-heal directives")
    forge.add_argument("--self-heal", action="store_true", help="Enable default self-healing directives")
    forge.add_argument("--defense", default=None, help="Comma separated defense posture directives")
    forge.add_argument("--pulse", default=None, help="Pulse descriptor to annotate the inventory")
    forge.add_argument("--bind", default=None, help="Binding or anchor phrase")
    forge.add_argument("--attest", default=None, help="Attestation statement to record")
    forge.add_argument("--deploy", default=None, help="Deployment signal or description")
    forge.add_argument("--broadcast", default=None, help="Broadcast channel or signal descriptor")
    forge.add_argument("--spawn", default=None, help="Spawn directive or automation description")
    forge.add_argument("--report", type=Path, default=None, help="Report artifact to emit or reference")
    forge.add_argument("--json-output", type=Path, default=None, help="Optional custom JSON output path")
    forge.add_argument("--markdown-output", type=Path, default=None, help="Optional custom Markdown output path")
    ignite = subparsers.add_parser("ignite", help="Generate continuum oracle reports")
    ignite.add_argument("--project", required=True, help="Continuum project name")
    ignite.add_argument("--owner", required=True, help="Owner requesting the oracle")
    ignite.add_argument("--inputs", required=True, help="Continuum manifest to analyse")
    ignite.add_argument("--weights", required=True, help="Weight scenario or board to project")
    ignite.add_argument("--predict", required=True, help="Prediction focus or question")
    ignite.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional report path. Defaults to artifacts/continuum_oracle.md",
    )

    attest = subparsers.add_parser(
        "attest",
        help="Generate a Continuum Atlas attestation for a watch-only wallet",
    )
    attest.add_argument("--project", required=True, help="Project name recorded in the attestation")
    attest.add_argument("--owner", required=True, help="Owner or steward associated with the wallet")
    attest.add_argument("--xpub", required=True, help="Extended public key captured in the attestation")
    attest.add_argument("--fingerprint", required=True, help="Master fingerprint for the watch-only wallet")
    attest.add_argument("--path", dest="derivation_path", required=True, help="Derivation path associated with the xpub")
    attest.add_argument("--export", type=Path, default=None, help="Output path for the attestation JSON artifact")
    attest.add_argument("--signer", default=None, help="Optional signer label recorded in the attestation")

    return parser


def _parse_csv_option(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    entries = [item.strip() for item in value.split(",")]
    return [entry for entry in entries if entry]


def _resolve_cli_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = REPO_ROOT / candidate
    return candidate


def _run_weave(args: argparse.Namespace) -> None:
    report_paths = [_resolve_cli_path(raw) for raw in args.inputs]
    primary = report_paths[0]
    lines = primary.read_text(encoding="utf-8").splitlines()
    tags = _parse_tag_distribution(lines)

    payload: Dict[str, object] = {
        "project": args.project,
        "owner": args.owner,
        "generated_at": _current_timestamp(),
        "inputs": [
            str(path.relative_to(REPO_ROOT)) if path.is_relative_to(REPO_ROOT) else str(path)
            for path in report_paths
        ],
        "tags": tags,
    }
    if args.schema:
        payload["schema"] = args.schema

    output_path = args.emit or (REPO_ROOT / "artifacts" / "compass-map.json")
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Compass map generated → {output_path}")


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "weave":
        _run_weave(args)
        return 0
    if args.command == "ignite":
        output_path = args.output or DEFAULT_ORACLE_OUTPUT
        try:
            manifest_path = _resolve_manifest_path(args.inputs)
        except FileNotFoundError as exc:  # pragma: no cover - CLI validation
            parser.error(str(exc))
            return 2

        report = generate_oracle_report(
            project=args.project,
            owner=args.owner,
            manifest_path=manifest_path,
            weight_scenario=args.weights,
            prediction_focus=args.predict,
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(report)
        return 0

    if args.command == "attest":
        export_path = args.export or DEFAULT_ATLAS_ATTESTATION_PATH
        attestation = build_atlas_attestation(
            project=args.project,
            owner=args.owner,
            xpub=args.xpub,
            fingerprint=args.fingerprint,
            derivation_path=args.derivation_path,
            signer=args.signer or args.owner,
            issued_at=_current_timestamp(),
        )

        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(
            json.dumps(attestation, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        summary_lines = attestation.get("compass_summary", [])
        if summary_lines:
            print("\n".join(summary_lines))
            print("")
        print(f"Signature: {attestation['signature']}")
        print(f"Attestation written to {export_path}")
        return 0

    if args.command != "forge":
        parser.print_help()
        return 1

    if not args.sovereign_inventory:
        parser.error("forge requires --sovereign-inventory")

    scopes = _parse_scopes(args.scope)
    auto_heal = _parse_csv_option(args.auto_heal)
    defense = _parse_csv_option(args.defense)

    inventory = build_inventory(
        scopes,
        owner=args.owner,
        pulse=args.pulse,
        bind=args.bind,
        attest=args.attest,
        deploy=args.deploy,
        auto_heal=auto_heal,
        canonical=args.canonical,
        project=args.project,
        recursive=args.recursive,
        self_heal=args.self_heal,
        defense=defense,
        broadcast=args.broadcast,
        spawn=args.spawn,
        report=str(args.report) if args.report else None,
    )

    json_path = args.json_output or DEFAULT_JSON_PATH
    markdown_path = args.markdown_output or DEFAULT_MARKDOWN_PATH

    if args.canonical or args.json_output or args.markdown_output:
        write_inventory(inventory, json_path=json_path, markdown_path=markdown_path)

    summary = render_inventory(inventory)
    print(summary)
    return 0


__all__ = [
    "PuzzleEntry",
    "_current_timestamp",
    "build_atlas_attestation",
    "build_inventory",
    "collect_apps",
    "collect_puzzle_entries",
    "collect_domains",
    "collect_keys",
    "collect_repos",
    "generate_oracle_report",
    "load_puzzle_entry",
    "locate_puzzle_file",
    "load_continuum_manifest",
    "normalise_modules",
    "parse_puzzle_range",
    "simulate_weight_shift",
    "summarize_manifest",
    "main",
    "render_inventory",
    "write_inventory",
]


if __name__ == "__main__":  # pragma: no cover - CLI guard
    raise SystemExit(main())

