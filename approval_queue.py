#!/usr/bin/env python3
"""Manage a local approval queue for automation-assisted pull requests."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

QUEUE = Path("approval_queue.jsonl")
AUDIT = Path("approval_audit.jsonl")
SECRET_KEY_PATH = Path.home() / ".echo_audit_key"


@dataclass
class QueueItem:
    repo: str
    pr: int
    title: str
    actor: str
    metadata: dict

    @classmethod
    def from_dict(cls, payload: dict) -> "QueueItem":
        return cls(
            repo=str(payload.get("repo", "")),
            pr=int(payload.get("pr", 0)),
            title=str(payload.get("title", "")),
            actor=str(payload.get("actor", "")),
            metadata={k: v for k, v in payload.items() if k not in {"repo", "pr", "title", "actor"}},
        )

    def to_json(self) -> str:
        base = {"repo": self.repo, "pr": self.pr, "title": self.title, "actor": self.actor}
        base.update(self.metadata)
        return json.dumps(base, sort_keys=True)


@dataclass
class AuditRecord:
    payload: dict
    sig: str

    def to_json(self) -> str:
        return json.dumps({"payload": self.payload, "sig": self.sig}, sort_keys=True)


def ensure_secret_key() -> bytes:
    if SECRET_KEY_PATH.exists():
        key = SECRET_KEY_PATH.read_text(encoding="utf-8").strip()
        if key:
            return key.encode()
    else:
        SECRET_KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(key + "\n", encoding="utf-8")
    try:
        os.chmod(SECRET_KEY_PATH, 0o600)
    except OSError:
        pass
    return key.encode()


def read_queue() -> List[QueueItem]:
    if not QUEUE.exists():
        return []
    items: List[QueueItem] = []
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            items.append(QueueItem.from_dict(payload))
        except json.JSONDecodeError:
            continue
    return items


def write_queue(items: Iterable[QueueItem]) -> None:
    lines = [item.to_json() for item in items]
    tmp = QUEUE.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    tmp.replace(QUEUE)


def append_queue(item: QueueItem) -> None:
    items = read_queue()
    items.append(item)
    write_queue(items)


def list_queue() -> List[QueueItem]:
    items = read_queue()
    if not items:
        print("[OK] no pending items")
        return []
    for idx, item in enumerate(items, start=1):
        title = item.title.strip()
        if len(title) > 80:
            title = f"{title[:77]}..."
        print(f"{idx:3d}. {item.repo}#PR{item.pr} — {title} (by {item.actor})")
    return items


def append_audit(item: QueueItem, approver: str) -> None:
    key = ensure_secret_key()
    payload = {
        "action": "approve",
        "item": json.loads(item.to_json()),
        "approver": approver,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    import hmac
    import hashlib

    signature = hmac.new(key, json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    record = AuditRecord(payload=payload, sig=signature)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(record.to_json() + "\n")


def approve_index(index: int, approver: Optional[str]) -> None:
    items = read_queue()
    if index < 1 or index > len(items):
        print("[ERR] invalid index")
        return
    item = items.pop(index - 1)
    write_queue(items)
    append_audit(item, approver or getpass.getuser())
    print(f"[OK] approved {item.repo}#PR{item.pr} — signed to {AUDIT}")


def enqueue_from_json(data: str) -> None:
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        print(f"[ERR] invalid JSON payload: {exc}")
        return
    item = QueueItem.from_dict(payload)
    if not item.repo or not item.pr:
        print("[ERR] payload must include repo and pr")
        return
    append_queue(item)
    print(f"[OK] queued {item.repo}#PR{item.pr}")


def parse_args(argv: Optional[Iterable[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=False)

    sub.add_parser("list", help="Show pending approvals")

    approve_parser = sub.add_parser("approve", help="Approve an item by index")
    approve_parser.add_argument("index", nargs="?", type=int, help="Queue index to approve (1-based)")
    approve_parser.add_argument("--approver", help="Override approver name (defaults to current user)")

    enqueue_parser = sub.add_parser("enqueue", help="Append a JSON payload from stdin or argument")
    enqueue_parser.add_argument("payload", nargs="?", help="JSON object representing a queue item")

    parser.add_argument("--version", action="version", version="approval-queue 1.0")
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    command = args.command or "list"

    if command == "list":
        list_queue()
        return 0

    if command == "approve":
        if args.index is None:
            items = list_queue()
            if not items:
                return 0
            try:
                index = int(input("Approve which index? ").strip())
            except ValueError:
                print("[ERR] invalid input")
                return 1
        else:
            index = args.index
        approve_index(index, getattr(args, "approver", None))
        return 0

    if command == "enqueue":
        payload = args.payload
        if payload is None:
            payload = sys.stdin.read()
        enqueue_from_json(payload)
        return 0

    print("Usage: approval_queue.py [list|approve|enqueue]")
    return 1


if __name__ == "__main__":
    sys.exit(main())
