"""Cross-chain DID commitment utilities.

This module provides helpers for constructing and verifying commitments that are
shared between the Ethereum, Solana, and Bitcoin anchor implementations added in
this change-set.  The functions focus on deterministic encodings so that each
chain can re-compute the same digest material regardless of language/runtime
differences.
"""

from __future__ import annotations

import dataclasses
import json
import time
from typing import Iterable, List, Sequence, Tuple

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from eth_utils.crypto import keccak


Bytes32 = bytes


def _canonical_json(value: object) -> bytes:
    """Return a canonical JSON encoding for deterministic hashing."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _hash_leaf(data: bytes) -> Bytes32:
    return keccak(data)


def _merkle_parent(left: Bytes32, right: Bytes32) -> Bytes32:
    return keccak(left + right)


def build_merkle_tree(leaves: Sequence[Bytes32]) -> List[List[Bytes32]]:
    """Build a Merkle tree (Keccak) from the provided leaves."""

    if not leaves:
        raise ValueError("merkle tree requires at least one leaf")

    tree: List[List[Bytes32]] = [list(leaves)]
    level = list(leaves)
    while len(level) > 1:
        next_level: List[Bytes32] = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else level[i]
            next_level.append(_merkle_parent(left, right))
        tree.append(next_level)
        level = next_level
    return tree


def merkle_root(leaves: Sequence[Bytes32]) -> Bytes32:
    """Compute the Merkle root for the given leaves."""

    return build_merkle_tree(leaves)[-1][0]


def merkle_proof(tree: Sequence[Sequence[Bytes32]], index: int) -> List[Bytes32]:
    """Return sibling hashes forming a Merkle proof for a leaf index."""

    if not tree:
        raise ValueError("cannot build proof from an empty tree")
    if index < 0 or index >= len(tree[0]):
        raise IndexError("leaf index out of range")

    proof: List[Bytes32] = []
    idx = index
    for level in tree[:-1]:
        sibling_idx = idx ^ 1
        if sibling_idx < len(level):
            proof.append(level[sibling_idx])
        else:
            # odd node duplicated; sibling is the node itself
            proof.append(level[idx])
        idx //= 2
    return proof


def verify_merkle_proof(
    leaf: Bytes32, proof: Iterable[Bytes32], root: Bytes32, index: int
) -> bool:
    computed = leaf
    idx = index
    for sibling in proof:
        if idx % 2 == 0:
            computed = _merkle_parent(computed, sibling)
        else:
            computed = _merkle_parent(sibling, computed)
        idx //= 2
    return computed == root


def ordinal_merkle_path(proof: Sequence[Bytes32], index: int) -> List[dict]:
    """Format a proof into ordinal inscription friendly descriptors."""

    descriptors: List[dict] = []
    idx = index
    for sibling in proof:
        position = "right" if idx % 2 == 0 else "left"
        descriptors.append({"hash": "0x" + sibling.hex(), "position": position})
        idx //= 2
    return descriptors


@dataclasses.dataclass(frozen=True)
class DIDCommitment:
    did_identifier: str
    did_hash: Bytes32
    merkle_root: Bytes32
    zk_commitment: Bytes32
    aggregate_commitment: Bytes32
    timestamp: int

    def as_bitcoin_ordinal_payload(self, network: str = "mainnet") -> dict:
        return {
            "protocol": "echo-did-commitment",
            "version": 1,
            "network": network,
            "timestamp": self.timestamp,
            "did": self.did_identifier,
            "hashes": {
                "did": "0x" + self.did_hash.hex(),
                "verifiableCredentials": "0x" + self.merkle_root.hex(),
                "zk": "0x" + self.zk_commitment.hex(),
                "aggregate": "0x" + self.aggregate_commitment.hex(),
            },
        }


def compute_did_commitment(
    did_document: dict,
    credential_proofs: Sequence[dict],
    zk_proof_bytes: bytes,
    did_identifier: str,
    timestamp: int | None = None,
) -> Tuple[DIDCommitment, List[Bytes32], List[List[Bytes32]]]:
    """Compute a DID commitment suite for cross-chain anchoring."""

    did_hash = keccak(_canonical_json(did_document))

    leaf_hashes = [_hash_leaf(_canonical_json(proof)) for proof in credential_proofs]
    vc_root = merkle_root(leaf_hashes)
    zk_commitment = keccak(zk_proof_bytes)
    aggregate = keccak(did_hash + vc_root + zk_commitment)

    commitment = DIDCommitment(
        did_identifier=did_identifier,
        did_hash=did_hash,
        merkle_root=vc_root,
        zk_commitment=zk_commitment,
        aggregate_commitment=aggregate,
        timestamp=int(timestamp or time.time()),
    )
    tree = build_merkle_tree(leaf_hashes)
    return commitment, leaf_hashes, tree


def ed25519_sign_commitment(private_key: Ed25519PrivateKey, commitment: DIDCommitment) -> Tuple[bytes, bytes]:
    message = commitment.aggregate_commitment
    signature = private_key.sign(message)
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)
    return signature, public_bytes


def ed25519_verify_commitment_signature(
    public_key_bytes: bytes, signature: bytes, commitment: DIDCommitment
) -> bool:
    public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    try:
        public_key.verify(signature, commitment.aggregate_commitment)
        return True
    except Exception:  # pragma: no cover - explicit failure path
        return False
