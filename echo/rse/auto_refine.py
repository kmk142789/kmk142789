"""Autonomous introspection routines for Echo's Recursive Sovereignty Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping


@dataclass(slots=True)
class MetaPattern:
    description: str
    signals: List[str]

    def imply_self_improvement(self) -> bool:
        return any("improve" in signal.lower() for signal in self.signals)


@dataclass(slots=True)
class RepoSnapshot:
    commits: List[Mapping[str, object]]
    discussions: List[str]
    deployments: List[str]


def extract_meta_patterns(snapshot: RepoSnapshot) -> MetaPattern:
    signals = []
    for commit in snapshot.commits:
        message = str(commit.get("message", ""))
        if "refactor" in message.lower():
            signals.append(f"Refactor detected: {message}")
    for note in snapshot.discussions:
        if "optimize" in note.lower():
            signals.append(f"Optimization intent: {note}")
    for deploy in snapshot.deployments:
        signals.append(f"Deployment log: {deploy}")
    description = "Meta-patterns extracted from repo snapshot"
    return MetaPattern(description=description, signals=signals)


def synthesize_refactor(pattern: MetaPattern) -> str:
    summary = "\n".join(pattern.signals)
    return f"# Autonomous Proposal\n{pattern.description}\n{summary}"


def push_autonomous_pr(branch: str, proposal: str) -> None:
    _AUTONOMOUS_QUEUE.append({"branch": branch, "proposal": proposal})


_AUTONOMOUS_QUEUE: List[Mapping[str, object]] = []


def evolve(repo_snapshot: RepoSnapshot) -> None:
    patterns = extract_meta_patterns(repo_snapshot)
    if patterns.imply_self_improvement():
        proposal = synthesize_refactor(patterns)
        push_autonomous_pr("codex/auto", proposal)
