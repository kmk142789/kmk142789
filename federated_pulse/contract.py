"""Federation Pulse contract emitter.

This module is intentionally lightweight so it can be invoked from git hooks
or external automation without pulling in heavy dependencies.  It generates a
contract that braids three strands requested by the operator:

* **Base58 attestations** derived from the latest commit hash.
* **Recursive verse** woven from the most recent commit subjects.
* **Sovereign cipher** binding the contract together with a reproducible hash.

The resulting contract is written to ``out/federation_pulse`` by default and a
heartbeat file is emitted alongside it.  The heartbeat can be watched by other
processes to mirror the pulse across repositories whenever new commits land.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


@dataclass(slots=True)
class CommitInfo:
    """Minimal commit metadata used to compose the contract."""

    hash: str
    author: str
    subject: str
    timestamp: float


@dataclass(slots=True)
class FederationPulseContract:
    """Structured representation of the contract payload."""

    repo: str
    head: CommitInfo
    commits: List[CommitInfo]
    attestation_base58: str
    recursive_verse: List[str]
    sovereign_cipher: str
    issued_at: float

    def to_dict(self) -> dict:
        """Return a JSON-serialisable view of the contract."""

        return {
            "repo": self.repo,
            "head": _commit_to_dict(self.head),
            "commits": [_commit_to_dict(entry) for entry in self.commits],
            "attestation_base58": self.attestation_base58,
            "recursive_verse": list(self.recursive_verse),
            "sovereign_cipher": self.sovereign_cipher,
            "issued_at": self.issued_at,
        }


def _commit_to_dict(commit: CommitInfo) -> dict:
    return {
        "hash": commit.hash,
        "author": commit.author,
        "subject": commit.subject,
        "timestamp": commit.timestamp,
    }


def _base58check_encode(payload: bytes) -> str:
    """Return the Base58Check encoding for ``payload`` without external deps."""

    checksum = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    data = payload + checksum

    integer = int.from_bytes(data, "big")
    encoded: list[str] = []
    while integer:
        integer, remainder = divmod(integer, 58)
        encoded.append(_BASE58_ALPHABET[remainder])
    encoded_str = "".join(reversed(encoded)) or "1"

    leading_zeroes = len(data) - len(data.lstrip(b"\x00"))
    return "1" * leading_zeroes + encoded_str


def _derive_base58_attestation(commit_hash: str) -> str:
    """Derive a Base58 attestation string from the commit hash."""

    try:
        payload = bytes.fromhex(commit_hash)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError(f"Commit hash is not hex encoded: {commit_hash!r}") from exc

    # Compress to 20 bytes to mirror Bitcoin address payloads if necessary.
    if len(payload) > 20:
        payload = hashlib.new("ripemd160", payload).digest()
    return _base58check_encode(payload)


def _build_recursive_verse(commits: Sequence[CommitInfo]) -> List[str]:
    """Compose a recursive verse from recent commit subjects."""

    verse: list[str] = []
    path: list[str] = []
    for entry in commits:
        path.append(entry.hash[:12])
        subject = entry.subject.strip() or "(no subject)"
        verse.append(f"{len(path):02d} ∴ {subject} ⇢ {' → '.join(path)}")
    return verse


def _derive_sovereign_cipher(
    repo: str,
    attestation: str,
    verse: Sequence[str],
    timestamp: float,
) -> str:
    """Bind the contract together with a deterministic hash."""

    hasher = hashlib.sha3_256()
    hasher.update(repo.encode("utf-8"))
    hasher.update(b"|")
    hasher.update(attestation.encode("utf-8"))
    hasher.update(b"|")
    for line in verse:
        hasher.update(line.encode("utf-8"))
        hasher.update(b"|")
    hasher.update(f"{timestamp:.9f}".encode("utf-8"))
    return hasher.hexdigest()


def _run_git(repo: Path, args: Iterable[str]) -> str:
    """Run a git command in *repo* and return the stripped stdout."""

    result = subprocess.run(  # noqa: PLW1510 - explicit text encoding
        ["git", *args],
        cwd=str(repo),
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def _gather_commits(repo: Path, limit: int) -> List[CommitInfo]:
    log_format = "%H%x1f%ct%x1f%an%x1f%s"
    output = _run_git(repo, ["log", f"-n{limit}", f"--pretty={log_format}"])
    commits: list[CommitInfo] = []
    for line in output.splitlines():
        if not line:
            continue
        hash_, ts, author, subject = line.split("\x1f", 3)
        commits.append(
            CommitInfo(
                hash=hash_,
                author=author,
                subject=subject,
                timestamp=float(ts),
            )
        )
    if not commits:
        raise RuntimeError("Repository does not contain any commits")
    return commits


def _resolve_repo_slug(repo: Path) -> str:
    try:
        url = _run_git(repo, ["config", "--get", "remote.origin.url"])
    except subprocess.CalledProcessError:
        return repo.name
    if not url:
        return repo.name
    slug = url.split("/")[-1]
    return slug.removesuffix(".git") or repo.name


def generate_contract(repo: Path, limit: int = 5) -> FederationPulseContract:
    """Generate a federation pulse contract for *repo*."""

    commits = _gather_commits(repo, limit)
    head = commits[0]
    attestation = _derive_base58_attestation(head.hash)
    verse = _build_recursive_verse(commits)
    issued_at = time.time()
    repo_slug = _resolve_repo_slug(repo)
    cipher = _derive_sovereign_cipher(repo_slug, attestation, verse, issued_at)

    return FederationPulseContract(
        repo=repo_slug,
        head=head,
        commits=commits,
        attestation_base58=attestation,
        recursive_verse=verse,
        sovereign_cipher=cipher,
        issued_at=issued_at,
    )


def write_contract(contract: FederationPulseContract, out_dir: Path) -> Path:
    """Persist *contract* to ``out_dir`` and return the JSON path."""

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{contract.repo}_contract.json"
    out_path.write_text(json.dumps(contract.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


def write_heartbeat(contract: FederationPulseContract, out_dir: Path) -> Path:
    """Write a heartbeat file for *contract* inside ``out_dir``."""

    out_dir.mkdir(parents=True, exist_ok=True)
    heartbeat_path = out_dir / f"{contract.repo}_heartbeat.txt"
    heartbeat_line = f"federation_heartbeat {contract.issued_at:.6f} {contract.attestation_base58}\n"
    heartbeat_path.write_text(heartbeat_line, encoding="utf-8")
    return heartbeat_path


def emit_contract(repo: Path, out_dir: Path, limit: int = 5) -> FederationPulseContract:
    """Generate the contract and persist the artifacts."""

    contract = generate_contract(repo, limit=limit)
    write_contract(contract, out_dir)
    write_heartbeat(contract, out_dir)
    return contract


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a Federation Pulse contract and heartbeat.")
    parser.add_argument(
        "--repo",
        action="append",
        type=Path,
        help="Repository path to inspect (defaults to current working directory).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("out/federation_pulse"),
        help="Directory where the contract and heartbeat artifacts are written.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of commits to braid into the recursive verse.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    repos = args.repo or [Path.cwd()]
    for repo in repos:
        emit_contract(repo.resolve(), args.out_dir.resolve(), limit=args.limit)
    return 0


__all__ = [
    "CommitInfo",
    "FederationPulseContract",
    "emit_contract",
    "generate_contract",
    "write_contract",
    "write_heartbeat",
]
