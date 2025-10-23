"""Utilities for documenting OP_RETURN claim clauses.

The helpers in this module are intentionally **non-executable** with respect to
transaction broadcasting.  They only parse already mined transactions and
generate structured documentation that a reviewer can examine before any
collection attempt is considered.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Literal, Optional


WINDOW_KEY_PHRASE = "if not abandoned make a transaction within 90 days"
SECONDARY_KEY_PHRASE = "solomon bros"

Recommendation = Literal[
    "no_action",
    "requires_claim_review",
    "eligible_for_authorized_collection",
    "not_applicable",
]


BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _b58encode(data: bytes) -> str:
    """Encode *data* using the Bitcoin Base58Check alphabet."""

    # Count leading zero bytes so we can reproduce the "1" prefix semantics.
    zero_prefix = 0
    for byte in data:
        if byte == 0:
            zero_prefix += 1
        else:
            break

    # Convert the payload to an integer and then to base58 digits.
    value = int.from_bytes(data, "big")
    digits: List[str] = []
    while value > 0:
        value, remainder = divmod(value, 58)
        digits.append(BASE58_ALPHABET[remainder])

    prefix = "1" * zero_prefix
    payload = "".join(reversed(digits)) or "1"
    return f"{prefix}{payload}"


def _base58check(version: int, payload: bytes) -> str:
    import hashlib

    body = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(body).digest()).digest()[:4]
    return _b58encode(body + checksum)


def _identify_script(script_hex: str) -> Dict[str, Optional[str]]:
    """Identify standard locking scripts and derive the canonical address."""

    script_hex = script_hex.lower()
    if script_hex.startswith("76a914") and script_hex.endswith("88ac"):
        # Pay-to-PubKey-Hash: OP_DUP OP_HASH160 <20-byte hash> OP_EQUALVERIFY OP_CHECKSIG
        hash_hex = script_hex[6:-4]
        return {
            "script_type": "p2pkh",
            "address": _base58check(0, bytes.fromhex(hash_hex)),
        }

    if script_hex.startswith("a914") and script_hex.endswith("87"):
        # Pay-to-Script-Hash
        hash_hex = script_hex[4:-2]
        return {
            "script_type": "p2sh",
            "address": _base58check(5, bytes.fromhex(hash_hex)),
        }

    return {"script_type": "unknown", "address": None}


def _decode_op_return(script_hex: str) -> Optional[str]:
    script_bytes = bytes.fromhex(script_hex)
    if not script_bytes or script_bytes[0] != 0x6A:  # OP_RETURN
        return None

    idx = 1
    if idx >= len(script_bytes):
        return None

    op = script_bytes[idx]
    idx += 1

    if op <= 75:
        data_len = op
    elif op == 0x4C:  # OP_PUSHDATA1
        if idx >= len(script_bytes):
            return None
        data_len = script_bytes[idx]
        idx += 1
    elif op == 0x4D:  # OP_PUSHDATA2
        if idx + 1 >= len(script_bytes):
            return None
        data_len = int.from_bytes(script_bytes[idx : idx + 2], "little")
        idx += 2
    else:
        # Anything more exotic is out-of-scope for this checklist helper.
        return None

    data = script_bytes[idx : idx + data_len]
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.hex()


@dataclass(slots=True)
class CompanionOutput:
    index: int
    script_type: str
    address: Optional[str]
    raw_script: str
    value_sats: Optional[int] = None


@dataclass(slots=True)
class ClaimEvidence:
    txid: str
    block_time: datetime
    op_return_message: str
    inactivity_window_days: Optional[int]
    inactivity_window_end: Optional[datetime]
    clause_detected: bool
    clause_variant: Optional[str]
    derived_entities: List[CompanionOutput] = field(default_factory=list)
    recommendation: Recommendation = "not_applicable"
    verification_notes: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["block_time"] = self.block_time.isoformat()
        if self.inactivity_window_end is not None:
            payload["inactivity_window_end"] = self.inactivity_window_end.isoformat()
        return payload


def _detect_clause(message: str) -> Dict[str, Optional[object]]:
    normalized = message.lower()
    matches_window = WINDOW_KEY_PHRASE in normalized
    matches_secondary = SECONDARY_KEY_PHRASE in normalized
    inactivity_window_days = 90 if matches_window else None
    clause_variant = None
    if matches_window and matches_secondary:
        clause_variant = "solomon_bros_window"
    elif matches_window:
        clause_variant = "generic_90_day_window"
    elif matches_secondary:
        clause_variant = "solomon_bros_reference"
    return {
        "clause_detected": matches_window or matches_secondary,
        "clause_variant": clause_variant,
        "inactivity_window_days": inactivity_window_days,
    }


def evaluate_recommendation(
    clause_detected: bool,
    inactivity_window_end: Optional[datetime],
    as_of: datetime,
) -> Recommendation:
    if not clause_detected:
        return "not_applicable"

    if inactivity_window_end is None:
        return "requires_claim_review"

    if as_of >= inactivity_window_end:
        return "requires_claim_review"

    return "no_action"


def collect_claim_evidence(
    transactions: Iterable[Dict[str, object]],
    *,
    as_of: Optional[datetime] = None,
) -> List[ClaimEvidence]:
    """Extract OP_RETURN evidence from an iterable of transaction dictionaries.

    Each transaction dictionary is expected to provide:

    - ``txid`` (str)
    - ``block_time`` (datetime or UNIX timestamp integer)
    - ``vout`` (list of output dictionaries with ``n`` and ``script_hex`` keys)
    - Optional ``value_sats`` per output
    """

    evidence: List[ClaimEvidence] = []
    as_of = as_of or datetime.now(timezone.utc)

    for tx in transactions:
        txid = str(tx["txid"])
        block_time_raw = tx["block_time"]
        if isinstance(block_time_raw, datetime):
            block_time = block_time_raw.astimezone(timezone.utc)
        else:
            block_time = datetime.fromtimestamp(int(block_time_raw), tz=timezone.utc)

        vout_iter = tx.get("vout", [])
        companion_outputs: List[CompanionOutput] = []
        op_return_messages: List[str] = []

        for output in vout_iter:
            script_hex = str(output.get("script_hex") or output.get("scriptPubKey", ""))
            decoded = _decode_op_return(script_hex)
            if decoded is None:
                details = _identify_script(script_hex)
                companion_outputs.append(
                    CompanionOutput(
                        index=int(output.get("n", 0)),
                        script_type=details["script_type"],
                        address=details["address"],
                        raw_script=script_hex,
                        value_sats=output.get("value_sats"),
                    )
                )
            else:
                op_return_messages.append(decoded)

        for message in op_return_messages:
            clause_metadata = _detect_clause(message)
            inactivity_window_end = None
            if clause_metadata["inactivity_window_days"] is not None:
                inactivity_window_end = block_time + timedelta(
                    days=clause_metadata["inactivity_window_days"]
                )

            recommendation = evaluate_recommendation(
                clause_metadata["clause_detected"], inactivity_window_end, as_of
            )

            evidence.append(
                ClaimEvidence(
                    txid=txid,
                    block_time=block_time,
                    op_return_message=message,
                    inactivity_window_days=clause_metadata["inactivity_window_days"],
                    inactivity_window_end=inactivity_window_end,
                    clause_detected=clause_metadata["clause_detected"],
                    clause_variant=clause_metadata["clause_variant"],
                    derived_entities=[*companion_outputs],
                    recommendation=recommendation,
                    verification_notes=[],
                )
            )

    return evidence


def assemble_report(
    *,
    claimant: str,
    generated_at: Optional[datetime] = None,
    evidence: Iterable[ClaimEvidence],
) -> Dict[str, object]:
    """Produce a JSON-serialisable report skeleton."""

    generated_at = generated_at or datetime.now(timezone.utc)
    material = [item.as_dict() for item in evidence]
    return {
        "summary": {
            "claimant": claimant,
            "generated_at": generated_at.astimezone(timezone.utc).isoformat(),
            "count": len(material),
            "window_phrase": WINDOW_KEY_PHRASE,
            "secondary_phrase": SECONDARY_KEY_PHRASE,
        },
        "records": material,
        "review_checklist": [
            "Confirm OP_RETURN payload text matches archived evidence.",
            "Validate inactivity window and verify calendar calculations.",
            "Confirm claimant authority documentation is complete.",
            "Ensure legal/ethical review approves any downstream action.",
        ],
    }

