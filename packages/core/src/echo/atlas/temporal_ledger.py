"""Temporal ledger that records append-only events with hash attestations."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping, Optional

from pydantic import BaseModel, Field

__all__ = [
    "LedgerEntry",
    "LedgerEntryInput",
    "TemporalLedger",
    "render_markdown",
    "render_dot",
    "render_svg",
]


class LedgerEntryInput(BaseModel):
    actor: str
    action: str
    ref: str
    proof_id: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class LedgerEntry:
    id: str
    ts: datetime
    actor: str
    action: str
    ref: str
    proof_id: str
    hash: str

    def to_dict(self) -> Mapping[str, str]:
        return {
            "id": self.id,
            "ts": self.ts.isoformat(),
            "actor": self.actor,
            "action": self.action,
            "ref": self.ref,
            "proof_id": self.proof_id,
            "hash": self.hash,
        }


class TemporalLedger:
    """Append-only ledger backed by a JSON lines file."""

    def __init__(self, *, state_dir: Path | str = Path("state")) -> None:
        self._state_dir = Path(state_dir)
        self._ledger_path = self._state_dir / "temporal_ledger.jsonl"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._ledger_path.touch(exist_ok=True)

    def append(self, entry: LedgerEntryInput) -> LedgerEntry:
        payload = entry.model_dump()
        entry_id = str(uuid.uuid4())
        payload["id"] = entry_id
        payload["ts"] = entry.ts.isoformat()
        payload_hash = _hash_entry(payload)
        payload["hash"] = payload_hash
        with self._ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")
        return LedgerEntry(
            id=entry_id,
            ts=entry.ts,
            actor=entry.actor,
            action=entry.action,
            ref=entry.ref,
            proof_id=entry.proof_id,
            hash=payload_hash,
        )

    def entries(self) -> List[LedgerEntry]:
        return list(self.iter_entries())

    def iter_entries(
        self,
        *,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> Iterator[LedgerEntry]:
        count = 0
        for raw in self._ledger_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            data = json.loads(raw)
            ts = datetime.fromisoformat(data["ts"])
            if since and ts <= since:
                continue
            entry = LedgerEntry(
                id=str(data["id"]),
                ts=ts,
                actor=str(data["actor"]),
                action=str(data["action"]),
                ref=str(data["ref"]),
                proof_id=str(data["proof_id"]),
                hash=str(data["hash"]),
            )
            yield entry
            count += 1
            if limit is not None and count >= limit:
                break

    def as_markdown(self, *, since: datetime | None = None, limit: int | None = None) -> str:
        return render_markdown(self.iter_entries(since=since, limit=limit))

    def as_svg(self, *, since: datetime | None = None, limit: int | None = None) -> str:
        return render_svg(self.iter_entries(since=since, limit=limit))

    def as_dot(self, *, since: datetime | None = None, limit: int | None = None) -> str:
        return render_dot(self.iter_entries(since=since, limit=limit))


def _hash_entry(payload: Mapping[str, str]) -> str:
    without_hash = {k: v for k, v in payload.items() if k != "hash"}
    canonical = json.dumps(without_hash, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def render_markdown(entries: Iterable[LedgerEntry]) -> str:
    lines = ["# Temporal Ledger Snapshot", ""]
    for entry in entries:
        lines.extend(
            [
                f"- **{entry.ts.isoformat()}** — {entry.actor} {entry.action} ({entry.ref})",
                f"  - proof: ``{entry.proof_id}``",
                f"  - hash: ``{entry.hash}``",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def render_dot(entries: Iterable[LedgerEntry]) -> str:
    nodes: List[str] = []
    edges: List[str] = []
    last_node: Optional[str] = None
    for index, entry in enumerate(entries):
        node_name = f"n{index}"
        label = f"{entry.ts.isoformat()}\n{entry.actor}\n{entry.action}"
        nodes.append(f'  {node_name} [shape=box, label="{label}"];')
        if last_node is not None:
            edges.append(f"  {last_node} -> {node_name};")
        last_node = node_name
    body = "\n".join(nodes + edges)
    return "digraph TemporalLedger {\n  rankdir=LR;\n" + body + "\n}\n"


def render_svg(entries: Iterable[LedgerEntry]) -> str:
    entries_list = list(entries)
    width = 220 * max(1, len(entries_list))
    height = 120
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "  <style>text{font-family:monospace;font-size:12px;} .ts{font-weight:bold;}</style>",
    ]
    for idx, entry in enumerate(entries_list):
        x = 20 + idx * 200
        parts.append("  <g>")
        parts.append(f"    <text class='ts' x='{x}' y='30'>{entry.ts.isoformat()}</text>")
        parts.append(f"    <text x='{x}' y='50'>{entry.actor}</text>")
        parts.append(f"    <text x='{x}' y='70'>{entry.action}</text>")
        parts.append(f"    <text x='{x}' y='90'>proof: {entry.proof_id}</text>")
        parts.append("  </g>")
        if idx:
            prev_x = 20 + (idx - 1) * 200
            parts.append(
                f"  <line x1='{prev_x + 80}' y1='40' x2='{x}' y2='40' stroke='black' stroke-width='2' />"
            )
    parts.append("</svg>")
    return "\n".join(parts)
