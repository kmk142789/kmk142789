"""Utilities for emitting and verifying Echo provenance attestations."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence


class ProvenanceError(RuntimeError):
    """Raised when provenance generation or verification fails."""


@dataclass(frozen=True)
class FileDigest:
    """Represents a file that was used as an input or generated output."""

    path: str
    sha256: str


@dataclass
class ProvenanceRecord:
    """Structured provenance payload persisted alongside Echo artifacts."""

    repo: str
    commit: str
    actor: str
    cycle_id: str
    context: str
    manifest_digest: str
    inputs: List[FileDigest]
    outputs: List[FileDigest]
    toolchain_versions: Dict[str, str]
    runtime_seed: str
    start_time: str
    end_time: str
    metadata: Dict[str, str] = field(default_factory=dict)
    seal: Optional[str] = None
    gpg_signature: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        payload = dataclasses.asdict(self)
        # Dataclasses.asdict converts FileDigest objects into dicts automatically.
        return payload


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "echo_manifest.json"
DEFAULT_PROVENANCE_DIR = REPO_ROOT / "artifacts" / "provenance"


def _sha256_path(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _detect_repo_root(path: Path) -> Path:
    current = path.resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").is_dir():
            return parent
    return path.resolve()


def _git_output(args: Sequence[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:  # pragma: no cover - defensive
        raise ProvenanceError(f"git {' '.join(args)} failed: {exc}") from exc
    return result.stdout.strip()


def _resolve_file_digests(paths: Iterable[Path]) -> List[FileDigest]:
    digests: List[FileDigest] = []
    for raw in sorted(set(Path(p).resolve() for p in paths)):
        if not raw.exists():
            raise ProvenanceError(f"Input path does not exist: {raw}")
        digest = _sha256_path(raw)
        try:
            rel = raw.relative_to(REPO_ROOT)
        except ValueError:
            rel = raw
        digests.append(FileDigest(path=str(rel), sha256=digest))
    return digests


def _canonical_payload(record: ProvenanceRecord) -> Dict[str, object]:
    payload = record.to_dict()
    payload.pop("seal", None)
    payload.pop("gpg_signature", None)
    return payload


def _stable_json(payload: Dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _default_actor() -> str:
    return (
        os.environ.get("GITHUB_ACTOR")
        or os.environ.get("USER")
        or os.environ.get("USERNAME")
        or "UNKNOWN"
    )


def _toolchain_versions() -> Dict[str, str]:
    python_cmd = subprocess.run(
        ["python", "--version"], capture_output=True, text=True, check=False
    )
    python_version = (python_cmd.stdout or python_cmd.stderr).strip()
    info: Dict[str, str] = {"python": python_version}
    for tool in ("pip", "node", "npm"):
        if shutil.which(tool):
            result = subprocess.run(
                [tool, "--version"], capture_output=True, text=True, check=False
            )
            text = (result.stdout or result.stderr).strip()
            if text:
                info[tool] = text
    return info


def build_record(
    *,
    context: str,
    inputs: Iterable[Path],
    outputs: Iterable[Path],
    repo: Optional[Path] = None,
    manifest_path: Path | None = None,
    cycle_id: Optional[str] = None,
    runtime_seed: Optional[str] = None,
    actor: Optional[str] = None,
    toolchain_versions: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, str]] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> ProvenanceRecord:
    repo_root = _detect_repo_root(repo or REPO_ROOT)
    manifest_file = manifest_path or DEFAULT_MANIFEST
    if not manifest_file.exists():
        raise ProvenanceError(f"Manifest not found: {manifest_file}")
    manifest_digest = _sha256_path(manifest_file)
    commit = _git_output(["rev-parse", "HEAD"], repo_root)
    record = ProvenanceRecord(
        repo=str(repo_root),
        commit=commit,
        actor=actor or _default_actor(),
        cycle_id=cycle_id or commit,
        context=context,
        manifest_digest=manifest_digest,
        inputs=_resolve_file_digests(inputs),
        outputs=_resolve_file_digests(outputs),
        toolchain_versions=toolchain_versions or _toolchain_versions(),
        runtime_seed=runtime_seed or "0",
        start_time=(start_time or datetime.now(timezone.utc)).isoformat(),
        end_time=(end_time or datetime.now(timezone.utc)).isoformat(),
        metadata=metadata or {},
    )
    record.seal = hashlib.sha256(_stable_json(_canonical_payload(record)).encode("utf-8")).hexdigest()
    return record


def _gpg_available() -> bool:
    return shutil.which("gpg") is not None


def _gpg_sign(payload: bytes, key: Optional[str] = None) -> str:
    if not _gpg_available():
        raise ProvenanceError("gpg binary is required for signing but was not found")
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(delete=False) as payload_file:
        payload_file.write(payload)
        payload_file.flush()
        payload_path = Path(payload_file.name)
    with NamedTemporaryFile(delete=False) as signature_file:
        signature_path = Path(signature_file.name)
    command = [
        "gpg",
        "--armor",
        "--batch",
        "--yes",
        "--detach-sign",
        "--output",
        str(signature_path),
        str(payload_path),
    ]
    if key:
        command.insert(4, "--local-user")
        command.insert(5, key)
    try:
        subprocess.run(command, check=True, capture_output=True)
        signature_text = signature_path.read_text(encoding="utf-8")
    except (subprocess.CalledProcessError, OSError) as exc:  # pragma: no cover - defensive
        raise ProvenanceError(f"gpg signing failed: {exc}") from exc
    finally:
        payload_path.unlink(missing_ok=True)
        signature_path.unlink(missing_ok=True)
    return signature_text


def _gpg_verify(payload: bytes, signature: str) -> bool:
    if not _gpg_available():
        raise ProvenanceError("gpg binary is required for verification but was not found")
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile(delete=False) as payload_file:
        payload_file.write(payload)
        payload_file.flush()
        payload_path = Path(payload_file.name)
    with NamedTemporaryFile(delete=False) as signature_file:
        signature_file.write(signature.encode("utf-8"))
        signature_file.flush()
        signature_path = Path(signature_file.name)
    try:
        result = subprocess.run(
            ["gpg", "--batch", "--verify", str(signature_path), str(payload_path)],
            capture_output=True,
        )
        return result.returncode == 0
    finally:
        payload_path.unlink(missing_ok=True)
        signature_path.unlink(missing_ok=True)


def write_record(
    record: ProvenanceRecord,
    *,
    output_path: Path | None = None,
    sign: bool = False,
    gpg_key: Optional[str] = None,
) -> Path:
    directory = output_path.parent if output_path else DEFAULT_PROVENANCE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    target = output_path or directory / f"provenance_{record.cycle_id}.json"
    payload = record.to_dict()
    payload["seal"] = record.seal
    if sign:
        canonical = _stable_json(_canonical_payload(record)).encode("utf-8")
        payload["gpg_signature"] = _gpg_sign(canonical, key=gpg_key)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def emit(
    *,
    context: str,
    inputs: Iterable[Path],
    outputs: Iterable[Path],
    repo: Optional[Path] = None,
    manifest_path: Path | None = None,
    cycle_id: Optional[str] = None,
    runtime_seed: Optional[str] = None,
    actor: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
    output_path: Path | None = None,
    sign: bool = False,
    gpg_key: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Path:
    record = build_record(
        context=context,
        inputs=list(inputs),
        outputs=list(outputs),
        repo=repo,
        manifest_path=manifest_path,
        cycle_id=cycle_id,
        runtime_seed=runtime_seed,
        actor=actor,
        metadata=metadata,
        start_time=start_time,
        end_time=end_time,
    )
    return write_record(record, output_path=output_path, sign=sign, gpg_key=gpg_key)


def verify(path: Path, *, require_signature: bool = False) -> ProvenanceRecord:
    if not path.exists():
        raise ProvenanceError(f"Provenance file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    record = ProvenanceRecord(
        repo=payload["repo"],
        commit=payload["commit"],
        actor=payload["actor"],
        cycle_id=payload["cycle_id"],
        context=payload["context"],
        manifest_digest=payload["manifest_digest"],
        inputs=[FileDigest(**entry) for entry in payload.get("inputs", [])],
        outputs=[FileDigest(**entry) for entry in payload.get("outputs", [])],
        toolchain_versions=payload.get("toolchain_versions", {}),
        runtime_seed=str(payload.get("runtime_seed", "0")),
        start_time=payload["start_time"],
        end_time=payload["end_time"],
        metadata=payload.get("metadata", {}),
        seal=payload.get("seal"),
        gpg_signature=payload.get("gpg_signature"),
    )
    if not record.seal:
        raise ProvenanceError("Provenance file missing seal")
    expected = hashlib.sha256(_stable_json(_canonical_payload(record)).encode("utf-8")).hexdigest()
    if expected != record.seal:
        raise ProvenanceError("Seal mismatch: provenance payload has been tampered with")
    if require_signature:
        signature = record.gpg_signature
        if not signature:
            raise ProvenanceError("Provenance file missing GPG signature")
        canonical = _stable_json(_canonical_payload(record)).encode("utf-8")
        if not _gpg_verify(canonical, signature):
            raise ProvenanceError("GPG signature verification failed")
    return record


def bundle(
    *,
    source: Optional[Path] = None,
    output: Optional[Path] = None,
    include_hidden: bool = False,
) -> Path:
    directory = source or DEFAULT_PROVENANCE_DIR
    if not directory.exists():
        raise ProvenanceError(f"Provenance directory not found: {directory}")
    target = output or (REPO_ROOT / "artifacts" / f"provenance_bundle_{datetime.now(timezone.utc).date()}.tar.gz")
    target.parent.mkdir(parents=True, exist_ok=True)
    entries = [
        entry
        for entry in sorted(directory.glob("*.json"))
        if include_hidden or not entry.name.startswith(".")
    ]
    if not entries:
        raise ProvenanceError(f"No provenance records to bundle in {directory}")
    with tarfile.open(target, "w:gz") as archive:
        for entry in entries:
            archive.add(entry, arcname=entry.name)
    return target


__all__ = [
    "ProvenanceError",
    "ProvenanceRecord",
    "FileDigest",
    "emit",
    "verify",
    "bundle",
    "build_record",
    "write_record",
]

