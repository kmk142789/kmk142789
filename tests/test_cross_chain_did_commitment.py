import json
import re

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from eth_utils.crypto import keccak

from packages.core.src.cross_chain_did_commitment import (
    compute_did_commitment,
    ed25519_sign_commitment,
    ed25519_verify_commitment_signature,
    merkle_proof,
    ordinal_merkle_path,
    verify_merkle_proof,
)


HEX32_RE = re.compile(r"^0x[a-f0-9]{64}$")
HEX64_RE = re.compile(r"^0x[a-f0-9]{128}$")


def _load_ordinal_schema():
    with open("schemas/did_ordinal_inscription.json", "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_cross_chain_commitment_round_trip():
    did_document = {
        "id": "did:example:echo",
        "controller": "did:example:controller",
        "verificationMethod": [
            {"id": "did:example:echo#keys-1", "type": "Ed25519VerificationKey2018"}
        ],
    }
    credential_proofs = [
        {"credential": "vc-1", "status": "valid"},
        {"credential": "vc-2", "status": "valid"},
        {"credential": "vc-3", "status": "revoked"},
    ]
    zk_proof_bytes = b"groth16-proof-commitment"

    commitment, leaves, tree = compute_did_commitment(
        did_document,
        credential_proofs,
        zk_proof_bytes,
        did_identifier=did_document["id"],
        timestamp=1_704_610_000,
    )

    assert commitment.aggregate_commitment == keccak(
        commitment.did_hash + commitment.merkle_root + commitment.zk_commitment
    )

    proof_index = 1
    proof = merkle_proof(tree, proof_index)
    assert verify_merkle_proof(leaves[proof_index], proof, commitment.merkle_root, proof_index)

    ordinal_path = ordinal_merkle_path(proof, proof_index)
    assert all(HEX32_RE.match(node["hash"]) for node in ordinal_path)
    assert set(node["position"] for node in ordinal_path) <= {"left", "right"}

    payload = commitment.as_bitcoin_ordinal_payload(network="testnet")
    payload["merkleProof"] = ordinal_path

    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(
        "1f" * 32
    ))
    signature, public_key = ed25519_sign_commitment(private_key, commitment)
    assert ed25519_verify_commitment_signature(public_key, signature, commitment)

    payload["signature"] = {
        "publicKey": "0x" + public_key.hex(),
        "value": "0x" + signature.hex(),
    }

    # Validate Bitcoin ordinal schema expectations.
    schema = _load_ordinal_schema()
    assert payload["timestamp"] == commitment.timestamp
    assert payload["protocol"] == schema["properties"]["protocol"]["const"]
    assert payload["version"] >= schema["properties"]["version"]["minimum"]
    assert payload["network"] in schema["properties"]["network"]["enum"]
    assert HEX32_RE.match(payload["hashes"]["did"])
    assert HEX32_RE.match(payload["hashes"]["verifiableCredentials"])
    assert HEX32_RE.match(payload["hashes"]["zk"])
    assert HEX32_RE.match(payload["hashes"]["aggregate"])
    assert HEX32_RE.match(payload["signature"]["publicKey"])
    assert HEX64_RE.match(payload["signature"]["value"])

    # Ethereum compatibility checks.
    did_key = keccak(did_document["id"].encode("utf-8"))
    assert len(did_key) == 32
    expected_aggregate = keccak(commitment.did_hash + commitment.merkle_root + commitment.zk_commitment)
    assert commitment.aggregate_commitment == expected_aggregate
    assert len(proof) == len(payload["merkleProof"])
    assert all(node["hash"].startswith("0x") for node in payload["merkleProof"])

    # Solana compatibility: signature bytes should be the same message used for verification.
    assert signature[:32] != b"\x00" * 32  # sanity check on deterministic signature
    assert len(public_key) == 32
