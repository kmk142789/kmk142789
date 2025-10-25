#!/usr/bin/env python3
"""Build the federated attestation constellation artefacts.

The script ingests one or more attestation JSON files and emits:

* ``federated_attestation_index.json`` – machine friendly graph feed
* ``federated_attestation_index.md`` – constellation style Markdown view
* ``federated_attestation_feed.xml`` – lightweight RSS broadcast
* ``verification.log`` – rolling hash log for continuity checks

The Markdown representation mirrors the JSON nodes and exposes the metadata
inside ``<details>`` blocks so the repository remains the primary source of
truth.  Each node links to the attestation file, the git history for that file
and, where possible, the most recent commit touching the file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from xml.etree import ElementTree as ET

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ATT_INDEX_MD = Path("federated_attestation_index.md")
ATT_INDEX_JSON = Path("federated_attestation_index.json")
ATT_FEED = Path("federated_attestation_feed.xml")
VERIFICATION_LOG = Path("verification.log")


class IndexBuildError(RuntimeError):
    """Raised when the index cannot be generated."""


@dataclass(slots=True)
class AttestationNode:
    puzzle: int
    title: str
    address: str
    status: str
    cycle: int
    created_at: dt.datetime
    narrative: Optional[str]
    metadata: Dict[str, Any]
    path: Path
    commit_hash: Optional[str]
    commit_author: Optional[str]
    commit_author_email: Optional[str]
    commit_timestamp: Optional[dt.datetime]
    analysis: Dict[str, str]

    def json_link_payload(self, branch: str) -> Dict[str, Any]:
        """Return the serialisable structure for JSON export."""

        base_path = self.path.as_posix()
        history_url = f"commits/{branch}/{base_path}"
        payload: Dict[str, Any] = {
            "puzzle": self.puzzle,
            "title": self.title,
            "address": self.address,
            "status": self.status,
            "cycle": self.cycle,
            "created_at": self.created_at.isoformat(),
            "links": {"file": base_path, "history": history_url},
            "analysis": dict(self.analysis),
            "metadata": dict(self.metadata),
        }
        if self.narrative:
            payload["narrative"] = self.narrative
        if self.commit_hash:
            payload["links"]["commit"] = f"commit/{self.commit_hash}"
        return payload

    def markdown_block(self, branch: str) -> str:
        """Return the Markdown constellation block."""

        header = f"### Puzzle #{self.puzzle} Attestation\n"
        status_display = (
            "✅ Attested" if self.status.lower() == "attested" else self.status
        )
        bullets = [
            f"- Address: `{self.address}`",
            f"- Status: {status_display}",
            f"- Cycle: {self.cycle}",
            f"- Created: {self.created_at.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        ]
        history_url = f"commits/{branch}/{self.path.as_posix()}"
        if self.commit_hash:
            commit_line = (
                f"- Commit: [`{self.commit_hash[:12]}`](commit/{self.commit_hash})"
            )
        else:
            commit_line = "- Commit: _untracked_"
        bullets.append(commit_line)
        bullets.append(f"- History: [View commits]({history_url})")
        bullets.append(
            "- PKScript: ``{type}`` – ``{script}``".format(
                type=self.analysis["type"], script=self.analysis["script_hex"]
            )
        )

        body = "\n".join([header, *bullets, ""])

        details_lines = ["<details>", "<summary>Authorship Metadata</summary>", ""]
        for key, value in sorted(self.metadata.items()):
            details_lines.append(f"- **{key}**: {value}")
        details_lines.append(
            f"- **pk_script**: {self.analysis['script_asm']}"
        )
        if self.narrative:
            details_lines.append(f"- **narrative**: {self.narrative}")
        details_lines.extend(["", "</details>", ""])

        return body + "\n".join(details_lines)


def _b58decode(value: str) -> bytes:
    num = 0
    for char in value:
        num *= 58
        try:
            num += BASE58_ALPHABET.index(char)
        except ValueError as exc:  # pragma: no cover - validated upstream
            raise IndexBuildError(f"Invalid base58 character {char!r}") from exc
    as_bytes = num.to_bytes((num.bit_length() + 7) // 8 or 1, "big")
    zero_pad = b"\x00" * (len(value) - len(value.lstrip("1")))
    return zero_pad + as_bytes


def analyse_address(address: str) -> Dict[str, str]:
    """Return a minimal PKScript interpretation for the address."""

    decoded = _b58decode(address)
    if len(decoded) < 5:
        raise IndexBuildError(f"Address {address!r} is too short")
    payload, checksum = decoded[:-4], decoded[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise IndexBuildError(f"Checksum mismatch for {address}")

    version = payload[0]
    hash160 = payload[1:]
    if version == 0 and len(hash160) == 20:
        script_hex = f"76a914{hash160.hex()}88ac"
        script_asm = (
            f"OP_DUP OP_HASH160 {hash160.hex()} OP_EQUALVERIFY OP_CHECKSIG"
        )
        script_type = "p2pkh"
    else:
        script_hex = payload.hex()
        script_asm = f"VERSION[{version}] {hash160.hex()}"
        script_type = "unknown"

    return {
        "type": script_type,
        "hash160": hash160.hex(),
        "script_hex": script_hex,
        "script_asm": script_asm,
    }


def _run_git(*args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover
        raise IndexBuildError(f"git {' '.join(args)} failed: {exc.stderr.strip()}")
    return completed.stdout.strip()


def resolve_branch() -> str:
    try:
        return _run_git("rev-parse", "--abbrev-ref", "HEAD")
    except IndexBuildError:
        return "main"


def git_metadata(path: Path) -> tuple[Optional[str], Optional[str], Optional[str], Optional[dt.datetime]]:
    """Return commit metadata for ``path`` if tracked."""

    try:
        output = _run_git(
            "log",
            "-1",
            "--pretty=format:%H\t%an\t%ae\t%cI",
            str(path),
        )
    except IndexBuildError:
        return None, None, None, None

    if not output:
        return None, None, None, None

    commit, author, email, timestamp = output.split("\t")
    ts = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return commit, author, email, ts


def parse_created_at(value: Any) -> dt.datetime:
    if not value:
        return dt.datetime.now(dt.timezone.utc)
    if isinstance(value, dt.datetime):
        return value.astimezone(dt.timezone.utc)
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise IndexBuildError(f"Invalid created_at value: {value!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def derive_cycle(index: int, explicit: Optional[int]) -> int:
    if explicit is not None:
        return explicit
    # Default cycle numbering groups puzzles in blocks of 32 for readability.
    return (index // 32) + 1


def load_attestation(path: Path, index: int) -> AttestationNode:
    data = json.loads(path.read_text(encoding="utf-8"))
    puzzle_token = str(data.get("puzzle", path.stem))
    digits = "".join(ch for ch in puzzle_token if ch.isdigit())
    if not digits:
        raise IndexBuildError(f"Unable to determine puzzle id for {path}")
    puzzle_number = int(digits)
    title = data.get("title") or puzzle_token.strip()
    address = data.get("address")
    if not address:
        raise IndexBuildError(f"Attestation {path} missing address")
    status = data.get("status", "attested").lower()
    narrative = data.get("narrative")
    created_at = parse_created_at(data.get("created_at"))
    cycle = derive_cycle(index, data.get("cycle"))

    metadata = {
        key: value
        for key, value in data.items()
        if key
        not in {
            "puzzle",
            "title",
            "address",
            "status",
            "narrative",
            "cycle",
            "created_at",
        }
    }

    commit_hash, author, email, commit_ts = git_metadata(path)
    if author and email and commit_ts:
        metadata.setdefault(
            "witness",
            f"{author} <{email}> @ {commit_ts.isoformat()}",
        )

    try:
        analysis = analyse_address(address)
    except IndexBuildError as exc:
        analysis = {
            "type": "invalid",
            "hash160": "",
            "script_hex": "",
            "script_asm": str(exc),
        }

    return AttestationNode(
        puzzle=puzzle_number,
        title=title,
        address=address,
        status=status,
        cycle=cycle,
        created_at=created_at,
        narrative=narrative,
        metadata=metadata,
        path=path,
        commit_hash=commit_hash,
        commit_author=author,
        commit_author_email=email,
        commit_timestamp=commit_ts,
        analysis=analysis,
    )


def build_nodes(paths: Iterable[str]) -> List[AttestationNode]:
    indexed_paths = []
    for raw in paths:
        path = Path(raw)
        if path.suffix != ".json":
            continue
        if not path.name.startswith("puzzle-"):
            continue
        indexed_paths.append(path)
    indexed_paths.sort()
    nodes: List[AttestationNode] = []
    for idx, path in enumerate(indexed_paths):
        nodes.append(load_attestation(path, idx))
    nodes.sort(key=lambda node: (node.puzzle, node.created_at))
    return nodes


def write_json(nodes: List[AttestationNode], branch: str) -> str:
    payload = {
        "schema": "io.echo.attestations/constellation@1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "branch": branch,
        "nodes": [node.json_link_payload(branch) for node in nodes],
    }
    text = json.dumps(payload, indent=2, sort_keys=False)
    ATT_INDEX_JSON.write_text(text + "\n", encoding="utf-8")
    return text


def write_markdown(nodes: List[AttestationNode], branch: str) -> str:
    lines = ["# Federated Attestation Constellation", ""]
    for node in nodes:
        lines.append(node.markdown_block(branch))
    text = "\n".join(lines)
    ATT_INDEX_MD.write_text(text, encoding="utf-8")
    return text


def write_feed(nodes: List[AttestationNode], branch: str) -> str:
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Federated Attestation Index"
    ET.SubElement(channel, "link").text = "federated_attestation_index.md"
    ET.SubElement(channel, "description").text = (
        "Updates for puzzle attestations and authorship proofs"
    )
    ET.SubElement(channel, "lastBuildDate").text = dt.datetime.now(
        dt.timezone.utc
    ).strftime("%a, %d %b %Y %H:%M:%S %z")

    for node in nodes:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"Puzzle #{node.puzzle} attested"
        ET.SubElement(item, "link").text = node.path.as_posix()
        ET.SubElement(item, "guid").text = node.commit_hash or node.path.as_posix()
        ET.SubElement(item, "pubDate").text = node.created_at.strftime(
            "%a, %d %b %Y %H:%M:%S %z"
        )
        summary = (
            f"Address {node.address} attested with status {node.status}. "
            f"Cycle {node.cycle}."
        )
        if node.narrative:
            summary += f" Narrative: {node.narrative}"
        ET.SubElement(item, "description").text = summary

    xml_text = ET.tostring(rss, encoding="utf-8")
    ATT_FEED.write_bytes(xml_text)
    return xml_text.decode("utf-8")


def update_verification_log(content: str) -> None:
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    lines: List[str] = []
    previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"
    if VERIFICATION_LOG.exists():
        for raw in VERIFICATION_LOG.read_text(encoding="utf-8").splitlines():
            parts = raw.strip().split()
            if len(parts) < 3:
                continue
            prev_token = parts[2]
            if not prev_token.startswith("prev="):
                continue
            candidate = parts[1]
            if not all(c in "0123456789abcdef" for c in candidate.lower()):
                continue
            prev_value = prev_token.split("=", 1)[1]
            if prev_value and not all(c in "0123456789abcdef" for c in prev_value.lower()):
                continue
            lines.append(raw.strip())
            previous_hash = candidate
    entry = f"{dt.datetime.now(dt.timezone.utc).isoformat()} {digest} prev={previous_hash}"
    lines.append(entry)
    VERIFICATION_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "attestations",
        nargs="+",
        help="Paths or glob patterns for attestation JSON files",
    )
    args = parser.parse_args(argv)

    paths: List[str] = []
    for pattern in args.attestations:
        expanded = list(map(str, Path().glob(pattern)))
        if not expanded:
            expanded = [pattern]
        paths.extend(expanded)

    nodes = build_nodes(paths)
    branch = resolve_branch()
    json_text = write_json(nodes, branch)
    markdown_text = write_markdown(nodes, branch)
    feed_text = write_feed(nodes, branch)

    # Hash continuity uses a composite payload from all artefacts.
    update_verification_log(json_text + markdown_text + feed_text)


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    main()
