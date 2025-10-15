"""Provenance and attestation utilities for Echo builds and engine runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, List, Optional


_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_OUTPUT_DIR = _REPO_ROOT / "artifacts" / "provenance"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN"
    return result.stdout.strip() or "UNKNOWN"


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _file_digest(path: Path) -> str:
    data = path.read_bytes()
    return _sha256_bytes(data)


def _default_toolchain() -> dict:
    version_info = ".".join(map(str, os.sys.version_info[:3]))
    return {"python": version_info, "platform": os.name}


@dataclass
class ArtifactRecord:
    path: str
    digest: str


@dataclass
class ProvenanceRecord:
    repo: str
    commit: str
    actor: str
    cycle_id: str
    context: str
    inputs: List[ArtifactRecord]
    outputs: List[ArtifactRecord]
    toolchain_versions: dict
    runtime_seed: str
    manifest_digest: str | None
    start_time: str
    end_time: str
    seal: dict = field(default_factory=dict)

    def stable_dict(self) -> dict:
        payload = asdict(self)
        payload["inputs"] = [asdict(item) for item in self.inputs]
        payload["outputs"] = [asdict(item) for item in self.outputs]
        return payload


class ProvenanceEmitter:
    """Create provenance attestations for Echo operations."""

    def __init__(
        self,
        output_directory: Path | None = None,
        *,
        clock: Callable[[], datetime] = _now,
        signer: Callable[[bytes], Optional[dict]] | None = None,
    ) -> None:
        self.output_directory = output_directory or _DEFAULT_OUTPUT_DIR
        self.clock = clock
        self.signer = signer

    def emit(
        self,
        *,
        context: str,
        inputs: Iterable[Path] = (),
        outputs: Iterable[Path] = (),
        actor: str | None = None,
        cycle_id: str | None = None,
        runtime_seed: str | None = None,
        manifest_path: Path | None = None,
    ) -> Path:
        start = self.clock().isoformat().replace("+00:00", "Z")
        manifest_digest = None
        manifest_file = manifest_path or (_REPO_ROOT / "echo_manifest.json")
        if manifest_file.exists():
            manifest_digest = _sha256_bytes(
                json.dumps(
                    json.loads(manifest_file.read_text(encoding="utf-8")),
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
        actor_name = actor or os.environ.get("GIT_COMMITTER_NAME") or _git("config", "user.name")
        record = ProvenanceRecord(
            repo=_git("config", "--get", "remote.origin.url"),
            commit=_git("rev-parse", "HEAD"),
            actor=actor_name or "UNKNOWN",
            cycle_id=cycle_id or _git("rev-parse", "--short", "HEAD"),
            context=context,
            inputs=[ArtifactRecord(str(path), _file_digest(path)) for path in inputs],
            outputs=[ArtifactRecord(str(path), _file_digest(path)) for path in outputs],
            toolchain_versions=_default_toolchain(),
            runtime_seed=runtime_seed or "0",
            manifest_digest=manifest_digest,
            start_time=start,
            end_time=self.clock().isoformat().replace("+00:00", "Z"),
        )
        payload = record.stable_dict()
        canonical_source = dict(payload)
        canonical_source.pop("seal", None)
        canonical = json.dumps(canonical_source, sort_keys=True, separators=(",", ":")).encode("utf-8")
        seal = {"sha256": _sha256_bytes(canonical)}
        if self.signer is not None:
            signature = self.signer(canonical)
            if signature:
                seal["signature"] = signature
        record.seal = seal
        payload["seal"] = seal
        self.output_directory.mkdir(parents=True, exist_ok=True)
        target = self.output_directory / f"{record.cycle_id}_{seal['sha256']}.json"
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


def verify_provenance(path: Path) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    seal = payload.get("seal", {})
    canonical = json.dumps(
        {key: value for key, value in payload.items() if key != "seal"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    expected = seal.get("sha256")
    if expected != _sha256_bytes(canonical):
        return False
    signature = seal.get("signature")
    if signature and shutil.which("gpg"):
        return _verify_signature(canonical, signature)
    return True


def _verify_signature(payload: bytes, signature: dict) -> bool:
    if "armored" not in signature:
        return False
    try:
        process = subprocess.run(
            ["gpg", "--verify"],
            input=signature["armored"].encode("utf-8"),
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return process.returncode == 0


def bundle_provenance(out_path: Path, source_dir: Path | None = None) -> Path:
    directory = source_dir or _DEFAULT_OUTPUT_DIR
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out_path, mode="w:gz") as tar:
        if directory.exists():
            for item in sorted(directory.glob("*.json")):
                tar.add(item, arcname=item.name)
    return out_path


def _cmd_emit(args: argparse.Namespace) -> int:
    emitter = ProvenanceEmitter()
    context = args.context
    inputs = [Path(path) for path in args.input]
    outputs = [Path(path) for path in args.output]
    manifest_path = Path(args.manifest) if args.manifest else None
    result = emitter.emit(
        context=context,
        inputs=inputs,
        outputs=outputs,
        actor=args.actor,
        cycle_id=args.cycle,
        runtime_seed=args.seed,
        manifest_path=manifest_path,
    )
    print(result)
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.path)
    ok = verify_provenance(path)
    print("valid" if ok else "invalid")
    return 0 if ok else 1


def _cmd_bundle(args: argparse.Namespace) -> int:
    output = Path(args.out)
    bundle_provenance(output)
    print(output)
    return 0


def build_parser(subparsers: argparse._SubParsersAction) -> None:
    provenance_parser = subparsers.add_parser("provenance", help="Provenance tooling")
    provenance_sub = provenance_parser.add_subparsers(dest="provenance_command", required=True)

    emit_parser = provenance_sub.add_parser("emit", help="Emit a provenance record")
    emit_parser.add_argument("--context", required=True, help="Execution context (manifest or engine:NAME)")
    emit_parser.add_argument("--input", action="append", default=[], help="Input artifact path")
    emit_parser.add_argument("--output", action="append", default=[], help="Output artifact path")
    emit_parser.add_argument("--manifest", help="Manifest path override")
    emit_parser.add_argument("--actor")
    emit_parser.add_argument("--cycle")
    emit_parser.add_argument("--seed")
    emit_parser.set_defaults(func=_cmd_emit)

    verify_parser = provenance_sub.add_parser("verify", help="Verify a provenance file")
    verify_parser.add_argument("path", help="Path to provenance JSON")
    verify_parser.set_defaults(func=_cmd_verify)

    bundle_parser = provenance_sub.add_parser("bundle", help="Bundle provenance artifacts")
    bundle_parser.add_argument("--out", required=True, help="Output tarball path")
    bundle_parser.set_defaults(func=_cmd_bundle)


__all__ = [
    "ProvenanceEmitter",
    "ProvenanceRecord",
    "bundle_provenance",
    "build_parser",
    "verify_provenance",
]

