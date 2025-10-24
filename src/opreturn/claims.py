"""Structured OP_RETURN claim parsing and validation helpers."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Mapping, MutableMapping, Optional, Sequence


ISO_FORMATS: Sequence[str] = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return _ensure_utc(value)

    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=timezone.utc)

    if isinstance(value, str):
        for fmt in ISO_FORMATS:
            try:
                parsed = datetime.strptime(value, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - defensive fall-back
            raise ValueError(f"Unsupported datetime value: {value!r}") from exc
        return _ensure_utc(parsed)

    raise TypeError(f"Unsupported block_time type: {type(value)!r}")


def _read_varint(buffer: memoryview, offset: int) -> tuple[int, int]:
    prefix = buffer[offset]
    if prefix < 0xFD:
        return prefix, offset + 1
    if prefix == 0xFD:
        return int.from_bytes(buffer[offset + 1 : offset + 3], "little"), offset + 3
    if prefix == 0xFE:
        return int.from_bytes(buffer[offset + 1 : offset + 5], "little"), offset + 5
    return int.from_bytes(buffer[offset + 1 : offset + 9], "little"), offset + 9


def _iter_vout_from_raw_hex(raw_hex: str) -> Iterator[tuple[int, bytes]]:
    raw_bytes = bytes.fromhex(raw_hex)
    view = memoryview(raw_bytes)
    idx = 4  # version

    # inputs
    input_count, idx = _read_varint(view, idx)
    for _ in range(input_count):
        idx += 32  # previous txid
        idx += 4  # vout
        script_len, idx = _read_varint(view, idx)
        idx += script_len  # scriptSig
        idx += 4  # sequence

    output_count, idx = _read_varint(view, idx)
    for vout_index in range(output_count):
        idx += 8  # value
        script_len, idx = _read_varint(view, idx)
        script = bytes(view[idx : idx + script_len])
        idx += script_len
        yield vout_index, script


def _normalise_payload(text: str) -> str:
    lowered = text.lower()
    markers = (
        "op_return",
        "payload",
        "data",
        "message",
        "claim",
    )
    separator_chars = (":", "-", "|", "=>")

    stripped = text.strip()
    for marker in markers:
        marker_lower = marker.lower()
        if marker_lower in lowered:
            idx = lowered.index(marker_lower)
            suffix = stripped[idx + len(marker) :].lstrip()
            for sep in separator_chars:
                if suffix.startswith(sep):
                    suffix = suffix[len(sep) :].lstrip()
                    break
            if suffix:
                return suffix
    return stripped


def _decode_op_return(script: bytes) -> Optional[str]:
    if not script or script[0] != 0x6A:
        return None

    idx = 1
    if idx >= len(script):
        return None

    opcode = script[idx]
    idx += 1

    if opcode <= 75:
        data_len = opcode
    elif opcode == 0x4C:
        data_len = script[idx]
        idx += 1
    elif opcode == 0x4D:
        data_len = int.from_bytes(script[idx : idx + 2], "little")
        idx += 2
    else:
        return None

    payload = bytes(script[idx : idx + data_len])
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError:
        return payload.hex()


@dataclass(slots=True)
class ParsedClaim:
    txid: str
    vout: int
    block_time: datetime
    op_return_hex: str
    op_return_text: str

    def as_dict(self) -> Mapping[str, object]:
        payload = asdict(self)
        payload["block_time"] = self.block_time.astimezone(timezone.utc).isoformat()
        return payload


def parse_claim_records(transactions: Iterable[Mapping[str, object]]) -> List[ParsedClaim]:
    """Extract OP_RETURN claims from *transactions*.

    Each transaction mapping may provide either a ``vout`` iterable of dictionaries
    (with ``n`` and ``script_hex`` keys) or a ``hex`` attribute containing the raw
    transaction hex string.  Any ``block_time`` representation supported by
    :func:`_parse_datetime` is accepted.
    """

    claims: List[ParsedClaim] = []
    for tx in transactions:
        txid = str(tx.get("txid", ""))
        if not txid:
            raise ValueError("Transaction missing txid")

        block_time = _parse_datetime(tx.get("block_time"))

        vout_entries: List[tuple[int, bytes]] = []
        if "vout" in tx and tx["vout"] is not None:
            for output in tx["vout"]:  # type: ignore[index]
                script_hex = output.get("script_hex") or output.get("scriptPubKey")
                if not script_hex:
                    continue
                try:
                    script_bytes = bytes.fromhex(str(script_hex))
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid script hex in transaction {txid}: {script_hex!r}"
                    ) from exc
                index = int(output.get("n", len(vout_entries)))
                vout_entries.append((index, script_bytes))
        elif "hex" in tx and tx["hex"]:
            vout_entries.extend(_iter_vout_from_raw_hex(str(tx["hex"])))
        else:
            raise ValueError(
                f"Transaction {txid} missing vout information (expected 'vout' list or 'hex')."
            )

        for index, script_bytes in vout_entries:
            payload_text = _decode_op_return(script_bytes)
            if payload_text is None:
                continue

            normalised = _normalise_payload(payload_text)
            claims.append(
                ParsedClaim(
                    txid=txid,
                    vout=index,
                    block_time=block_time,
                    op_return_hex=script_bytes.hex(),
                    op_return_text=normalised,
                )
            )

    return claims


@dataclass(slots=True)
class ValidatedClaim(ParsedClaim):
    claim_status: str
    reason: str
    issuer_tag: str
    confidence: float
    deadline: datetime
    next_step_suggestion: str

    def as_dict(self) -> MutableMapping[str, object]:
        payload = ParsedClaim.as_dict(self)
        payload.update(
            {
                "claim_status": self.claim_status,
                "reason": self.reason,
                "issuer_tag": self.issuer_tag,
                "confidence": round(self.confidence, 3),
                "deadline": self.deadline.astimezone(timezone.utc).isoformat(),
                "next_step_suggestion": self.next_step_suggestion,
            }
        )
        return payload


def _classify_issuer(text: str) -> tuple[str, float]:
    lowered = text.lower()
    markers: tuple[tuple[str, str, float], ...] = (
        ("solomon bros", "solomon_bros", 0.9),
        ("owner of wallet", "self_attested_owner", 0.75),
        ("owner of this wallet", "self_attested_owner", 0.8),
        ("legal representative", "legal_representative", 0.7),
    )

    for marker, tag, confidence in markers:
        if marker in lowered:
            return tag, confidence

    return "kmk142789", 0.4


def _determine_next_step(status: str, confidence: float) -> str:
    if status == "expired":
        return "escalate for allocation"
    if status == "valid" and confidence >= 0.8:
        return "evidence verified"
    if status == "valid":
        return "action (not expired)"
    return "action (not expired)"


def validate_claim_windows(
    records: Iterable[ParsedClaim],
    *,
    as_of: Optional[datetime] = None,
) -> List[ValidatedClaim]:
    """Apply the 90-day inactivity window to the parsed claim *records*."""

    now = _ensure_utc(as_of or datetime.now(timezone.utc))
    validated: List[ValidatedClaim] = []
    for record in records:
        deadline = record.block_time + timedelta(days=90)
        issuer_tag, confidence = _classify_issuer(record.op_return_text)

        if now <= deadline:
            status = "valid"
            remaining = deadline - now
            reason = (
                f"Claim is within the 90-day window ({remaining.days} day(s) remaining)."
            )
        else:
            status = "expired"
            elapsed = now - deadline
            reason = (
                f"Claim window expired {elapsed.days} day(s) ago on {deadline.date()}"
            )

        next_step = _determine_next_step(status, confidence)
        validated.append(
            ValidatedClaim(
                txid=record.txid,
                vout=record.vout,
                block_time=record.block_time,
                op_return_hex=record.op_return_hex,
                op_return_text=record.op_return_text,
                claim_status=status,
                reason=reason,
                issuer_tag=issuer_tag,
                confidence=confidence,
                deadline=deadline,
                next_step_suggestion=next_step,
            )
        )

    return validated


def write_actionable_report(
    records: Iterable[ValidatedClaim],
    *,
    json_path: Path,
    csv_path: Path,
) -> dict[str, str]:
    """Persist *records* to ``json_path`` and ``csv_path``."""

    material = [record.as_dict() for record in records]

    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(material, indent=2), encoding="utf-8")

    fieldnames = [
        "txid",
        "block_time",
        "op_return_text",
        "claim_status",
        "issuer_tag",
        "next_step_suggestion",
    ]

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in material:
            writer.writerow({key: record[key] for key in fieldnames})

    return {"json": str(json_path), "csv": str(csv_path)}


__all__ = [
    "ParsedClaim",
    "ValidatedClaim",
    "parse_claim_records",
    "validate_claim_windows",
    "write_actionable_report",
]

