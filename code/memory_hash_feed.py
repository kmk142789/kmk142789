"""Utilities for generating evolving context snapshots for the sigil QR pipeline.

The :class:`MemoryHashFeed` class collects lightweight signals from the current
repository – timestamps, git metadata, and selected context documents – and
produces deterministic hashes that can be embedded inside the evolving sigil
codes.  The goal is to keep the module side-effect free and easily testable
while offering clear extension points for richer state ingestion later on.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional


Snapshot = Mapping[str, Any]


def _default_context_sources() -> Dict[str, Path]:
    """Return a curated map of optional context files to fold into hashes.

    The repo contains a sprawling collection of manifest-like JSON documents.
    Pulling the entire tree into every payload would be prohibitively expensive
    and difficult to stabilise; instead we track a short list of canonical files
    that summarise the state of the Echo ecosystem.  These defaults can be
    customised by callers and are safe to extend.
    """

    candidates = [
        Path("echo_manifest.json"),
        Path("pulse.json"),
        Path("pulse_history.json"),
        Path("state"),
    ]

    context: Dict[str, Path] = {}
    for path in candidates:
        if path.exists():
            context[path.name] = path
    return context


@dataclass(slots=True)
class MemoryHashFeed:
    """Build evolving payloads for the living sigil system.

    Parameters
    ----------
    base_dir:
        Root directory to read context artefacts from.  Defaults to the current
        working directory so that the module can be executed from tooling or
        notebooks without extra configuration.
    include_sources:
        Optional mapping of friendly names to files or directories whose
        contents should influence the payload hash.  When not provided the
        module falls back to :func:`_default_context_sources`.
    clock:
        Test hook that can be swapped with a deterministic supplier in unit
        tests.
    """

    base_dir: Path = field(default_factory=Path.cwd)
    include_sources: Optional[Mapping[str, Path]] = None
    clock: Any = datetime.now

    def build_snapshot(
        self,
        extra_context: Optional[Mapping[str, Any]] = None,
    ) -> Snapshot:
        """Collect the current timestamp, git metadata, and file hashes.

        Parameters
        ----------
        extra_context:
            Callers can provide additional lightweight metadata (for example the
            active task identifier from orchestration tooling).  The values must
            be JSON serialisable.
        """

        timestamp = self.clock(timezone.utc)
        git_info = self._git_state()
        content_hashes = self._hash_context_sources()

        snapshot: MutableMapping[str, Any] = {
            "timestamp": timestamp.isoformat(),
            "git": git_info,
            "content_hashes": content_hashes,
        }

        if extra_context:
            snapshot["extra"] = extra_context

        snapshot["combined_hash"] = self._combined_digest(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    # Internal helpers

    def _git_state(self) -> Dict[str, Optional[str]]:
        """Capture lightweight git metadata if the repo is initialised."""

        def safe_call(args: Iterable[str]) -> Optional[str]:
            try:
                result = subprocess.run(
                    list(args),
                    cwd=self.base_dir,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None
            return result.stdout.strip() or None

        return {
            "head": safe_call(["git", "rev-parse", "HEAD"]),
            "branch": safe_call(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
            "status": safe_call(["git", "status", "--short"]),
        }

    def _hash_context_sources(self) -> Dict[str, str]:
        """Return stable SHA-256 digests for each configured file or directory."""

        sources = self.include_sources or _default_context_sources()
        hashes: Dict[str, str] = {}
        for label, relative_path in sources.items():
            absolute = (self.base_dir / relative_path).resolve()
            if absolute.is_dir():
                digest = self._hash_directory(absolute)
            elif absolute.is_file():
                digest = self._hash_file(absolute)
            else:
                continue
            hashes[label] = digest
        return dict(sorted(hashes.items()))

    def _hash_file(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _hash_directory(self, path: Path) -> str:
        hasher = hashlib.sha256()
        for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
            relative = file_path.relative_to(path)
            hasher.update(str(relative).encode("utf-8"))
            with file_path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(8192), b""):
                    hasher.update(chunk)
        return hasher.hexdigest()

    def _combined_digest(self, snapshot: Snapshot) -> str:
        serialised = json.dumps(snapshot, sort_keys=True, separators=(",", ":"))
        return hashlib.sha3_512(serialised.encode("utf-8")).hexdigest()


__all__ = ["MemoryHashFeed", "Snapshot"]

