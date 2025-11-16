"""Zero-knowledge privacy orchestration layer for Echo."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import secrets
from typing import Any, Mapping, Sequence

__all__ = [
    "ProofClaim",
    "ProofResult",
    "ProofCircuit",
    "ProofBackend",
    "ProofVerifier",
    "KeyOwnershipCircuit",
    "CapabilityCircuit",
    "EventCommitmentCircuit",
    "HashCommitmentBackend",
    "ZeroKnowledgePrivacyLayer",
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ProofClaim:
    """Structured claim describing what should be proven."""

    claim_id: str
    claim_type: str
    subject: str
    statement: Mapping[str, Any]
    private_inputs: Mapping[str, Any] = field(default_factory=dict)
    capability: str | None = None
    context: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:  # pragma: no cover - trivial setter
        self.statement = dict(self.statement)
        self.private_inputs = dict(self.private_inputs)
        self.context = dict(self.context)

    @classmethod
    def key_ownership(
        cls,
        *,
        claim_id: str,
        subject: str,
        public_key: str,
        private_material: str,
    ) -> "ProofClaim":
        return cls(
            claim_id=claim_id,
            claim_type="key_ownership",
            subject=subject,
            statement={"public_key": public_key},
            private_inputs={"key_material": private_material},
            capability="signing",
        )

    @classmethod
    def capability_claim(
        cls,
        *,
        claim_id: str,
        subject: str,
        action: str,
        policy_digest: str,
        capability_token: str,
    ) -> "ProofClaim":
        return cls(
            claim_id=claim_id,
            claim_type="capability",
            subject=subject,
            statement={"action": action, "policy_digest": policy_digest},
            private_inputs={"capability_token": capability_token},
            capability=action,
        )

    @classmethod
    def event_commitment(
        cls,
        *,
        claim_id: str,
        subject: str,
        event_hash: str,
        payload_secret: str,
    ) -> "ProofClaim":
        return cls(
            claim_id=claim_id,
            claim_type="event_commitment",
            subject=subject,
            statement={"event_hash": event_hash},
            private_inputs={"payload_secret": payload_secret},
        )


@dataclass(slots=True)
class ProofResult:
    """Outcome of a zero-knowledge claim."""

    claim_id: str
    claim_type: str
    subject: str
    circuit: str
    backend: str
    commitment: str
    proof: Mapping[str, Any]
    public_statement: Mapping[str, Any]
    verified: bool
    generated_at: str
    capability: str | None = None
    diagnostics: Mapping[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract interfaces
# ---------------------------------------------------------------------------


class ProofCircuit(ABC):
    """Abstract circuit definition for privacy-preserving proofs."""

    def __init__(
        self,
        name: str,
        description: str,
        *,
        statement_keys: Sequence[str] | None = None,
        private_keys: Sequence[str] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self._statement_keys = tuple(statement_keys or ())
        self._private_keys = tuple(private_keys or ())

    def validate(self, claim: ProofClaim) -> None:
        missing_statement = [key for key in self._statement_keys if key not in claim.statement]
        missing_private = [key for key in self._private_keys if key not in claim.private_inputs]
        if missing_statement:
            raise ValueError(f"claim missing statement keys: {', '.join(missing_statement)}")
        if missing_private:
            raise ValueError(f"claim missing private inputs: {', '.join(missing_private)}")

    def public_inputs(self, claim: ProofClaim) -> Mapping[str, Any]:
        return {key: claim.statement[key] for key in self._statement_keys if key in claim.statement}

    def secret_inputs(self, claim: ProofClaim) -> Mapping[str, Any]:
        return {key: claim.private_inputs[key] for key in self._private_keys if key in claim.private_inputs}


class ProofBackend(ABC):
    """Pluggable backend capable of generating and verifying proofs."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def supports(self, circuit: ProofCircuit) -> bool:
        """Return ``True`` if the backend can operate on ``circuit``."""

    @abstractmethod
    def prove(self, circuit: ProofCircuit, claim: ProofClaim) -> Mapping[str, Any]:
        """Return a proof artifact suitable for downstream verification."""

    @abstractmethod
    def verify(
        self,
        circuit: ProofCircuit,
        claim: ProofClaim,
        proof_payload: Mapping[str, Any],
    ) -> bool:
        """Verify ``proof_payload`` against ``claim`` and ``circuit``."""


class ProofVerifier(ABC):
    """Policy for verifying proofs emitted by a backend."""

    @abstractmethod
    def verify(
        self,
        backend: ProofBackend,
        circuit: ProofCircuit,
        claim: ProofClaim,
        proof_payload: Mapping[str, Any],
    ) -> bool:
        ...


class BackendProofVerifier(ProofVerifier):
    """Verifier that defers to the backend's native verification logic."""

    def verify(
        self,
        backend: ProofBackend,
        circuit: ProofCircuit,
        claim: ProofClaim,
        proof_payload: Mapping[str, Any],
    ) -> bool:
        return backend.verify(circuit, claim, proof_payload)


# ---------------------------------------------------------------------------
# Circuits
# ---------------------------------------------------------------------------


class KeyOwnershipCircuit(ProofCircuit):
    """Circuit for proving knowledge of a signing key."""

    def __init__(self) -> None:
        super().__init__(
            name="key_ownership",
            description="Prove possession of a private key without revealing it.",
            statement_keys=("public_key",),
            private_keys=("key_material",),
        )


class CapabilityCircuit(ProofCircuit):
    """Circuit for anonymous capability assertions."""

    def __init__(self) -> None:
        super().__init__(
            name="capability",
            description="Show that an action aligns with policy without leaking policy internals.",
            statement_keys=("action", "policy_digest"),
            private_keys=("capability_token",),
        )


class EventCommitmentCircuit(ProofCircuit):
    """Circuit for proving that an event occurred using commitments."""

    def __init__(self) -> None:
        super().__init__(
            name="event_commitment",
            description="Expose only a hash of the event while proving it happened.",
            statement_keys=("event_hash",),
            private_keys=("payload_secret",),
        )


# ---------------------------------------------------------------------------
# Concrete backend
# ---------------------------------------------------------------------------


class HashCommitmentBackend(ProofBackend):
    """Reference backend using Blake2b commitments.

    The backend never stores plain private inputs.  Instead it seals the witness
    using a hash and combines it with deterministic metadata, simulating how a
    production-grade SNARK backend would operate.
    """

    def __init__(self) -> None:
        super().__init__(name="hash_commitment")

    def supports(self, circuit: ProofCircuit) -> bool:  # pragma: no cover - trivial
        return True

    def prove(self, circuit: ProofCircuit, claim: ProofClaim) -> Mapping[str, Any]:
        circuit.validate(claim)
        public_inputs = circuit.public_inputs(claim)
        sealed_witness = self._hash_inputs(circuit.secret_inputs(claim))
        salt = secrets.token_hex(16)
        commitment = self._commitment(public_inputs, sealed_witness, salt)
        return {
            "public_inputs": public_inputs,
            "sealed_witness": sealed_witness,
            "salt": salt,
            "commitment": commitment,
            "backend": self.name,
            "circuit": circuit.name,
        }

    def verify(
        self,
        circuit: ProofCircuit,
        claim: ProofClaim,
        proof_payload: Mapping[str, Any],
    ) -> bool:
        public_inputs = proof_payload.get("public_inputs", {})
        sealed_witness = proof_payload.get("sealed_witness")
        salt = proof_payload.get("salt")
        if not isinstance(public_inputs, Mapping) or not isinstance(sealed_witness, str) or not isinstance(salt, str):
            return False
        expected = self._commitment(public_inputs, sealed_witness, salt)
        return expected == proof_payload.get("commitment")

    def _hash_inputs(self, inputs: Mapping[str, Any]) -> str:
        if not inputs:
            return hashlib.blake2b(b"zero-proof", digest_size=32).hexdigest()
        digest = hashlib.blake2b(digest_size=32)
        for key in sorted(inputs):
            value = str(inputs[key]).encode()
            digest.update(key.encode())
            digest.update(b"::")
            digest.update(value)
        return digest.hexdigest()

    def _commitment(
        self,
        public_inputs: Mapping[str, Any],
        sealed_witness: str,
        salt: str,
    ) -> str:
        digest = hashlib.blake2b(digest_size=32)
        digest.update(sealed_witness.encode())
        digest.update(salt.encode())
        for key in sorted(public_inputs):
            digest.update(key.encode())
            digest.update(b"::")
            digest.update(str(public_inputs[key]).encode())
        return digest.hexdigest()


# ---------------------------------------------------------------------------
# Privacy layer
# ---------------------------------------------------------------------------


class ZeroKnowledgePrivacyLayer:
    """Coordinator for all privacy-preserving proof interactions."""

    def __init__(
        self,
        *,
        verifier: ProofVerifier | None = None,
        receipt_limit: int = 256,
    ) -> None:
        self._backends: dict[str, ProofBackend] = {}
        self._circuits: dict[str, ProofCircuit] = {}
        self._verifier = verifier or BackendProofVerifier()
        self._receipts: deque[Mapping[str, Any]] = deque(maxlen=max(16, receipt_limit))
        self._results: deque[ProofResult] = deque(maxlen=max(16, receipt_limit))

    # Registration ---------------------------------------------------------
    def register_backend(self, backend: ProofBackend) -> None:
        self._backends[backend.name] = backend

    def register_circuit(self, circuit: ProofCircuit) -> None:
        self._circuits[circuit.name] = circuit

    # Proof lifecycle ------------------------------------------------------
    def prove(
        self,
        circuit: str | ProofCircuit,
        claim: ProofClaim,
        *,
        backend: str | None = None,
    ) -> ProofResult:
        circuit_obj = self._resolve_circuit(circuit)
        backend_obj = self._select_backend(circuit_obj, backend)
        payload = backend_obj.prove(circuit_obj, claim)
        verified = self._verifier.verify(backend_obj, circuit_obj, claim, payload)
        result = ProofResult(
            claim_id=claim.claim_id,
            claim_type=claim.claim_type,
            subject=claim.subject,
            circuit=circuit_obj.name,
            backend=backend_obj.name,
            commitment=str(payload.get("commitment")),
            proof=dict(payload),
            public_statement=dict(payload.get("public_inputs", {})),
            verified=verified,
            generated_at=_now_iso(),
            capability=claim.capability,
            diagnostics={"context": dict(claim.context)},
        )
        self._record_result(result)
        return result

    def issue_capability_credential(
        self,
        *,
        claim_id: str,
        subject: str,
        action: str,
        policy_digest: str,
        capability_token: str,
        backend: str | None = None,
    ) -> ProofResult:
        claim = ProofClaim.capability_claim(
            claim_id=claim_id,
            subject=subject,
            action=action,
            policy_digest=policy_digest,
            capability_token=capability_token,
        )
        return self.prove("capability", claim, backend=backend)

    def verify(self, result: ProofResult) -> bool:
        backend = self._backends.get(result.backend)
        circuit = self._circuits.get(result.circuit)
        if not backend or not circuit:
            return False
        sanitized_claim = ProofClaim(
            claim_id=result.claim_id,
            claim_type=result.claim_type,
            subject=result.subject,
            statement=result.public_statement,
            private_inputs={},
            capability=result.capability,
        )
        return backend.verify(circuit, sanitized_claim, result.proof)

    # Introspection --------------------------------------------------------
    def export_receipts(self, limit: int = 10) -> list[Mapping[str, Any]]:
        slice_count = max(0, min(limit, len(self._receipts)))
        return list(list(self._receipts)[-slice_count:])

    def recent_proofs(self, limit: int = 5) -> list[ProofResult]:
        slice_count = max(0, min(limit, len(self._results)))
        return list(list(self._results)[-slice_count:])

    def recent_commitments(self, limit: int = 5) -> list[str]:
        return [result.commitment for result in self.recent_proofs(limit=limit)]

    def privacy_signal(self) -> float:
        if not self._results:
            return 0.0
        verified = sum(1 for result in self._results if result.verified)
        return round(verified / len(self._results), 4)

    def available_backends(self) -> tuple[str, ...]:
        return tuple(sorted(self._backends))

    # Internal -------------------------------------------------------------
    def _resolve_circuit(self, circuit: str | ProofCircuit) -> ProofCircuit:
        if isinstance(circuit, ProofCircuit):
            return circuit
        if circuit not in self._circuits:
            raise ValueError(f"unknown circuit '{circuit}'")
        return self._circuits[circuit]

    def _select_backend(self, circuit: ProofCircuit, backend_name: str | None) -> ProofBackend:
        if backend_name:
            backend = self._backends.get(backend_name)
            if not backend:
                raise ValueError(f"backend '{backend_name}' not registered")
            if not backend.supports(circuit):
                raise ValueError(f"backend '{backend_name}' does not support circuit '{circuit.name}'")
            return backend
        for backend in self._backends.values():
            if backend.supports(circuit):
                return backend
        raise RuntimeError(f"no backend available for circuit '{circuit.name}'")

    def _record_result(self, result: ProofResult) -> None:
        self._results.append(result)
        self._receipts.append(
            {
                "claim_id": result.claim_id,
                "commitment": result.commitment,
                "circuit": result.circuit,
                "backend": result.backend,
                "subject": result.subject,
                "verified": result.verified,
                "capability": result.capability,
                "timestamp": result.generated_at,
            }
        )
