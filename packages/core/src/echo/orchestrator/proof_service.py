"""Verifiable credential orchestration service with proof aggregation support.

This module introduces an orchestrator that can:

* Collect verifiable credentials (VCs) from arbitrary sources.
* Generate aggregated proofs using configurable cryptographic schemes
  (currently simulated zk-SNARK and BBS+ rollups).
* Dispatch the aggregated proofs across multiple blockchains while
  respecting user-managed key custody through signer interfaces for both
  secp256k1 and Ed25519 curves.
* Persist submission state so CLI and SDK consumers can query
  verification status, including partial failures.
* Emit detailed logging and monitoring metadata while writing fallback
  payloads for networks that could not be reached during the initial
  submission.

The cryptographic operations implemented here are intentionally
lightweight placeholders – the actual zero-knowledge or BBS+
construction should be supplied by production integrations. The module
provides a clear interface boundary so the heavy-lifting components can
be swapped in without modifying the orchestration flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Protocol, Sequence
from uuid import uuid4

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _parse_datetime(value: Any) -> datetime:
    """Parse an ISO 8601 datetime string or return ``datetime`` untouched."""

    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if not isinstance(value, str):
        raise ValueError("Expected ISO datetime string or datetime instance")
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    return datetime.fromisoformat(candidate).astimezone(timezone.utc)


def _to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_mapping(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise ValueError(f"Credential field '{field_name}' must be a mapping, got {type(value)!r}")


def _ensure_non_empty_string(value: Any, *, field_name: str) -> str:
    if isinstance(value, str) and value:
        return value
    raise ValueError(f"Credential field '{field_name}' must be a non-empty string")


# ---------------------------------------------------------------------------
# Dataclasses representing credentials, proofs, and dispatch state
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class VerifiableCredential:
    """Normalized representation of a verifiable credential."""

    identifier: str
    issuer: str
    subject: str
    claims: Mapping[str, Any]
    proof: Mapping[str, Any]
    issuance_date: datetime
    expiration_date: datetime | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "VerifiableCredential":
        identifier = _ensure_non_empty_string(payload.get("id"), field_name="id")
        issuer = _ensure_non_empty_string(payload.get("issuer"), field_name="issuer")

        subject_block = payload.get("credentialSubject") or payload.get("subject")
        claims = _ensure_mapping(subject_block, field_name="credentialSubject")
        subject_id = claims.get("id") or claims.get("subject")
        subject = _ensure_non_empty_string(subject_id, field_name="credentialSubject.id")

        proof = _ensure_mapping(payload.get("proof"), field_name="proof")

        issuance_raw = payload.get("issuanceDate") or payload.get("issuance_date")
        issuance_date = _parse_datetime(issuance_raw)

        expiration_raw = payload.get("expirationDate") or payload.get("expiration_date")
        expiration_date = _parse_datetime(expiration_raw) if expiration_raw else None

        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), Mapping) else {}

        return cls(
            identifier=identifier,
            issuer=issuer,
            subject=subject,
            claims=dict(claims),
            proof=dict(proof),
            issuance_date=issuance_date,
            expiration_date=expiration_date,
            metadata=dict(metadata),
        )

    def to_serializable(self) -> Mapping[str, Any]:
        payload: MutableMapping[str, Any] = {
            "id": self.identifier,
            "issuer": self.issuer,
            "credentialSubject": dict(self.claims),
            "proof": dict(self.proof),
            "issuanceDate": _to_iso(self.issuance_date),
        }
        if self.expiration_date:
            payload["expirationDate"] = _to_iso(self.expiration_date)
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(slots=True)
class AggregatedProof:
    """Aggregated proof artifact covering several credentials."""

    identifier: str
    scheme: str
    created_at: datetime
    credential_ids: Sequence[str]
    digest: str
    payload: Mapping[str, Any]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "id": self.identifier,
            "scheme": self.scheme,
            "created_at": _to_iso(self.created_at),
            "credential_ids": list(self.credential_ids),
            "digest": self.digest,
            "payload": dict(self.payload),
        }


@dataclass(slots=True)
class NetworkConfig:
    """Configuration for a blockchain network submission target."""

    name: str
    chain_id: str
    protocol: str = "generic"
    rpc_url: str | None = None

    def to_dict(self) -> Mapping[str, Any]:
        payload: MutableMapping[str, Any] = {
            "name": self.name,
            "chain_id": self.chain_id,
            "protocol": self.protocol,
        }
        if self.rpc_url:
            payload["rpc_url"] = self.rpc_url
        return payload


@dataclass(slots=True)
class DispatchResult:
    """Outcome of dispatching an aggregated proof to a network."""

    network: NetworkConfig
    status: str
    latency_seconds: float
    tx_hash: str | None = None
    error: str | None = None

    def to_dict(self) -> Mapping[str, Any]:
        payload: MutableMapping[str, Any] = {
            "network": self.network.to_dict(),
            "status": self.status,
            "latency_seconds": round(self.latency_seconds, 6),
        }
        if self.tx_hash:
            payload["tx_hash"] = self.tx_hash
        if self.error:
            payload["error"] = self.error
        return payload


@dataclass(slots=True)
class SubmissionStatus:
    """Persistent record of a proof submission."""

    submission_id: str
    aggregated_proof: AggregatedProof
    created_at: datetime
    credential_count: int
    scheme: str
    dispatch_results: Sequence[DispatchResult]
    pending_networks: Sequence[str]
    metrics: Mapping[str, Any]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "submission_id": self.submission_id,
            "aggregated_proof": self.aggregated_proof.to_dict(),
            "created_at": _to_iso(self.created_at),
            "credential_count": self.credential_count,
            "scheme": self.scheme,
            "dispatch_results": [result.to_dict() for result in self.dispatch_results],
            "pending_networks": list(self.pending_networks),
            "metrics": dict(self.metrics),
        }


# ---------------------------------------------------------------------------
# Wallet interfaces – enable user-controlled custody
# ---------------------------------------------------------------------------


class WalletSigner(Protocol):
    """Protocol describing signing capability for blockchain dispatch."""

    algorithm: str

    @property
    def address(self) -> str:  # pragma: no cover - property only
        """Return the address or public identifier for the wallet."""

    def sign(self, payload: bytes) -> bytes:
        """Return a signature over ``payload``."""


def _derive_address(public_key_bytes: bytes, prefix: str) -> str:
    digest = hashlib.sha256(public_key_bytes).hexdigest()
    return f"{prefix}{digest[:40]}"


class Secp256k1Wallet(WalletSigner):
    """Signer implementation for secp256k1 keys.

    The wallet can be instantiated either with an in-memory private key or
    an external signer callable. When using an external signer the caller
    remains in full custody of the secret and only provides signatures on
    demand.
    """

    algorithm = "secp256k1"

    def __init__(
        self,
        *,
        private_key: ec.EllipticCurvePrivateKey | bytes | None = None,
        signer: Callable[[bytes], bytes] | None = None,
        public_key: bytes | None = None,
    ) -> None:
        if signer is None and private_key is None:
            raise ValueError("Provide either a private key or a signer callable")

        self._external_signer = signer
        self._private_key: ec.EllipticCurvePrivateKey | None = None

        if private_key is not None:
            if isinstance(private_key, ec.EllipticCurvePrivateKey):
                self._private_key = private_key
            elif isinstance(private_key, (bytes, bytearray)):
                int_value = int.from_bytes(bytes(private_key), "big")
                self._private_key = ec.derive_private_key(int_value, ec.SECP256K1())
            else:  # pragma: no cover - defensive branch
                raise TypeError("Unsupported private key type for secp256k1 wallet")

            public_key_obj = self._private_key.public_key()
            public_key_bytes = public_key_obj.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
        else:
            if public_key is None:
                raise ValueError("A public key is required when using an external signer")
            public_key_bytes = bytes(public_key)

        self._public_key_bytes = public_key_bytes
        self._address = _derive_address(public_key_bytes, prefix="0x")

    @property
    def address(self) -> str:
        return self._address

    def sign(self, payload: bytes) -> bytes:
        if self._external_signer is not None:
            return self._external_signer(payload)
        assert self._private_key is not None  # For type-checkers
        signature = self._private_key.sign(payload, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(signature)
        return encode_dss_signature(r, s)

    @property
    def public_key_bytes(self) -> bytes:
        return self._public_key_bytes

    @classmethod
    def from_private_key_hex(cls, value: str) -> "Secp256k1Wallet":
        return cls(private_key=bytes.fromhex(value))


class Ed25519Wallet(WalletSigner):
    """Signer implementation for Ed25519 keys."""

    algorithm = "ed25519"

    def __init__(
        self,
        *,
        private_key: ed25519.Ed25519PrivateKey | bytes | None = None,
        signer: Callable[[bytes], bytes] | None = None,
        public_key: bytes | None = None,
    ) -> None:
        if signer is None and private_key is None:
            raise ValueError("Provide either a private key or a signer callable")

        self._external_signer = signer
        self._private_key: ed25519.Ed25519PrivateKey | None = None

        if private_key is not None:
            if isinstance(private_key, ed25519.Ed25519PrivateKey):
                self._private_key = private_key
            elif isinstance(private_key, (bytes, bytearray)):
                self._private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(private_key))
            else:  # pragma: no cover - defensive branch
                raise TypeError("Unsupported private key type for Ed25519 wallet")
            public_key_bytes = self._private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        else:
            if public_key is None:
                raise ValueError("A public key is required when using an external signer")
            public_key_bytes = bytes(public_key)

        self._public_key_bytes = public_key_bytes
        self._address = _derive_address(public_key_bytes, prefix="ed25519:")

    @property
    def address(self) -> str:
        return self._address

    def sign(self, payload: bytes) -> bytes:
        if self._external_signer is not None:
            return self._external_signer(payload)
        assert self._private_key is not None
        return self._private_key.sign(payload)

    @property
    def public_key_bytes(self) -> bytes:
        return self._public_key_bytes

    @classmethod
    def from_private_key_hex(cls, value: str) -> "Ed25519Wallet":
        return cls(private_key=bytes.fromhex(value))


# ---------------------------------------------------------------------------
# Core services
# ---------------------------------------------------------------------------


class CredentialCollector:
    """Normalize raw credential payloads into ``VerifiableCredential`` objects."""

    def collect(self, raw_credentials: Iterable[Mapping[str, Any] | VerifiableCredential]) -> list[VerifiableCredential]:
        credentials: list[VerifiableCredential] = []
        seen: set[str] = set()
        for item in raw_credentials:
            credential = item if isinstance(item, VerifiableCredential) else VerifiableCredential.from_dict(item)
            if credential.identifier in seen:
                continue
            seen.add(credential.identifier)
            credentials.append(credential)
        return credentials


class ProofAggregationError(RuntimeError):
    """Raised when proof aggregation fails."""


class ProofAggregator:
    """Combine several verifiable credentials into a single proof artifact."""

    SUPPORTED_SCHEMES = {"zk-snark", "bbs+"}

    def aggregate(
        self, credentials: Sequence[VerifiableCredential], *, scheme: str = "zk-snark"
    ) -> AggregatedProof:
        if scheme not in self.SUPPORTED_SCHEMES:
            raise ProofAggregationError(f"Unsupported proof scheme '{scheme}'")
        if not credentials:
            raise ProofAggregationError("At least one credential is required to aggregate proofs")

        normalized = [credential.to_serializable() for credential in credentials]
        serialized = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
        digest = hashlib.blake2b(serialized.encode("utf-8"), digest_size=32).hexdigest()

        payload = {
            "scheme": scheme,
            "credential_count": len(credentials),
            "zk_rollup_hint": hashlib.sha256(serialized.encode("utf-8")).hexdigest(),
        }

        aggregated = AggregatedProof(
            identifier=str(uuid4()),
            scheme=scheme,
            created_at=datetime.now(timezone.utc),
            credential_ids=[credential.identifier for credential in credentials],
            digest=digest,
            payload=payload,
        )
        return aggregated


class DispatchError(RuntimeError):
    """Raised when dispatching to a network fails."""


class MultiChainDispatcher:
    """Dispatch aggregated proofs to multiple chains with latency monitoring."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("echo.orchestrator.proof.dispatch")

    def dispatch(
        self,
        proof: AggregatedProof,
        networks: Sequence[NetworkConfig],
        signers: Mapping[str, WalletSigner],
    ) -> list[DispatchResult]:
        results: list[DispatchResult] = []
        payload = json.dumps(proof.to_dict(), sort_keys=True).encode("utf-8")
        for network in networks:
            start = time.perf_counter()
            try:
                signer = signers.get(network.name)
                if signer is None:
                    raise DispatchError(f"No signer registered for network '{network.name}'")
                signature = signer.sign(payload)
                tx_hash = hashlib.sha256(signature + payload).hexdigest()
                latency = time.perf_counter() - start
                self._logger.info(
                    "Dispatched aggregated proof to network",
                    extra={
                        "network": network.name,
                        "tx_hash": tx_hash,
                        "latency_seconds": latency,
                        "algorithm": signer.algorithm,
                    },
                )
                results.append(
                    DispatchResult(
                        network=network,
                        status="submitted",
                        latency_seconds=latency,
                        tx_hash=tx_hash,
                    )
                )
            except Exception as exc:  # pragma: no cover - errors handled uniformly
                latency = time.perf_counter() - start
                self._logger.warning(
                    "Failed to dispatch aggregated proof",
                    exc_info=exc,
                    extra={
                        "network": network.name,
                        "latency_seconds": latency,
                    },
                )
                results.append(
                    DispatchResult(
                        network=network,
                        status="failed",
                        latency_seconds=latency,
                        error=str(exc),
                    )
                )
        return results


# ---------------------------------------------------------------------------
# Proof orchestrator façade
# ---------------------------------------------------------------------------


class ProofOrchestratorService:
    """High-level service that coordinates credential collection and dispatch."""

    def __init__(
        self,
        state_dir: Path | str,
        *,
        collector: CredentialCollector | None = None,
        aggregator: ProofAggregator | None = None,
        dispatcher: MultiChainDispatcher | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._state_dir = Path(state_dir)
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._status_path = self._state_dir / "submissions.jsonl"
        self._pending_dir = self._state_dir / "pending"
        self._pending_dir.mkdir(parents=True, exist_ok=True)

        self._collector = collector or CredentialCollector()
        self._aggregator = aggregator or ProofAggregator()
        self._dispatcher = dispatcher or MultiChainDispatcher()
        self._logger = logger or logging.getLogger("echo.orchestrator.proof.service")

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------
    def collect_credentials(
        self, sources: Iterable[Mapping[str, Any] | VerifiableCredential]
    ) -> list[VerifiableCredential]:
        credentials = self._collector.collect(sources)
        self._logger.debug("Collected credentials", extra={"count": len(credentials)})
        return credentials

    def generate_aggregated_proof(
        self, credentials: Sequence[VerifiableCredential], *, scheme: str = "zk-snark"
    ) -> AggregatedProof:
        proof = self._aggregator.aggregate(credentials, scheme=scheme)
        self._logger.info(
            "Aggregated proof generated",
            extra={
                "proof_id": proof.identifier,
                "scheme": proof.scheme,
                "credential_count": len(credentials),
            },
        )
        return proof

    def submit_proof(
        self,
        raw_credentials: Iterable[Mapping[str, Any] | VerifiableCredential],
        *,
        scheme: str = "zk-snark",
        networks: Sequence[NetworkConfig] | None = None,
        signers: Mapping[str, WalletSigner] | None = None,
    ) -> SubmissionStatus:
        credentials = self.collect_credentials(raw_credentials)
        aggregated_proof = self.generate_aggregated_proof(credentials, scheme=scheme)

        submission_id = str(uuid4())
        dispatch_results: list[DispatchResult] = []
        pending: list[str] = []

        networks = list(networks or [])
        if networks:
            dispatch_results = self._dispatcher.dispatch(
                aggregated_proof,
                networks,
                signers or {},
            )
            pending = [result.network.name for result in dispatch_results if result.status != "submitted"]
            if pending:
                self._logger.warning(
                    "Partial dispatch failure detected",
                    extra={
                        "submission_id": submission_id,
                        "pending_networks": pending,
                    },
                )
                self._persist_fallback(submission_id, aggregated_proof, dispatch_results)

        metrics = {
            "credential_count": len(credentials),
            "pending_networks": pending,
        }

        status = SubmissionStatus(
            submission_id=submission_id,
            aggregated_proof=aggregated_proof,
            created_at=datetime.now(timezone.utc),
            credential_count=len(credentials),
            scheme=scheme,
            dispatch_results=dispatch_results,
            pending_networks=pending,
            metrics=metrics,
        )
        self._append_status(status)
        return status

    # ------------------------------------------------------------------
    # Monitoring and persistence
    # ------------------------------------------------------------------
    def _append_status(self, status: SubmissionStatus) -> None:
        with self._status_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(status.to_dict()) + "\n")

    def _persist_fallback(
        self,
        submission_id: str,
        aggregated_proof: AggregatedProof,
        dispatch_results: Sequence[DispatchResult],
    ) -> None:
        payload = {
            "submission_id": submission_id,
            "aggregated_proof": aggregated_proof.to_dict(),
            "dispatch_results": [result.to_dict() for result in dispatch_results],
        }
        fallback_path = self._pending_dir / f"{submission_id}.json"
        fallback_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._logger.info(
            "Persisted fallback payload",
            extra={"submission_id": submission_id, "path": str(fallback_path)},
        )

    # ------------------------------------------------------------------
    # Query interface used by CLI/SDK
    # ------------------------------------------------------------------
    def query_status(self, submission_id: str) -> Mapping[str, Any] | None:
        for record in self._iter_statuses():
            if record.get("submission_id") == submission_id:
                return record
        return None

    def list_statuses(self, limit: int | None = None) -> list[Mapping[str, Any]]:
        records = list(self._iter_statuses())
        if limit is not None:
            return records[-int(limit) :]
        return records

    def pending_fallbacks(self) -> list[Path]:
        return sorted(self._pending_dir.glob("*.json"))

    def _iter_statuses(self) -> Iterable[Mapping[str, Any]]:
        if not self._status_path.exists():
            return []
        with self._status_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:  # pragma: no cover - corrupted line
                    self._logger.error("Unable to decode submission status line", extra={"line": line})
                    continue


__all__ = [
    "AggregatedProof",
    "CredentialCollector",
    "DispatchError",
    "DispatchResult",
    "Ed25519Wallet",
    "MultiChainDispatcher",
    "NetworkConfig",
    "ProofAggregator",
    "ProofAggregationError",
    "ProofOrchestratorService",
    "Secp256k1Wallet",
    "SubmissionStatus",
    "VerifiableCredential",
    "WalletSigner",
]
