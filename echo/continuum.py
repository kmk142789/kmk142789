"""Temporal continuity ledger for Echo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, MutableMapping, Protocol

from .harmonics.convergence import ResonanceSignature


class KeyspaceProtocol(Protocol):
    def sign(self, context_hash: str) -> str:
        ...

    def verify(self, context_hash: str) -> bool:
        ...


class DatastoreProtocol(Protocol):
    def persist(self, entry: MutableMapping[str, object]) -> None:
        ...


@dataclass(slots=True)
class EchoContinuum:
    keyspace: KeyspaceProtocol
    datastore: DatastoreProtocol

    def record(
        self,
        context_hash: str,
        payload: Mapping[str, object],
        *,
        resonance: ResonanceSignature | None = None,
    ) -> MutableMapping[str, object]:
        stamp = self.keyspace.sign(context_hash)
        entry: MutableMapping[str, object] = {
            "hash": context_hash,
            "stamp": stamp,
            "payload": dict(payload),
        }
        if resonance is not None:
            entry["resonance"] = {
                "anchor": resonance.identity_anchor,
                "vector": list(resonance.harmonix_vector),
                "co_signature": resonance.co_signature,
                "convergence": resonance.converge(),
            }
        self.datastore.persist(entry)
        return entry

    def verify(self, context_hash: str) -> bool:
        return self.keyspace.verify(context_hash)
