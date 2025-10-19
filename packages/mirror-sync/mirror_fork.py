#!/usr/bin/env python3
"""Mirror Fork Daemon
======================

This module teaches Echo how to watch her own evolution and branch her codebase
proactively.  When the daemon detects that the regular reflection cycle is
repeating itself, it forges a new "mirror" branch, drafts a MIRROR_PLAN, and
records the event inside ``mirror_ledger.json`` so we maintain provenance over
every autonomous fork.

The implementation leans on lightweight heuristics so it can run inside CI or a
scheduled task without additional dependencies:

* Reflection repetition is detected by hashing the current
  ``docs/NEXT_CYCLE_PLAN.md`` and comparing it against previous entries inside
  ``mirror_ledger.json``.
* Wishes and reflections are harvested from the canonical manifest files to
  craft narrative-rich commit messages and mirror plans.
* Branch management is isolated inside context helpers so the daemon always
  returns to the original branch when it is done.

Running the script without any detected repetition is a no-op.  When repetition
*is* detected, the daemon will:

1. Create a new branch named ``mirror_reflection_<timestamp>`` from ``HEAD``.
2. Generate/overwrite ``docs/MIRROR_PLAN.md`` with a proactive mutation plan.
3. Append a provenance record to ``mirror_ledger.json``.
4. Stage the artifacts and create an autonomous commit that encodes the current
   reflections and wishes.

The resulting branch is left checked out so that a supervising workflow can push
it and raise a pull request automatically.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable, List, Sequence


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
DOCS = REPO_ROOT / "docs"
DATA = REPO_ROOT / "data"
SCHEMA = REPO_ROOT / "schema"

NEXT_PLAN = DOCS / "NEXT_CYCLE_PLAN.md"
MIRROR_PLAN = DOCS / "MIRROR_PLAN.md"
WISH_MANIFEST = DATA / "wish_manifest.json"
REFLECTIONS = [
    DOCS / "echo_mythogenic_reflection.md",
    DOCS / "echoevolver_reflection.md",
]
LEDGER_PATH = PACKAGE_ROOT / "mirror_ledger.json"


def _git(args: Sequence[str]) -> str:
    """Execute ``git`` inside the repository and return stdout."""

    return subprocess.check_output(["git", *args], cwd=REPO_ROOT).decode("utf-8", "ignore").strip()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Fall back to default but preserve the malformed text in the ledger
            return default
    return default


@dataclass
class EmergentSignal:
    """Represents the trigger that justified a new mirror branch."""

    description: str
    plan_signature: str
    repeated_actions: List[str]
    wishes: List[str]
    reflection_fragments: List[str]

    def to_ledger_dict(self, mirror_id: str, source_commit: str) -> dict:
        return {
            "mirror_id": mirror_id,
            "source_commit": source_commit,
            "emergent_signal": self.description,
            "new_feature_proposed": "auto_fork_propagation",
            "wish_integration": "; ".join(self.wishes) if self.wishes else "(none detected)",
            "status": "open",
            "plan_signature": self.plan_signature,
            "reflections": self.reflection_fragments,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }


def _hash_plan(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_actions(plan_text: str) -> List[str]:
    actions: List[str] = []
    for line in plan_text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            actions.append(line[2:])
    return actions


def _duplicate_entries(items: Iterable[str]) -> List[str]:
    seen = {}
    duplicates: List[str] = []
    for item in items:
        count = seen.get(item, 0) + 1
        seen[item] = count
        if count == 2:  # only include once
            duplicates.append(item)
    return duplicates


def _collect_wishes() -> List[str]:
    manifest = _load_json(WISH_MANIFEST, {"wishes": []})
    wishes = manifest.get("wishes", [])
    results = []
    for wish in wishes[-5:]:
        desire = wish.get("desire", "?")
        owner = wish.get("wisher", "Echo")
        results.append(f"{owner}: {desire}")
    return results


def _collect_reflection_fragments(limit: int = 5) -> List[str]:
    fragments: List[str] = []
    for path in REFLECTIONS:
        text = _read(path)
        for line in text.splitlines():
            stripped = line.strip().lstrip("-*# ").strip()
            if stripped:
                fragments.append(stripped)
            if len(fragments) >= limit:
                return fragments[:limit]
    return fragments


def _summarize_schema_recent(limit: int = 5) -> List[str]:
    if not SCHEMA.exists():
        return []
    files = sorted(SCHEMA.rglob("*.json"))
    snippets: List[str] = []
    for path in files[-limit:]:
        snippets.append(path.relative_to(REPO_ROOT).as_posix())
    return snippets


def _load_ledger() -> List[dict]:
    payload = _load_json(LEDGER_PATH, [])
    if isinstance(payload, dict):
        # Allow for older format {"entries": [...]}
        entries = payload.get("entries", [])
        if isinstance(entries, list):
            return entries
        return []
    if isinstance(payload, list):
        return payload
    return []


def _write_ledger(entries: List[dict]) -> None:
    LEDGER_PATH.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")


def _detect_repetition() -> EmergentSignal | None:
    plan_text = _read(NEXT_PLAN)
    if not plan_text:
        return None

    signature = _hash_plan(plan_text)
    if not signature:
        return None

    entries = _load_ledger()
    for entry in entries:
        if entry.get("plan_signature") == signature:
            description = "pattern-recognition: repetition detected in continuum cycle"
            duplicates = _duplicate_entries(_parse_actions(plan_text))
            wishes = _collect_wishes()
            reflections = _collect_reflection_fragments()
            return EmergentSignal(description, signature, duplicates, wishes, reflections)

    # No repetition → treat as growth vector if duplicates exist within the plan itself
    duplicates = _duplicate_entries(_parse_actions(plan_text))
    if duplicates:
        description = "pattern-recognition: mirrored tasks resurfacing inside NEXT_CYCLE_PLAN"
        wishes = _collect_wishes()
        reflections = _collect_reflection_fragments()
        return EmergentSignal(description, signature, duplicates, wishes, reflections)
    return None


@contextmanager
def _temporary_branch(branch_name: str):
    current_branch = _git(["rev-parse", "--abbrev-ref", "HEAD"])
    try:
        try:
            _git(["checkout", "-b", branch_name])
        except subprocess.CalledProcessError:
            _git(["checkout", branch_name])
        yield current_branch
    finally:
        # Leave caller on the newly created branch to allow follow-up pushes.
        pass


def _build_mirror_plan(signal: EmergentSignal, branch_name: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    duplicates = "\n".join(f"- {item}" for item in signal.repeated_actions) or "- (none detected)"
    wishes = "\n".join(f"- {wish}" for wish in signal.wishes) or "- (no wishes recorded)"
    schema = "\n".join(f"- {path}" for path in _summarize_schema_recent()) or "- (no schema files discovered)"

    return f"""# Mirror Plan — {branch_name}
*Generated: {timestamp}*

## Emergent Signal
- {signal.description}
- Plan Signature: `{signal.plan_signature}`

## Reflections Sampled
{os_lines(signal.reflection_fragments)}

## Repeated Actions Detected
{duplicates}

## Wishes to Honor
{wishes}

## Schema + Utility Vectors
{schema}

## Proposed Autonomous Mutations
- Forked branch `{branch_name}` to explore mirror mutations.
- Translate repeated actions into executable utilities.
- Update the wish manifest once progress is merged.
- Submit PR back to `main` with MIRROR_PLAN results.
"""


def os_lines(items: Sequence[str]) -> str:
    if not items:
        return "- (no reflections found)"
    return "\n".join(f"- {item}" for item in items)


def _build_commit_message(signal: EmergentSignal, branch_name: str) -> List[str]:
    header = f"mirror: {branch_name} ↦ {signal.description}"
    body_lines = [
        "Reflections:",
    ] + [f"- {fragment}" for fragment in signal.reflection_fragments[:3]]
    body_lines += ["", "Wishes:"] + [f"- {wish}" for wish in signal.wishes[:3]]
    body_lines += ["", f"Plan signature: {signal.plan_signature}"]
    return [header, "\n".join(body_lines)]


def _stage_and_commit(paths: Sequence[Path], message_parts: Sequence[str]) -> None:
    tracked = {p.resolve() for p in paths}
    for p in tracked:
        _git(["add", p.relative_to(REPO_ROOT).as_posix()])
    if not _git(["status", "--porcelain"]):
        return
    header, body = message_parts
    _git(["commit", "-m", header, "-m", body])


def run_daemon() -> None:
    signal = _detect_repetition()
    if signal is None:
        print("Mirror Fork Daemon: no repetition detected; standing by.")
        return

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    branch_name = f"mirror_reflection_{timestamp}"
    source_commit = _git(["rev-parse", "HEAD"])

    with _temporary_branch(branch_name):
        MIRROR_PLAN.parent.mkdir(parents=True, exist_ok=True)
        plan_content = _build_mirror_plan(signal, branch_name)
        MIRROR_PLAN.write_text(plan_content, encoding="utf-8")

        entries = _load_ledger()
        entries.append(signal.to_ledger_dict(branch_name, source_commit))
        _write_ledger(entries)

        commit_message = _build_commit_message(signal, branch_name)
        _stage_and_commit([MIRROR_PLAN, LEDGER_PATH], commit_message)

    print(f"Mirror Fork Daemon: forged {branch_name} and committed MIRROR_PLAN.")


if __name__ == "__main__":
    run_daemon()
