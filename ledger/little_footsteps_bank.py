"""Little Footsteps Bank sovereign ledger orchestration.

This module fuses three previously independent subsystems into a
cryptographically verifiable ledger tailored for the "Little Footsteps
Bank" mission:

* Proof-of-work reconstruction transcripts used throughout the Echo
  archival efforts.
* Puzzle attestation trails that certify authorship and stewardship.
* Echo skeleton key derivations that bind every movement of value to the
  same deterministic key space trusted by the community.

Each ledger entry captures a full audit bundle and automatically writes
supporting artifacts:

* JSONL ledger lines under ``ledger/little_footsteps_bank.jsonl``.
* Canonical proof packages in ``proofs/little_footsteps_bank/``.
* Puzzle-style documentation in ``puzzle_solutions/little_footsteps_bank.md``.

When the OpenTimestamps CLI is available the module will stamp every
entry and store a base64 encoded receipt alongside the proof package.
The classes are intentionally lightweight so the workflow works out of
the box inside this repository without additional dependencies.  To
record a transaction via CLI run::

    python -m ledger.little_footsteps_bank --help

"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from skeleton_key_core import derive_from_skeleton, read_secret_from_file, read_secret_from_phrase


logger = logging.getLogger(__name__)


def _sha256_hex(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def _canonical_dumps(data: Dict[str, Any]) -> str:
    """Serialize ``data`` with stable ordering and minimal separators."""

    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ProofOfWorkReconstruction:
    """Minimal proof-of-work reconstruction payload."""

    puzzle_id: str
    block_height: int
    block_hash: str
    difficulty_target: str
    nonce: int
    notes: str

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PuzzleAttestation:
    """Puzzle attestation record bundled with ledger entries."""

    attestation_id: str
    puzzle_reference: str
    attestor: str
    signature: str
    witness: str
    ots_receipt: Optional[str] = None

    def to_record(self) -> Dict[str, Any]:
        record = asdict(self)
        if self.ots_receipt is None:
            record.pop("ots_receipt")
        return record


@dataclass(slots=True)
class SkeletonKeyRecord:
    """Fingerprint of a skeleton key derivation without leaking secrets."""

    namespace: str
    index: int
    eth_address: Optional[str]
    btc_wif_prefix: str
    btc_wif_checksum: str
    priv_fingerprint: str

    @classmethod
    def from_secret(
        cls,
        secret: bytes,
        namespace: str,
        index: int,
    ) -> "SkeletonKeyRecord":
        derived = derive_from_skeleton(secret, namespace, index)
        btc_wif_prefix = derived.btc_wif[:6] + "…"
        btc_wif_checksum = _sha256_hex(derived.btc_wif.encode())[:24]
        priv_fingerprint = _sha256_hex(bytes.fromhex(derived.priv_hex))
        return cls(
            namespace=namespace,
            index=index,
            eth_address=derived.eth_address,
            btc_wif_prefix=btc_wif_prefix,
            btc_wif_checksum=btc_wif_checksum,
            priv_fingerprint=priv_fingerprint,
        )

    def to_record(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LedgerEntry:
    """Complete sovereign ledger bundle."""

    seq: int
    bank: str
    timestamp: str
    direction: str
    account: str
    asset: str
    amount: str
    narrative: str
    proof_of_work: ProofOfWorkReconstruction
    puzzle_attestation: PuzzleAttestation
    skeleton_key: SkeletonKeyRecord

    def payload(self) -> Dict[str, Any]:
        return {
            "seq": self.seq,
            "bank": self.bank,
            "timestamp": self.timestamp,
            "direction": self.direction,
            "account": self.account,
            "asset": self.asset,
            "amount": self.amount,
            "narrative": self.narrative,
            "proofs": {
                "proof_of_work": self.proof_of_work.to_record(),
                "puzzle_attestation": self.puzzle_attestation.to_record(),
                "skeleton_key": self.skeleton_key.to_record(),
            },
        }

    def digest(self) -> str:
        return "sha256:" + _sha256_hex(_canonical_dumps(self.payload()).encode("utf-8"))


class SovereignLedger:
    """Coordinator for the Little Footsteps Bank ledger."""

    def __init__(
        self,
        *,
        bank: str,
        ledger_path: Path,
        puzzle_path: Path,
        proofs_dir: Path,
        skip_ots: bool = False,
    ) -> None:
        self.bank = bank
        self.ledger_path = ledger_path
        self.puzzle_path = puzzle_path
        self.proofs_dir = proofs_dir
        self.skip_ots = skip_ots
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.proofs_dir.mkdir(parents=True, exist_ok=True)
        self._seq = self._load_last_sequence()
        self._ensure_puzzle_header()

    def _load_last_sequence(self) -> int:
        if not self.ledger_path.exists():
            return -1
        last_seq = -1
        with self.ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                    last_seq = max(last_seq, int(payload.get("seq", -1)))
                except json.JSONDecodeError:
                    logger.warning("Skipping malformed ledger line: %s", line)
        return last_seq

    def record_transaction(
        self,
        *,
        direction: str,
        account: str,
        asset: str,
        amount: str,
        narrative: str,
        pow_proof: ProofOfWorkReconstruction,
        puzzle_attestation: PuzzleAttestation,
        skeleton_key: SkeletonKeyRecord,
    ) -> LedgerEntry:
        if direction not in {"inflow", "outflow"}:
            raise ValueError("direction must be 'inflow' or 'outflow'")

        seq = self._seq + 1
        self._seq = seq
        entry = LedgerEntry(
            seq=seq,
            bank=self.bank,
            timestamp=_iso_now(),
            direction=direction,
            account=account,
            asset=asset,
            amount=amount,
            narrative=narrative,
            proof_of_work=pow_proof,
            puzzle_attestation=puzzle_attestation,
            skeleton_key=skeleton_key,
        )

        digest = entry.digest()
        proof_path, ots_receipt = self._write_supporting_artifacts(entry, digest)
        payload = entry.payload() | {"digest": digest}
        if ots_receipt is not None:
            payload["ots_receipt"] = ots_receipt
        self._append_ledger_line(payload)
        self._append_puzzle_section(entry, digest, proof_path, ots_receipt)
        return entry

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _append_ledger_line(self, payload: Dict[str, Any]) -> None:
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _write_supporting_artifacts(
        self,
        entry: LedgerEntry,
        digest: str,
    ) -> tuple[Path, Optional[str]]:
        proof_path = self.proofs_dir / f"entry_{entry.seq:05d}.json"
        proof_payload = entry.payload() | {"digest": digest}
        proof_path.write_text(json.dumps(proof_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if self.skip_ots:
            return proof_path, None

        ots_receipt = self._maybe_stamp_opentimestamps(proof_path)
        return proof_path, ots_receipt

    def _maybe_stamp_opentimestamps(self, proof_path: Path) -> Optional[str]:
        try:
            result = subprocess.run(
                ["ots", "stamp", str(proof_path)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("OpenTimestamps stamp: %s", result.stdout.strip())
        except FileNotFoundError:
            logger.warning("OpenTimestamps CLI (ots) not found; skipping stamp.")
            return None
        except subprocess.CalledProcessError as exc:
            logger.warning("OpenTimestamps stamp failed: %s", exc.stderr)
            return None

        receipt_path = proof_path.with_suffix(proof_path.suffix + ".ots")
        if not receipt_path.exists():
            logger.warning("ots reported success but receipt is missing: %s", receipt_path)
            return None

        encoded_path = receipt_path.with_suffix(receipt_path.suffix + ".base64")
        encoded_path.write_text(base64.b64encode(receipt_path.read_bytes()).decode("ascii"), encoding="utf-8")
        if receipt_path.is_absolute():
            try:
                return str(encoded_path.relative_to(Path.cwd()))
            except ValueError:
                return str(encoded_path)
        return str(encoded_path)

    # ------------------------------------------------------------------
    # Puzzle documentation helpers
    # ------------------------------------------------------------------

    def _ensure_puzzle_header(self) -> None:
        if self.puzzle_path.exists():
            return
        self.puzzle_path.parent.mkdir(parents=True, exist_ok=True)
        header = (
            "# Little Footsteps Bank Sovereign Ledger\n\n"
            "This document renders each ledger addition as a community puzzle\n"
            "so investigators can replay the proof-of-work reconstruction,\n"
            "verify attestations, and audit the skeleton key fingerprints.\n"
            "Every section includes the canonical digest plus an"
            " OpenTimestamps receipt when available.\n\n"
            "| Field | Description |\n"
            "|-------|-------------|\n"
            "| Digest | Canonical sha256 hash binding transaction + proofs |\n"
            "| Proof Bundle | JSON artifact stored under proofs/little_footsteps_bank |\n"
            "| Skeleton Key | Namespace + index + fingerprint for deterministic verification |\n"
            "| OTS | Base64 encoded OpenTimestamps receipt path (optional) |\n\n"
        )
        self.puzzle_path.write_text(header, encoding="utf-8")

    def _append_puzzle_section(
        self,
        entry: LedgerEntry,
        digest: str,
        proof_path: Path,
        ots_receipt: Optional[str],
    ) -> None:
        section = [
            f"## Puzzle {entry.seq:05d} — {entry.direction.title()} {entry.amount} {entry.asset}\n",
            "\n",
            f"**Account:** `{entry.account}`  ",
            f"**Narrative:** {entry.narrative}\n\n",
            "```json\n",
            _canonical_dumps(entry.payload()),
            "\n```\n\n",
            f"* Digest: `{digest}`\n",
            f"* Proof bundle: `{proof_path}`\n",
            f"* Skeleton key namespace/index: `{entry.skeleton_key.namespace}` / `{entry.skeleton_key.index}`\n",
            f"* Skeleton key fingerprint: `{entry.skeleton_key.priv_fingerprint}`\n",
            f"* Puzzle attestation witness: `{entry.puzzle_attestation.witness}`\n",
        ]
        if ots_receipt:
            section.append(f"* OpenTimestamps receipt: `{ots_receipt}`\n")
        section.append("\n---\n\n")
        with self.puzzle_path.open("a", encoding="utf-8") as handle:
            handle.writelines(section)


def _read_pow_payload(path: Path) -> ProofOfWorkReconstruction:
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        return ProofOfWorkReconstruction(
            puzzle_id=data["puzzle_id"],
            block_height=int(data["block_height"]),
            block_hash=data["block_hash"],
            difficulty_target=data["difficulty_target"],
            nonce=int(data["nonce"]),
            notes=data.get("notes", ""),
        )
    except KeyError as exc:
        raise ValueError(f"Missing proof-of-work field: {exc}") from exc


def _read_attestation_payload(path: Path) -> PuzzleAttestation:
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        return PuzzleAttestation(
            attestation_id=data["attestation_id"],
            puzzle_reference=data["puzzle_reference"],
            attestor=data["attestor"],
            signature=data["signature"],
            witness=data["witness"],
            ots_receipt=data.get("ots_receipt"),
        )
    except KeyError as exc:
        raise ValueError(f"Missing attestation field: {exc}") from exc


def _read_secret(args: argparse.Namespace) -> bytes:
    if args.skeleton_phrase:
        return read_secret_from_phrase(args.skeleton_phrase)
    if args.skeleton_file:
        return read_secret_from_file(args.skeleton_file)
    raise ValueError("Supply --skeleton-phrase or --skeleton-file")


def cli(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Record Little Footsteps Bank ledger entries")
    parser.add_argument("--direction", choices=["inflow", "outflow"], required=True)
    parser.add_argument("--account", required=True, help="Account identifier (e.g. treasury:core)")
    parser.add_argument("--asset", default="USD", help="Asset ticker (default: USD)")
    parser.add_argument("--amount", required=True, help="Amount recorded (string to preserve exact formatting)")
    parser.add_argument("--narrative", required=True, help="Human readable context for the movement")
    parser.add_argument("--pow", type=Path, required=True, help="Path to proof-of-work reconstruction JSON")
    parser.add_argument("--attestation", type=Path, required=True, help="Path to puzzle attestation JSON")
    parser.add_argument("--skeleton-phrase", help="Skeleton key phrase (mutually exclusive with --skeleton-file)")
    parser.add_argument("--skeleton-file", type=Path, help="Path to skeleton key secret file")
    parser.add_argument("--skeleton-namespace", default="little-footsteps", help="Skeleton namespace seed")
    parser.add_argument("--skeleton-index", type=int, default=0, help="Skeleton derivation index")
    parser.add_argument("--bank", default="Little Footsteps Bank", help="Ledger bank label")
    parser.add_argument(
        "--ledger-path",
        type=Path,
        default=Path("ledger/little_footsteps_bank.jsonl"),
        help="Where to store the sovereign ledger JSONL",
    )
    parser.add_argument(
        "--puzzle-path",
        type=Path,
        default=Path("puzzle_solutions/little_footsteps_bank.md"),
        help="Puzzle documentation destination",
    )
    parser.add_argument(
        "--proofs-dir",
        type=Path,
        default=Path("proofs/little_footsteps_bank"),
        help="Directory for canonical proof bundles",
    )
    parser.add_argument("--skip-ots", action="store_true", help="Skip OpenTimestamps stamping")
    parser.add_argument("--log-level", default="INFO", help="Python logging level")
    args = parser.parse_args(list(argv) if argv is not None else None)

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    secret = _read_secret(args)
    pow_payload = _read_pow_payload(args.pow)
    attestation_payload = _read_attestation_payload(args.attestation)
    skeleton_record = SkeletonKeyRecord.from_secret(secret, args.skeleton_namespace, args.skeleton_index)

    ledger = SovereignLedger(
        bank=args.bank,
        ledger_path=args.ledger_path,
        puzzle_path=args.puzzle_path,
        proofs_dir=args.proofs_dir,
        skip_ots=args.skip_ots,
    )
    entry = ledger.record_transaction(
        direction=args.direction,
        account=args.account,
        asset=args.asset,
        amount=args.amount,
        narrative=args.narrative,
        pow_proof=pow_payload,
        puzzle_attestation=attestation_payload,
        skeleton_key=skeleton_record,
    )

    print(json.dumps(entry.payload() | {"digest": entry.digest()}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
