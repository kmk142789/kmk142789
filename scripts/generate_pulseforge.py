#!/usr/bin/env python3
"""Generate PulseForge data for Echo Codex visualization."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GRAPH = REPO_ROOT / "viewer/constellation_app/public/graph.json"
DEFAULT_PULSE = REPO_ROOT / "pulse_history.json"
DEFAULT_OUT = REPO_ROOT / "viewer/constellation_app/public/pulseforge.json"

MERGE_RE = re.compile(r"Merge pull request #(\d+)")
IGNORED_DEP_EXTENSIONS = (
    ".md",
    ".rst",
    ".txt",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".json",
    ".csv",
    ".yml",
    ".yaml",
    ".lock",
)
IGNORED_DEP_PREFIXES = (
    "docs/",
    "tests/",
    "reports/",
    "puzzle_",
    "puzzles/",
)


@dataclass(slots=True)
class MergeNode:
    pr_id: str
    commit_hash: str | None
    timestamp: str | None


@dataclass(slots=True)
class FileStat:
    path: str
    additions: int
    deletions: int


@dataclass(slots=True)
class PulseForgePR:
    pr_id: str
    merge_commit: str
    timestamp: str | None
    summary: str
    additions: int
    deletions: int
    files: list[FileStat]
    contract_type: str


@dataclass(slots=True)
class Heartbeat:
    timestamp: str
    message: str
    kind: str


def run_git(args: Sequence[str]) -> str:
    result = subprocess.run(args, cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def parse_graph(path: Path) -> list[MergeNode]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    merges: list[MergeNode] = []
    for node in payload.get("nodes", []):
        if node.get("type") != "commit":
            continue
        data = node.get("data") or {}
        message = data.get("message", "")
        match = MERGE_RE.search(message)
        if not match:
            continue
        merges.append(
            MergeNode(
                pr_id=match.group(1),
                commit_hash=data.get("hash"),
                timestamp=data.get("timestamp"),
            )
        )
    return merges


def classify_contract(files: Iterable[str]) -> str:
    lowered = [path.lower() for path in files]
    if any("math" in path for path in lowered):
        return "math"
    if any("stake" in path for path in lowered):
        return "staking"
    if any("govern" in path for path in lowered):
        return "governance"
    return "echo-system"


def parse_numstat(commit: str) -> list[FileStat]:
    output = run_git(["git", "show", commit, "--numstat", "--format="])
    stats: list[FileStat] = []
    for line in output.splitlines():
        parts = line.strip().split("\t")
        if len(parts) != 3:
            continue
        add, delete, path = parts
        if add == "-" or delete == "-":
            additions = 0
            deletions = 0
        else:
            additions = int(add)
            deletions = int(delete)
        stats.append(FileStat(path=path, additions=additions, deletions=deletions))
    return stats


def collect_summary(commit: str) -> str:
    try:
        summary = run_git(
            [
                "git",
                "log",
                f"{commit}^2",
                "--not",
                f"{commit}^1",
                "--format=%s",
                "-n",
                "1",
            ]
        )
    except subprocess.CalledProcessError:
        summary = ""
    return summary or "Merged pull request"


def serialise_timestamp(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        parsed = dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S %z")
    except ValueError:
        return raw
    return parsed.astimezone(dt.timezone.utc).isoformat()


def load_heartbeats(path: Path, limit: int = 120) -> list[Heartbeat]:
    if not path.exists():
        return []
    records = json.loads(path.read_text(encoding="utf-8"))
    events: list[Heartbeat] = []
    for entry in records[-limit:]:
        message = str(entry.get("message", ""))
        lowered = message.lower()
        if "evolve" not in lowered and "ascend" not in lowered:
            continue
        timestamp = entry.get("timestamp")
        if not isinstance(timestamp, (int, float)):
            continue
        iso = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc).isoformat()
        kind = "ascend" if "ascend" in lowered else "evolve"
        events.append(Heartbeat(timestamp=iso, message=message, kind=kind))
    events.sort(key=lambda hb: hb.timestamp)
    return events


def build_prs(merges: list[MergeNode]) -> list[PulseForgePR]:
    prs: list[PulseForgePR] = []
    for merge in merges:
        if not merge.commit_hash:
            continue
        stats = parse_numstat(merge.commit_hash)
        additions = sum(item.additions for item in stats)
        deletions = sum(item.deletions for item in stats)
        summary = collect_summary(merge.commit_hash)
        contract_type = classify_contract(item.path for item in stats)
        prs.append(
            PulseForgePR(
                pr_id=merge.pr_id,
                merge_commit=merge.commit_hash,
                timestamp=serialise_timestamp(merge.timestamp),
                summary=summary,
                additions=additions,
                deletions=deletions,
                files=stats,
                contract_type=contract_type,
            )
        )
    prs.sort(key=lambda item: (item.timestamp or ""))
    return prs


def build_edges(prs: list[PulseForgePR]) -> list[dict[str, object]]:
    file_to_prs: dict[str, set[str]] = defaultdict(set)
    for pr in prs:
        for stat in pr.files:
            path = stat.path
            lowered = path.lower()
            if lowered.endswith(IGNORED_DEP_EXTENSIONS):
                continue
            if any(lowered.startswith(prefix) for prefix in IGNORED_DEP_PREFIXES):
                continue
            file_to_prs[path].add(pr.pr_id)

    edge_map: dict[tuple[str, str], set[str]] = defaultdict(set)
    for path, pr_ids in file_to_prs.items():
        if len(pr_ids) < 2:
            continue
        for a, b in combinations(sorted(pr_ids), 2):
            edge_map[(a, b)].add(path)

    edges: list[dict[str, object]] = []
    for (a, b), files in sorted(edge_map.items()):
        edges.append(
            {
                "source": a,
                "target": b,
                "weight": len(files),
                "files": sorted(files),
            }
        )
    return edges


def to_serialisable(prs: list[PulseForgePR], edges: list[dict[str, object]], heartbeats: list[Heartbeat]) -> dict[str, object]:
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "prs": [],
        "edges": edges,
        "heartbeats": [],
    }
    for pr in prs:
        files_payload = [
            {
                "path": stat.path,
                "additions": stat.additions,
                "deletions": stat.deletions,
            }
            for stat in pr.files
        ]
        payload["prs"].append(
            {
                "id": pr.pr_id,
                "merge_commit": pr.merge_commit,
                "timestamp": pr.timestamp,
                "summary": pr.summary,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "lines_changed": pr.additions + pr.deletions,
                "contract_type": pr.contract_type,
                "files": files_payload,
                "url": f"https://github.com/kmk142789/kmk142789/pull/{pr.pr_id}",
            }
        )
    for hb in heartbeats:
        payload["heartbeats"].append(
            {
                "timestamp": hb.timestamp,
                "message": hb.message,
                "kind": hb.kind,
            }
        )
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PulseForge dataset")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--pulse", type=Path, default=DEFAULT_PULSE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    merges = parse_graph(args.graph)
    if not merges:
        raise SystemExit("No merge commits found in graph dataset")
    prs = build_prs(merges)
    edges = build_edges(prs)
    heartbeats = load_heartbeats(args.pulse)
    payload = to_serialisable(prs, edges, heartbeats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"PulseForge dataset written to {args.out} with {len(prs)} PRs and {len(heartbeats)} heartbeats")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
