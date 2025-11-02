"""Proof-of-Computation utilities for verifying puzzles and recording attestations."""

from __future__ import annotations

import hashlib
import json
import re
import warnings
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from web3.contract.contract import Contract
from web3.exceptions import ContractLogicError

try:  # pragma: no cover - optional dependency for puzzle loading
    from echo_puzzle_lab.data import load_records
except Exception:  # pragma: no cover - defensive fallback
    load_records = None  # type: ignore[assignment]

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _discover_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "puzzle_solutions").exists() and (candidate / "echo_map.json").exists():
            return candidate
    return current.parent


_REPO_ROOT = _discover_repo_root()
_DEFAULT_LEDGER_PATH = _REPO_ROOT / "pulse_dashboard" / "data" / "proof_of_computation.json"


class PuzzleVerificationError(RuntimeError):
    """Raised when a puzzle solution cannot be validated."""


@dataclass(slots=True)
class PuzzleProof:
    """Intermediate proof object produced after verifying a puzzle solution."""

    puzzle_id: int
    hash160: str
    base58check: str
    digest: str
    timestamp: datetime
    solution_path: Path
    record_address: str
    metadata: Dict[str, str]


@dataclass(slots=True)
class ProofSubmission:
    """Result returned once a proof has been recorded on-chain or via stub."""

    puzzle_id: int
    hash160: str
    base58check: str
    digest: str
    signature: str
    tx_hash: str
    recorded_at: datetime
    signer: str
    chain_id: Optional[int]
    contract_address: Optional[str]
    metadata: Dict[str, str]


class ProofRecorder(Protocol):
    """Protocol implemented by recorders that persist proofs to a ledger."""

    def record(self, proof: PuzzleProof) -> ProofSubmission:
        ...


class PuzzleProofVerifier:
    """Verify puzzle solutions and prepare proof payloads."""

    _HASH_RE = re.compile(r"hash160[^`]*`([0-9a-f]{40})`", re.IGNORECASE)
    _VERSION_RE = re.compile(r"version byte[^`]*`0x([0-9a-f]{2})`", re.IGNORECASE)
    _BASE58_INLINE_RE = re.compile(
        r"Base58Check[^`]*`([123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{26,})`",
        re.IGNORECASE,
    )
    _BASE58_BLOCK_RE = re.compile(
        r"```(?:base58check)?\s*\n?([123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]+)\s*```",
        re.IGNORECASE,
    )

    def __init__(self, *, project_root: Path | str | None = None) -> None:
        self._root = Path(project_root or _REPO_ROOT)
        self._records: Optional[dict[int, dict[str, str]]] = None

    # ------------------------------------------------------------------
    def verify(self, puzzle_id: int, *, solution_path: Path | None = None) -> PuzzleProof:
        """Validate the solution for ``puzzle_id`` and return a proof payload."""

        record = self._get_record(puzzle_id)
        if record is None:
            raise PuzzleVerificationError(f"Puzzle {puzzle_id} is not present in echo_map.json")

        candidate_path = solution_path or self._default_solution_path(puzzle_id)
        if not candidate_path.exists():
            raise PuzzleVerificationError(f"Solution file not found for puzzle {puzzle_id}: {candidate_path}")

        text = candidate_path.read_text(encoding="utf-8")
        hash160 = self._extract_hash160(text)
        if hash160 is None:
            raise PuzzleVerificationError(f"Puzzle {puzzle_id} solution does not describe a hash160")
        if hash160.lower() != record["hash160"].lower():
            raise PuzzleVerificationError(
                f"Puzzle {puzzle_id} hash160 mismatch: {hash160} != {record['hash160']}"
            )

        version_hint = self._extract_version(text)
        derived = self._derive_base58(hash160, version_hint, record["address"])
        provided_address = self._extract_base58(text) or ""
        if provided_address and provided_address != record["address"]:
            raise PuzzleVerificationError(
                f"Puzzle {puzzle_id} solution address mismatch: {provided_address} != {record['address']}"
            )
        if derived != record["address"]:
            raise PuzzleVerificationError(
                f"Puzzle {puzzle_id} recomputed address mismatch: {derived} != {record['address']}"
            )

        timestamp = datetime.now(timezone.utc)
        digest = hashlib.sha256(f"{puzzle_id}:{hash160}:{derived}".encode("utf-8")).hexdigest()

        metadata = {
            "solution_path": str(candidate_path),
            "record_hash160": record["hash160"],
            "record_address": record["address"],
        }
        if version_hint is not None:
            metadata["version_byte"] = f"0x{version_hint:02x}"
        if provided_address:
            metadata["provided_address"] = provided_address

        return PuzzleProof(
            puzzle_id=puzzle_id,
            hash160=hash160.lower(),
            base58check=derived,
            digest=digest,
            timestamp=timestamp,
            solution_path=candidate_path,
            record_address=record["address"],
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    def _get_record(self, puzzle_id: int) -> Optional[dict[str, str]]:
        if self._records is None:
            self._records = {}
            if load_records is None:
                raise PuzzleVerificationError("echo_puzzle_lab is not available in this environment")
            for record in load_records():
                self._records[int(record.puzzle)] = {
                    "hash160": str(record.hash160),
                    "address": str(record.address),
                }
        return self._records.get(puzzle_id)

    def _default_solution_path(self, puzzle_id: int) -> Path:
        return self._root / "puzzle_solutions" / f"puzzle_{puzzle_id}.md"

    @classmethod
    def _extract_hash160(cls, text: str) -> Optional[str]:
        match = cls._HASH_RE.search(text)
        if match:
            return match.group(1).lower()
        return None

    @classmethod
    def _extract_version(cls, text: str) -> Optional[int]:
        match = cls._VERSION_RE.search(text)
        if match:
            return int(match.group(1), 16)
        return None

    @classmethod
    def _extract_base58(cls, text: str) -> Optional[str]:
        inline = cls._BASE58_INLINE_RE.search(text)
        if inline:
            return inline.group(1).strip()
        block = cls._BASE58_BLOCK_RE.search(text)
        if block:
            return block.group(1).strip()
        return None

    @staticmethod
    def _derive_base58(hash160_hex: str, version_hint: Optional[int], record_address: str) -> str:
        payload = PuzzleProofVerifier._decode_base58(record_address)
        if len(payload) < 5:
            raise PuzzleVerificationError("Unable to decode record address for payload derivation")
        record_version = payload[0]
        version = version_hint if version_hint is not None else record_version
        data = bytes([version]) + bytes.fromhex(hash160_hex)
        return PuzzleProofVerifier._encode_base58_check(data)

    @staticmethod
    def _encode_base58_check(data: bytes) -> str:
        checksum = hashlib.sha256(hashlib.sha256(data).digest()).digest()[:4]
        value = data + checksum
        num = int.from_bytes(value, "big")
        encoded = ""
        while num:
            num, remainder = divmod(num, 58)
            encoded = ALPHABET[remainder] + encoded
        leading = len(value) - len(value.lstrip(b"\x00"))
        return "1" * leading + encoded

    @staticmethod
    def _decode_base58(address: str) -> bytes:
        num = 0
        for char in address:
            num = num * 58 + ALPHABET.index(char)
        combined = num.to_bytes((num.bit_length() + 7) // 8, "big") or b"\x00"
        leading = len(address) - len(address.lstrip("1"))
        return b"\x00" * leading + combined


class PolygonProofRecorder:
    """Record puzzle proofs on Polygon testnet or via a deterministic stub."""

    def __init__(
        self,
        private_key: str,
        *,
        provider_uri: str | None = None,
        contract_address: str | None = None,
        contract_abi: Iterable[dict] | None = None,
        chain_id: int | None = None,
        ledger_path: Path | str | None = None,
        wait_for_receipt: bool = False,
        receipt_timeout: int = 120,
    ) -> None:
        if not private_key:
            raise ValueError("A private key is required to record proofs")
        self._account = Account.from_key(private_key)
        self._web3: Optional[Web3] = None
        self._contract: Optional[Contract] = None
        self._chain_id = chain_id
        self._wait = wait_for_receipt
        self._timeout = receipt_timeout
        self._contract_address = contract_address
        if provider_uri:
            self._web3 = Web3(Web3.HTTPProvider(provider_uri))
            if self._web3.is_connected():  # pragma: no branch - network conditional
                try:
                    remote_chain_id = self._web3.eth.chain_id
                except Exception:  # pragma: no cover - provider quirks
                    remote_chain_id = None
                if self._chain_id is None and remote_chain_id is not None:
                    self._chain_id = remote_chain_id
                if contract_address and contract_abi is not None:
                    self._contract = self._web3.eth.contract(
                        address=Web3.to_checksum_address(contract_address), abi=list(contract_abi)
                    )
        self._ledger_path = Path(ledger_path or _DEFAULT_LEDGER_PATH)
        self._ledger_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def record(self, proof: PuzzleProof) -> ProofSubmission:
        """Record ``proof`` on-chain or using a deterministic local ledger."""

        message = encode_defunct(hexstr=proof.digest)
        signed = self._account.sign_message(message)
        signature = Web3.to_hex(signed.signature)

        recorded_at = datetime.now(timezone.utc)
        tx_hash, mode = self._submit_transaction(proof, signature)

        entry = {
            "puzzle": proof.puzzle_id,
            "hash160": proof.hash160,
            "base58check": proof.base58check,
            "digest": proof.digest,
            "signature": signature,
            "recorded_at": recorded_at.isoformat(),
            "signer": self._account.address,
            "tx_hash": tx_hash,
            "chain_id": self._chain_id,
            "contract_address": self._contract_address,
            "metadata": {"mode": mode, **proof.metadata},
        }
        self._persist_entry(entry)

        return ProofSubmission(
            puzzle_id=proof.puzzle_id,
            hash160=proof.hash160,
            base58check=proof.base58check,
            digest=proof.digest,
            signature=signature,
            tx_hash=tx_hash,
            recorded_at=recorded_at,
            signer=self._account.address,
            chain_id=self._chain_id,
            contract_address=self._contract_address,
            metadata={"mode": mode, **proof.metadata},
        )

    # ------------------------------------------------------------------
    def _submit_transaction(self, proof: PuzzleProof, signature: str) -> tuple[str, str]:
        if not self._contract or not self._web3:
            simulated = self._simulate_tx_hash(proof.digest, signature)
            if self._chain_id is None:
                self._chain_id = 80002  # Polygon Amoy testnet default
            return simulated, "stub"

        try:  # pragma: no branch - attempt live submission
            nonce = self._web3.eth.get_transaction_count(self._account.address)
            txn = self._contract.functions.recordProof(
                proof.hash160,
                proof.base58check,
                proof.digest,
                signature,
            ).build_transaction(
                {
                    "from": self._account.address,
                    "nonce": nonce,
                    "gas": 300_000,
                    "gasPrice": self._web3.eth.gas_price,
                    "chainId": self._chain_id or self._web3.eth.chain_id,
                }
            )
            signed_tx = self._account.sign_transaction(txn)
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            if self._wait:
                self._web3.eth.wait_for_transaction_receipt(tx_hash, timeout=self._timeout)
            return Web3.to_hex(tx_hash), "contract"
        except (ContractLogicError, ValueError, TimeoutError) as exc:
            warnings.warn(f"Proof submission fell back to stub mode: {exc}")
        except Exception as exc:  # pragma: no cover - defensive fallback
            warnings.warn(f"Unexpected submission error: {exc}")

        simulated = self._simulate_tx_hash(proof.digest, signature)
        if self._chain_id is None:
            self._chain_id = self._web3.eth.chain_id if self._web3 else 80002
        return simulated, "stub"

    @staticmethod
    def _simulate_tx_hash(digest: str, signature: str) -> str:
        payload = f"{digest}:{signature}".encode("utf-8")
        return "0x" + hashlib.sha256(payload).hexdigest()

    def _persist_entry(self, entry: Dict[str, object]) -> None:
        existing = load_proof_ledger(self._ledger_path)
        filtered = [item for item in existing if int(item.get("puzzle", -1)) != entry["puzzle"]]
        filtered.append(entry)
        filtered.sort(key=lambda item: item.get("recorded_at", ""), reverse=True)
        self._ledger_path.write_text(json.dumps(filtered, indent=2, sort_keys=True), encoding="utf-8")


class ProofOfComputationService:
    """High-level service tying verification and recording together."""

    def __init__(self, verifier: PuzzleProofVerifier, recorder: ProofRecorder) -> None:
        self._verifier = verifier
        self._recorder = recorder

    def process_puzzle(self, puzzle_id: int, *, solution_path: Path | None = None) -> ProofSubmission:
        proof = self._verifier.verify(puzzle_id, solution_path=solution_path)
        return self._recorder.record(proof)


def load_proof_ledger(path: Path | str | None = None) -> List[Dict[str, object]]:
    """Load recorded proof entries for dashboard and analytics consumption."""

    target = Path(path or _DEFAULT_LEDGER_PATH)
    if not target.exists():
        return []
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    cleaned: List[Dict[str, object]] = []
    for item in data:
        if isinstance(item, dict):
            cleaned.append(dict(item))
    cleaned.sort(key=lambda item: item.get("recorded_at", ""), reverse=True)
    return cleaned


__all__ = [
    "PuzzleProofVerifier",
    "PuzzleProof",
    "ProofSubmission",
    "ProofRecorder",
    "PolygonProofRecorder",
    "ProofOfComputationService",
    "PuzzleVerificationError",
    "load_proof_ledger",
]
