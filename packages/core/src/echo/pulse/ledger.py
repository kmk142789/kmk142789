"""Append-only ledger for weave receipts with API helpers."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, List, Mapping, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from echo.modes.phantom import PhantomReporter


_LEDGER_SECRET = b"echo-pulse-ledger-signature-v1"


@dataclass(frozen=True)
class HarmonixLink:
    snapshot_id: str
    cycle: int
    timestamp: str
    recursion_hash: str

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "cycle": self.cycle,
            "timestamp": self.timestamp,
            "recursion_hash": self.recursion_hash,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "HarmonixLink":
        try:
            snapshot_id = payload["snapshot_id"]
            cycle = payload["cycle"]
            timestamp = payload["timestamp"]
            recursion_hash = payload["recursion_hash"]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise ValueError("Harmonix link payload missing required field") from exc
        if snapshot_id is None or timestamp is None or recursion_hash is None:
            raise ValueError("Harmonix link payload contains null fields")
        return cls(
            snapshot_id=str(snapshot_id),
            cycle=int(cycle),
            timestamp=str(timestamp),
            recursion_hash=str(recursion_hash),
        )


@dataclass(frozen=True)
class PulseReceipt:
    sha256_of_diff: str
    time: str
    actor: str
    rhyme: str
    result: str
    seed: str
    signature: str
    path: Path
    harmonix: Optional[HarmonixLink] = None

    def to_dict(self, include_signature: bool = True) -> dict:
        payload = {
            "sha256_of_diff": self.sha256_of_diff,
            "time": self.time,
            "actor": self.actor,
            "rhyme": self.rhyme,
            "result": self.result,
            "seed": self.seed,
        }
        if self.harmonix is not None:
            payload["harmonix"] = self.harmonix.to_dict()
        if include_signature:
            payload["signature"] = self.signature
        return payload


class PulseLedger:
    """Manages signed JSON receipts in an append-only directory."""

    def __init__(self, root: Path | None = None, secret: bytes | None = None) -> None:
        self.root = root or Path("state") / "pulse" / "receipts"
        self.secret = secret or _LEDGER_SECRET

    def _signature(self, payload: dict) -> str:
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hmac.new(self.secret, data, hashlib.sha256).hexdigest()

    def _timestamp(self) -> datetime:
        return datetime.now(timezone.utc)

    def _rhyme(self, diff_hash: str) -> str:
        couplet = diff_hash[-8:]
        return f"Pulse weave sings {couplet} in time"

    def _receipt_path(self, timestamp: datetime, diff_hash: str) -> Path:
        date_dir = self.root / f"{timestamp.year:04d}" / f"{timestamp.month:02d}" / f"{timestamp.day:02d}"
        date_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{timestamp.strftime('%H%M%S%f')}_{diff_hash[:12]}.json"
        return date_dir / filename

    def log(
        self,
        *,
        diff_signature: str,
        actor: str,
        result: str,
        seed: str,
        harmonix: Mapping[str, object] | HarmonixLink | None = None,
    ) -> PulseReceipt:
        timestamp = self._timestamp()
        diff_hash = hashlib.sha256(diff_signature.encode("utf-8")).hexdigest()
        payload = {
            "sha256_of_diff": diff_hash,
            "time": timestamp.isoformat(),
            "actor": actor,
            "rhyme": self._rhyme(diff_hash),
            "result": result,
            "seed": seed,
        }
        harmonix_link: Optional[HarmonixLink] = None
        if harmonix is not None:
            if isinstance(harmonix, HarmonixLink):
                harmonix_link = harmonix
            elif isinstance(harmonix, Mapping):
                harmonix_link = HarmonixLink.from_mapping(harmonix)
            else:  # pragma: no cover - defensive guard
                raise TypeError("harmonix metadata must be a mapping or HarmonixLink")
            payload["harmonix"] = harmonix_link.to_dict()
        signature = self._signature(payload)
        path = self._receipt_path(timestamp, diff_hash)
        payload_with_signature = dict(payload)
        payload_with_signature["signature"] = signature
        path.write_text(json.dumps(payload_with_signature, indent=2, sort_keys=True), encoding="utf-8")
        receipt_payload = dict(payload)
        receipt_payload.pop("harmonix", None)
        return PulseReceipt(path=path, signature=signature, harmonix=harmonix_link, **receipt_payload)

    def verify(self, receipt: PulseReceipt) -> bool:
        payload = receipt.to_dict(include_signature=False)
        expected = self._signature(payload)
        return hmac.compare_digest(expected, receipt.signature)

    def _receipt_from_payload(self, path: Path, data: Mapping[str, object]) -> PulseReceipt:
        harmonix_payload = data.get("harmonix")
        harmonix_link: Optional[HarmonixLink] = None
        if isinstance(harmonix_payload, Mapping):
            try:
                harmonix_link = HarmonixLink.from_mapping(harmonix_payload)
            except (ValueError, TypeError):  # pragma: no cover - ignore malformed metadata
                harmonix_link = None
        return PulseReceipt(
            sha256_of_diff=str(data["sha256_of_diff"]),
            time=str(data["time"]),
            actor=str(data["actor"]),
            rhyme=str(data["rhyme"]),
            result=str(data["result"]),
            seed=str(data["seed"]),
            signature=str(data["signature"]),
            path=path,
            harmonix=harmonix_link,
        )

    def latest(self, limit: int | None = 5) -> List[PulseReceipt]:
        if limit is None:
            limit = 5
        if limit <= 0:
            return []
        files = sorted(self.root.rglob("*.json"))
        receipts: List[PulseReceipt] = []
        for path in reversed(files):
            data = json.loads(path.read_text(encoding="utf-8"))
            receipt = self._receipt_from_payload(path, data)
            receipts.append(receipt)
            if len(receipts) >= limit:
                break
        return receipts

    def iter_receipts(self) -> Iterator[PulseReceipt]:
        """Yield every receipt stored in the ledger in chronological order."""

        if not self.root.exists():
            return

        for path in sorted(self.root.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            yield self._receipt_from_payload(path, data)


class _HarmonixLinkPayload(BaseModel):
    snapshot_id: str
    cycle: int
    timestamp: str
    recursion_hash: str


class _LedgerLogRequest(BaseModel):
    diff_signature: str
    actor: str = "api"
    result: str = "success"
    seed: str
    harmonix: Optional[_HarmonixLinkPayload] = None


def create_app(ledger: PulseLedger | None = None) -> FastAPI:
    ledger = ledger or PulseLedger()
    reporter = PhantomReporter()
    app = FastAPI(title="Echo Pulse Ledger", version="1.0.0")

    @app.post("/pulse/ledger/log")
    def log_entry(request: _LedgerLogRequest) -> dict:
        receipt = ledger.log(
            diff_signature=request.diff_signature,
            actor=request.actor,
            result=request.result,
            seed=request.seed,
            harmonix=request.harmonix.model_dump() if request.harmonix else None,
        )
        return reporter.redact(receipt.to_dict())

    @app.get("/pulse/ledger/latest")
    def latest(limit: int = 5) -> dict:
        receipts = [reporter.redact(r.to_dict()) for r in ledger.latest(limit=limit)]
        return {"receipts": receipts}

    return app


def _cmd_latest(args: argparse.Namespace) -> int:
    ledger = PulseLedger(root=args.root)
    receipts = ledger.latest(limit=args.limit)
    for receipt in receipts:
        print(json.dumps(receipt.to_dict(), indent=2))
    return 0


def build_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("ledger", help="Pulse ledger operations")
    parser.add_argument("--root", type=Path, default=None, help="Ledger root directory")
    parser.add_argument("--limit", type=int, default=5)
    parser.set_defaults(func=_cmd_latest)


__all__ = ["PulseLedger", "PulseReceipt", "create_app", "build_parser"]
