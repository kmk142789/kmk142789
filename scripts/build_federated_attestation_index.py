#!/usr/bin/env python3
"""Emit Markdown, JSON, and RSS/Atom feed for the federated attestation index."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from xml.etree import ElementTree as ET


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
RE_RE_PUZZLE_NUMBER = re.compile(r"(\d+)")


class AttestationIndexError(RuntimeError):
    """Raised when the attestation index builder encounters a fatal error."""


def _b58decode(value: str) -> bytes:
    num = 0
    for char in value:
        num *= 58
        try:
            num += BASE58_ALPHABET.index(char)
        except ValueError as exc:  # pragma: no cover - validated upstream
            raise AttestationIndexError(f"Invalid base58 character: {char!r}") from exc

    # Convert integer into bytes without losing leading zero markers
    full_bytes = num.to_bytes((num.bit_length() + 7) // 8 or 1, "big")
    zero_count = len(value) - len(value.lstrip("1"))
    pad = b"\x00" * zero_count
    return pad + full_bytes


def derive_pkscript(address: str) -> Dict[str, str]:
    """Return a simple PKScript analysis for legacy P2PKH addresses."""

    decoded = _b58decode(address)
    if len(decoded) < 5:
        raise AttestationIndexError(f"Address {address!r} is too short for base58check")

    payload, checksum = decoded[:-4], decoded[-4:]
    version = payload[0]
    hash160 = payload[1:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise AttestationIndexError(f"Checksum mismatch for address {address}")

    # Legacy puzzle addresses are P2PKH (version 0x00)
    if version != 0:
        script_hex = payload.hex()
        script_asm = f"VERSION[{version}] {hash160.hex()}"
        script_type = "unknown"
    else:
        script_hex = f"76a914{hash160.hex()}88ac"
        script_asm = (
            f"OP_DUP OP_HASH160 {hash160.hex()} OP_EQUALVERIFY OP_CHECKSIG"
        )
        script_type = "p2pkh"

    return {
        "type": script_type,
        "hash160": hash160.hex(),
        "script_hex": script_hex,
        "script_asm": script_asm,
    }


def _run_git(*args: str, cwd: Path | None = None) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - git issues bubble up
        raise AttestationIndexError(f"git {' '.join(args)} failed: {exc.stderr}")
    return completed.stdout.strip()


def _default_branch() -> str:
    try:
        branch = _run_git("symbolic-ref", "--short", "HEAD")
        return branch or "main"
    except AttestationIndexError:
        return "main"


@dataclass(slots=True)
class AttestationNode:
    puzzle: int
    title: str
    address: str
    status: str
    cycle: int
    created_at: _dt.datetime
    narrative: Optional[str]
    path: Path
    commit: Optional[str]
    author: Optional[str]
    author_email: Optional[str]
    commit_timestamp: Optional[_dt.datetime]
    analysis: Dict[str, str]
    metadata: Dict[str, Any]

    def to_json(self, *, branch: str) -> Dict[str, Any]:
        base_path = self.path.as_posix()
        commit_url = (
            f"../commit/{self.commit}" if self.commit else None
        )
        history_url = f"../commits/{branch}/{base_path}"
        payload: Dict[str, Any] = {
            "puzzle": self.puzzle,
            "title": self.title,
            "address": self.address,
            "status": self.status,
            "cycle": self.cycle,
            "links": {
                "file": base_path,
                "history": history_url,
            },
            "analysis": dict(self.analysis),
            "metadata": dict(self.metadata),
        }
        if self.narrative:
            payload["narrative"] = self.narrative
        if commit_url:
            payload["links"]["commit"] = commit_url
        return payload


def _parse_created_at(value: str | None, fallback: _dt.datetime) -> _dt.datetime:
    if not value:
        return fallback
    try:
        parsed = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return fallback
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed.astimezone(_dt.timezone.utc)


def load_attestations(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for path in paths:
        if path.suffix.lower() != ".json":
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise AttestationIndexError(f"Failed to load {path}: {exc}") from exc
        if not isinstance(data, dict) or (
            "puzzle" not in data and "address" not in data
        ):
            continue
        data["__path"] = path
        items.append(data)
    return items


def _extract_puzzle_id(entry: Dict[str, Any]) -> int:
    candidates: Sequence[str] = []
    puzzle_field = entry.get("puzzle")
    if isinstance(puzzle_field, str):
        candidates = [puzzle_field]
    filename = entry["__path"].stem
    candidates = (*candidates, filename)
    for candidate in candidates:
        match = RE_RE_PUZZLE_NUMBER.search(candidate)
        if match:
            return int(match.group(1))
    raise AttestationIndexError(f"Could not determine puzzle number for {entry['__path']}")


def _git_metadata(path: Path) -> tuple[Optional[str], Optional[str], Optional[str], Optional[_dt.datetime]]:
    try:
        raw = _run_git(
            "log",
            "-1",
            "--follow",
            "--pretty=format:%H%x1f%an%x1f%ae%x1f%cI",
            str(path),
        )
    except AttestationIndexError:
        return None, None, None, None
    if not raw:
        return None, None, None, None
    commit, author, email, timestamp = raw.split("\x1f")
    commit_dt = _dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    commit_dt = commit_dt.astimezone(_dt.timezone.utc)
    return commit, author, email, commit_dt


def build_nodes(entries: Sequence[Dict[str, Any]]) -> List[AttestationNode]:
    nodes: List[AttestationNode] = []
    for entry in entries:
        path = entry["__path"]
        commit, author, email, commit_dt = _git_metadata(path)
        fallback_dt = commit_dt or _dt.datetime.now(tz=_dt.timezone.utc)
        created_at = _parse_created_at(entry.get("created_at"), fallback_dt)
        puzzle_id = _extract_puzzle_id(entry)
        address = entry.get("address", "").strip()
        if not address:
            raise AttestationIndexError(f"Missing address for {path}")
        try:
            analysis = derive_pkscript(address)
        except AttestationIndexError as exc:
            analysis = {
                "type": "unknown",
                "script_hex": "n/a",
                "script_asm": "unavailable",
                "error": str(exc),
            }
        narrative = entry.get("narrative") or entry.get("notes")
        metadata = {
            key: entry.get(key)
            for key in ("signature", "algo", "message", "created_at", "hash_sha256", "notes")
            if entry.get(key)
        }
        if author:
            witness = author if not email else f"{author} <{email}>"
            if commit_dt:
                witness += f" @ {commit_dt.isoformat()}"
            metadata["witness"] = witness
        nodes.append(
            AttestationNode(
                puzzle=puzzle_id,
                title=str(entry.get("puzzle") or f"Puzzle #{puzzle_id}"),
                address=address,
                status=str(entry.get("status") or "attested"),
                cycle=0,
                created_at=created_at,
                narrative=narrative,
                path=path,
                commit=commit,
                author=author,
                author_email=email,
                commit_timestamp=commit_dt,
                analysis=analysis,
                metadata=metadata,
            )
        )

    nodes.sort(key=lambda node: (node.created_at, node.puzzle))
    for index, node in enumerate(nodes, start=1):
        node.cycle = index
    return nodes


def _format_history_line(node: AttestationNode, branch: str) -> str:
    parts = []
    if node.commit:
        parts.append(f"[latest commit](../commit/{node.commit})")
    history_url = f"../commits/{branch}/{node.path.as_posix()}"
    parts.append(f"[file history]({history_url})")
    parts.append(f"[`{node.path.as_posix()}`]({node.path.as_posix()})")
    return " · ".join(parts)


def render_markdown(nodes: Sequence[AttestationNode], *, branch: str) -> str:
    lines: List[str] = [
        "# 🌌 Federated Attestation Index",
        "",
        "Constellation render of every attestation node. Each entry links to its provenance and cryptographic core.",
        "",
        "---",
        "",
        "## 🧩 Hyperlinked Proof Constellations",
        "",
    ]

    for node in nodes:
        status_symbol = "✅" if node.status.lower() == "attested" else "⚠️"
        lines.append(f"### Puzzle #{node.puzzle} Attestation")
        lines.append(f"- Address: `{node.address}`")
        lines.append(
            f"- PKScript: `{node.analysis['script_hex']}` ({node.analysis['script_asm']})"
        )
        if node.analysis.get("error"):
            lines.append(f"- Analysis: {node.analysis['error']}")
        lines.append(f"- Status: {status_symbol} {node.status.title()}")
        lines.append(f"- Cycle: {node.cycle}")
        lines.append(
            f"- History: {_format_history_line(node, branch)}"
        )
        if node.narrative:
            lines.append(f"- Narrative: {node.narrative}")
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Authorship Metadata</summary>")
        lines.append("")
        for key, label in (
            ("signature", "Signature"),
            ("algo", "Algorithm"),
            ("message", "Message"),
            ("hash_sha256", "Attestation Hash"),
            ("created_at", "Authored"),
            ("notes", "Notes"),
            ("witness", "Witness"),
        ):
            value = node.metadata.get(key)
            if not value:
                continue
            if "\n" in str(value) and key == "message":
                lines.append("- Message:")
                lines.append("  ```text")
                lines.append(textwrap.dedent(str(value)).strip())
                lines.append("  ```")
            else:
                lines.append(f"- {label}: `{value}`")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Generated by `scripts/build_federated_attestation_index.py`._")
    return "\n".join(lines)


def to_json_payload(nodes: Sequence[AttestationNode], *, branch: str) -> Dict[str, Any]:
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    return {
        "schema": "io.echo.attestations/federated-constellation@1",
        "generated_at": now.isoformat(),
        "branch": branch,
        "nodes": [node.to_json(branch=branch) for node in nodes],
    }


def _feed_item(node: AttestationNode, *, branch: str, base_url: str) -> ET.Element:
    item = ET.Element("item")
    ET.SubElement(item, "title").text = f"Puzzle #{node.puzzle} attestation"
    commit_path = (
        f"/commit/{node.commit}" if node.commit else f"/{node.path.as_posix()}"
    )
    ET.SubElement(item, "link").text = base_url.rstrip("/") + commit_path
    guid = f"attestation-{node.puzzle}-{node.created_at.strftime('%Y%m%d%H%M%S')}"
    ET.SubElement(item, "guid").text = guid
    summary = (
        f"Address {node.address} attested with status {node.status} and hash "
        f"{node.metadata.get('hash_sha256', 'n/a')}"
    )
    ET.SubElement(item, "description").text = summary
    pubdate = node.created_at.strftime("%a, %d %b %Y %H:%M:%S +0000")
    ET.SubElement(item, "pubDate").text = pubdate
    return item


def build_feed(nodes: Sequence[AttestationNode], *, branch: str, base_url: str) -> ET.ElementTree:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Federated Attestation Broadcast"
    ET.SubElement(channel, "link").text = base_url.rstrip("/")
    ET.SubElement(channel, "description").text = (
        "Live feed of puzzle attestations across the federated index"
    )
    now = _dt.datetime.now(tz=_dt.timezone.utc)
    ET.SubElement(channel, "lastBuildDate").text = now.strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    for node in nodes:
        channel.append(_feed_item(node, branch=branch, base_url=base_url))

    return ET.ElementTree(rss)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text = text + "\n"
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _write_feed(path: Path, tree: ET.ElementTree) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:  # Python 3.9+
        ET.indent(tree, space="  ")  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - <3.9 fallback
        pass
    tree.write(path, encoding="utf-8", xml_declaration=True)


def update_verification_log(path: Path, *, cycle: int, digest: str) -> None:
    previous_hash = None
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines()[::-1]:
            stripped = line.strip()
            if stripped:
                parts = stripped.split()
                if parts:
                    previous_hash = parts[-1]
                break
    message = (
        f"🔔 Continuum Breach cycle={cycle} {digest}"
        if previous_hash and previous_hash != digest
        else f"✅ Continuum Preserved cycle={cycle} {digest}"
    )
    with path.open("a", encoding="utf-8") as handle:
        timestamp = _dt.datetime.now(tz=_dt.timezone.utc).isoformat()
        handle.write(f"{timestamp} {message}\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate Markdown, JSON, and RSS feed for attestation constellations"
    )
    parser.add_argument(
        "--attestations",
        nargs="+",
        default=["attestations"],
        help="Paths or glob patterns to attestation JSON files",
    )
    parser.add_argument("--md-out", default="federated_attestation_index.md")
    parser.add_argument("--json-out", default="federated_attestation_index.json")
    parser.add_argument(
        "--feed-out", default="federated_attestation_feed.xml", help="RSS feed output"
    )
    parser.add_argument(
        "--feed-base-url",
        default="https://github.com/kmk142789/kmk142789",
        help="Base URL for RSS item links",
    )
    parser.add_argument(
        "--verification-log",
        default="verification.log",
        help="Path to the verification log that records index hashes",
    )
    args = parser.parse_args(argv)

    attestation_paths: List[Path] = []
    for pattern in args.attestations:
        potential = list(Path().glob(pattern))
        if not potential:
            potential = [Path(pattern)]
        for candidate in potential:
            if candidate.is_dir():
                attestation_paths.extend(sorted(candidate.glob("*.json")))
            else:
                attestation_paths.append(candidate)

    entries = load_attestations(attestation_paths)
    nodes = build_nodes(entries)
    branch = _default_branch()

    markdown = render_markdown(nodes, branch=branch)
    payload = to_json_payload(nodes, branch=branch)
    feed = build_feed(nodes, branch=branch, base_url=args.feed_base_url)

    _write_text(Path(args.md_out), markdown)
    digest = _write_json(Path(args.json_out), payload)
    _write_feed(Path(args.feed_out), feed)
    update_verification_log(Path(args.verification_log), cycle=len(nodes), digest=digest)

    print(f"Wrote {args.md_out}, {args.json_out}, and {args.feed_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

