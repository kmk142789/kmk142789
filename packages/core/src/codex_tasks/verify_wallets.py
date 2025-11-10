"""Utilities for verifying sovereign treasury wallets."""

from __future__ import annotations

import csv
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3


REPO_ROOT = Path(__file__).resolve().parents[4]
METADATA_DIR = REPO_ROOT / "treasury" / "sources" / "wallets"
DEFAULT_RPC_ENDPOINT = "https://cloudflare-eth.com"
MESSAGE_TEMPLATE = (
    "LittleFootsteps Sovereign Trust Wallet Verification\n"
    "Address: {address}\n"
    "I, {steward}, attest I control the private key for this address.\n"
    "Nonce: {nonce}\n"
    "Purpose: Add wallet as authorized funding pipeline to LittleFootsteps Treasury.\n"
    "Sign this exact message with the wallet private key and paste signature here."
)


@dataclass(slots=True)
class WalletCandidate:
    """Represents a wallet awaiting signature verification."""

    address: str
    signature: str
    steward: str
    nonce: str
    chain: str
    notes: str
    message: str | None


@dataclass(slots=True)
class WalletResult:
    """Outcome of a verification attempt."""

    address: str
    chain: str
    signature: str
    status: str
    steward: str
    nonce: str
    notes: str
    message: str | None
    reason: str | None
    balance_eth: str | None
    balance_display: str | None
    balance_usd: float | None
    last_active_block: int | None
    metadata_file: str | None
    signature_hash: str | None
    verified_at: str

    def as_payload(self) -> dict[str, object]:
        return {
            "address": self.address,
            "chain": self.chain,
            "status": self.status,
            "signature": self.signature,
            "steward": self.steward,
            "nonce": self.nonce,
            "notes": self.notes,
            "message": self.message,
            "reason": self.reason,
            "balance": self.balance_display,
            "balance_eth": self.balance_eth,
            "balance_usd": self.balance_usd,
            "last_active_block": self.last_active_block,
            "metadata_file": self.metadata_file,
            "time": self.verified_at,
            "signature_hash": self.signature_hash,
        }


@dataclass(slots=True)
class VerifyWalletsOptions:
    """Command options for the ``verify_wallets`` task."""

    input_path: Path
    batch_size: int
    mode: str
    workers: int
    retry: int
    throttle_seconds: float | None
    output_path: Path | None = None


@dataclass(slots=True)
class BalanceSnapshot:
    """Simplified balance snapshot for a wallet."""

    balance_eth: Decimal | None
    balance_usd: Decimal | None
    block_number: int | None


class BalanceFetcher:
    """Fetch Ethereum balances via a JSON-RPC endpoint."""

    def __init__(self, endpoint: str = DEFAULT_RPC_ENDPOINT) -> None:
        self._endpoint = endpoint
        self._web3: Web3 | None = None
        self._cache: dict[str, BalanceSnapshot] = {}

    def _ensure_client(self) -> Web3:
        if self._web3 is None:
            self._web3 = Web3(Web3.HTTPProvider(self._endpoint, request_kwargs={"timeout": 10}))
        return self._web3

    def fetch(self, address: str) -> BalanceSnapshot:
        cached = self._cache.get(address)
        if cached is not None:
            return cached

        try:
            web3 = self._ensure_client()
            balance_wei = web3.eth.get_balance(address)
            block_number = web3.eth.block_number
            balance_eth = Decimal(web3.from_wei(balance_wei, "ether"))
            snapshot = BalanceSnapshot(balance_eth=balance_eth, balance_usd=None, block_number=block_number)
        except Exception:  # pragma: no cover - network failures fall back to None
            snapshot = BalanceSnapshot(balance_eth=None, balance_usd=None, block_number=None)

        self._cache[address] = snapshot
        return snapshot


def _parse_candidates(path: Path) -> list[WalletCandidate]:
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        candidates: list[WalletCandidate] = []
        for row in reader:
            address = (row.get("address") or "").strip()
            signature = (row.get("signature") or "").strip()
            steward = (row.get("steward") or "LittleFootsteps Steward").strip()
            nonce = (row.get("nonce") or "").strip()
            chain = (row.get("chain") or "ethereum").strip().lower() or "ethereum"
            notes = (row.get("notes") or "owner_claimed").strip()
            message = (row.get("message") or None)
            candidates.append(
                WalletCandidate(
                    address=address,
                    signature=signature,
                    steward=steward,
                    nonce=nonce,
                    chain=chain,
                    notes=notes,
                    message=message.strip() if isinstance(message, str) and message.strip() else None,
                )
            )
    return candidates


def _message_for(candidate: WalletCandidate) -> str | None:
    if candidate.message:
        return candidate.message
    if not candidate.address or not candidate.nonce:
        return None
    steward = candidate.steward or "LittleFootsteps Steward"
    return MESSAGE_TEMPLATE.format(address=candidate.address, steward=steward, nonce=candidate.nonce)


def _sha256_hex(signature: str) -> str:
    clean = signature[2:] if signature.startswith("0x") else signature
    data = bytes.fromhex(clean)
    return hashlib.sha256(data).hexdigest()


def _format_balance(value: Decimal | None) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    quantized = value.quantize(Decimal("0.000000"), rounding=ROUND_DOWN)
    return f"{quantized:f} ETH", f"{quantized:f}"


def _metadata_path(address: str) -> Path:
    return METADATA_DIR / f"{address.lower()}.md"


def _write_metadata(result: WalletResult, message: str) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_path = _metadata_path(result.address)
    content = [
        "# LittleFootsteps Sovereign Trust Wallet Verification",
        "",
        f"- **Address:** {result.address}",
        f"- **Chain:** {result.chain}",
        f"- **Status:** {result.status}",
        f"- **Verified at:** {result.verified_at}",
        f"- **Steward:** {result.steward}",
        f"- **Nonce:** {result.nonce}",
        f"- **Signature:** {result.signature}",
        f"- **Signature hash:** {result.signature_hash or '—'}",
        f"- **Mode:** verify-signatures-only",
        f"- **Notes:** {result.notes or '—'}",
        "",
        "## Verification Message",
        "",
        "```",
        message,
        "```",
    ]
    if result.balance_display:
        content.insert(6, f"- **Balance:** {result.balance_display}")
    metadata_path.write_text("\n".join(content) + "\n", encoding="utf-8")


def _relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _next_batch_path() -> Path:
    existing = sorted(REPO_ROOT.glob("verified_wallets_batch_*.json"))
    if not existing:
        return REPO_ROOT / "verified_wallets_batch_01.json"
    last = existing[-1].stem.rsplit("_", 1)[-1]
    try:
        next_idx = int(last) + 1
    except ValueError:
        next_idx = len(existing) + 1
    return REPO_ROOT / f"verified_wallets_batch_{next_idx:02d}.json"


def run_verify_wallets(
    options: VerifyWalletsOptions,
    *,
    balance_fetcher: BalanceFetcher | None = None,
) -> dict[str, object]:
    if options.mode != "verify-signatures-only":
        raise ValueError("unsupported mode; expected 'verify-signatures-only'")

    candidates = _parse_candidates(options.input_path)
    total = len(candidates)
    if total == 0:
        raise ValueError("input list is empty")

    fetcher = balance_fetcher or BalanceFetcher()
    throttle = options.throttle_seconds or 0.0
    now = datetime.now(timezone.utc)
    batch_path = options.output_path or _next_batch_path()
    batch_id = batch_path.stem.rsplit("_", 1)[-1]

    results: list[WalletResult] = []
    verified = 0
    unverified = 0
    skipped = 0

    for index, candidate in enumerate(candidates, start=1):
        message = _message_for(candidate)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        balance_display: str | None = None
        balance_eth: str | None = None
        balance_usd_value: float | None = None
        last_block: int | None = None
        metadata_file: str | None = None
        signature_hash: str | None = None
        reason: str | None = None

        if not candidate.address or not candidate.signature:
            status = "SKIPPED"
            reason = "missing address or signature"
        elif message is None:
            status = "SKIPPED"
            reason = "insufficient data to build message"
        else:
            try:
                recovered = Account.recover_message(encode_defunct(text=message), signature=candidate.signature)
            except Exception as exc:
                status = "UNVERIFIED"
                reason = str(exc)
            else:
                if recovered.lower() == candidate.address.lower():
                    status = "VERIFIED"
                    signature_hash = _sha256_hex(candidate.signature)
                    snapshot = fetcher.fetch(candidate.address)
                    display, value_str = _format_balance(snapshot.balance_eth)
                    balance_display = display
                    balance_eth = value_str
                    balance_usd_value = (
                        float(snapshot.balance_usd) if snapshot.balance_usd is not None else None
                    )
                    last_block = snapshot.block_number
                    metadata_path = _metadata_path(candidate.address)
                    _write_metadata(
                        WalletResult(
                            address=candidate.address,
                            chain=candidate.chain,
                            signature=candidate.signature,
                            status=status,
                            steward=candidate.steward,
                            nonce=candidate.nonce,
                            notes=candidate.notes,
                            message=message,
                            reason=reason,
                            balance_eth=balance_eth,
                            balance_display=balance_display,
                            balance_usd=balance_usd_value,
                            last_active_block=snapshot.block_number,
                            metadata_file=None,
                            signature_hash=signature_hash,
                            verified_at=timestamp,
                        ),
                        message,
                    )
                    metadata_file = _relative_path(metadata_path)
                else:
                    status = "UNVERIFIED"
                    reason = "signature does not match address"

        if status == "VERIFIED":
            verified += 1
        elif status == "UNVERIFIED":
            unverified += 1
        else:
            skipped += 1

        result = WalletResult(
            address=candidate.address,
            chain=candidate.chain,
            signature=candidate.signature,
            status=status,
            steward=candidate.steward,
            nonce=candidate.nonce,
            notes=candidate.notes,
            message=message,
            reason=reason,
            balance_eth=balance_eth,
            balance_display=balance_display,
            balance_usd=balance_usd_value,
            last_active_block=last_block,
            metadata_file=metadata_file,
            signature_hash=signature_hash,
            verified_at=timestamp,
        )
        results.append(result)

        print(f"[{index}/{total}] {candidate.address or '—'} → {status}")
        if throttle and status == "VERIFIED":
            time.sleep(throttle)

    payload = {
        "batch_id": batch_id,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input": _relative_path(options.input_path),
        "mode": options.mode,
        "stats": {
            "total": total,
            "verified": verified,
            "unverified": unverified,
            "skipped": skipped,
        },
        "wallets": [item.as_payload() for item in results],
    }

    batch_path.parent.mkdir(parents=True, exist_ok=True)
    batch_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Verification results written → {_relative_path(batch_path)}")
    return payload


__all__ = [
    "BalanceFetcher",
    "BalanceSnapshot",
    "VerifyWalletsOptions",
    "run_verify_wallets",
]

