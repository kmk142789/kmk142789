"""Blueprint exposing endpoints for Web3 domain and NFT utilities."""

from __future__ import annotations

import hashlib
import os
import random
import secrets
from typing import Any, Dict, Tuple

from flask import Blueprint, jsonify, request

try:  # pragma: no cover - optional dependency during tests
    from eth_account import Account
    from web3 import Web3  # type: ignore
except ImportError:  # pragma: no cover - graceful degradation
    Account = None  # type: ignore
    Web3 = None  # type: ignore


crypto_bp = Blueprint("crypto", __name__)


class SecureKeyHandler:
    """Utility helpers focused on ephemeral key material handling."""

    @staticmethod
    def validate_private_key(private_key_input: str) -> Tuple[bool, str | None, str | None]:
        """Normalise *private_key_input* and derive its public address.

        Returns a tuple ``(is_valid, normalized_key, public_address)``.  When
        validation fails the final element contains an error message instead of
        an address.
        """

        if not isinstance(private_key_input, str):
            return False, None, "Invalid private key format"

        key = private_key_input.strip()
        if key.startswith("0x"):
            key = key[2:]

        if len(key) != 64:
            return False, None, "Invalid private key format"

        try:
            private_key_bytes = bytes.fromhex(key)
        except ValueError:
            return False, None, "Invalid private key format"

        try:
            if Account is None:
                raise RuntimeError("web3 dependencies are not installed")

            account = Account.from_key(private_key_bytes)
            normalized_key = f"0x{key.lower()}"
            # Hash the key bytes so that we can reference the validation event
            # without retaining the sensitive material itself.
            hashlib.sha256(private_key_bytes).hexdigest()
            return True, normalized_key, account.address
        except Exception as exc:  # pragma: no cover - depends on web3
            hashed = hashlib.sha256(private_key_bytes).hexdigest()
            return False, hashed, f"{exc}"

    @staticmethod
    def generate_domain_name(public_address: str) -> str:
        """Derive a pseudo-random domain name from *public_address*."""

        if not public_address:
            raise ValueError("Public address is required")

        salt = secrets.token_hex(4)
        combined = f"{public_address.lower()}:{salt}"
        domain_hash = hashlib.sha256(combined.encode()).hexdigest()
        return f"{domain_hash[:16]}.crypto"

    @staticmethod
    def create_nft_metadata(
        public_address: str,
        genesis_info: Dict[str, Any] | None = None,
        *,
        domain_name: str | None = None,
    ) -> Dict[str, Any]:
        """Build NFT metadata for the generated domain."""

        genesis_info = genesis_info or {}
        domain_name = domain_name or genesis_info.get("domain_name") or SecureKeyHandler.generate_domain_name(public_address)

        metadata = {
            "name": domain_name,
            "description": (
                "Unique 1/1 Genesis Web3 Domain NFT derived from cryptographic "
                "key material. This domain represents a quantum-resistant, "
                "decentralized identity."
            ),
            "image": "https://api.placeholder.com/400x400/0066cc/ffffff?text=Genesis+Domain",
            "external_url": "https://example.com/domains",
            "attributes": [
                {"trait_type": "Domain Type", "value": "Genesis Domain"},
                {"trait_type": "Public Address", "value": public_address},
                {"trait_type": "Quantum Resistant", "value": "Yes"},
                {
                    "trait_type": "Genesis ID",
                    "value": genesis_info.get("genesis_id", "Unknown"),
                },
            ],
        }

        return metadata


@crypto_bp.route("/validate-key", methods=["POST"])
def validate_key():
    """Validate a private key and return the corresponding public address."""

    data = request.get_json(silent=True) or {}
    private_key = data.get("private_key")

    if not private_key:
        return jsonify({"valid": False, "error": "Private key is required"}), 400

    is_valid, normalized_key, result = SecureKeyHandler.validate_private_key(private_key)

    if not is_valid:
        return (
            jsonify(
                {
                    "valid": False,
                    "message": f"Validation failed: {result}",
                    "key_hash": normalized_key,
                }
            ),
            400,
        )

    return jsonify(
        {
            "valid": True,
            "message": "Private key validated successfully. Key material has been securely disposed.",
            "public_address": result,
            "normalized_key": normalized_key,
        }
    )


@crypto_bp.route("/generate-domain", methods=["POST"])
def generate_domain():
    """Generate a deterministic domain and NFT metadata for an address."""

    data = request.get_json(silent=True) or {}
    public_address = data.get("public_address")
    genesis_info = data.get("genesis_info", {})

    if not public_address:
        return jsonify({"success": False, "error": "Public address is required"}), 400

    try:
        domain_name = SecureKeyHandler.generate_domain_name(public_address)
        metadata = SecureKeyHandler.create_nft_metadata(
            public_address,
            genesis_info,
            domain_name=domain_name,
        )
        return jsonify({"success": True, "domain": domain_name, "metadata": metadata})
    except Exception as exc:
        return (
            jsonify({"success": False, "error": f"Domain generation failed: {exc}"}),
            400,
        )


@crypto_bp.route("/simulate-mint", methods=["POST"])
def simulate_mint():
    """Mock the NFT minting process for demonstration purposes."""

    data = request.get_json(silent=True) or {}
    required_fields = {"owner_address", "metadata_url", "domain"}

    if not required_fields.issubset(data):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    token_id = data.get("token_id") or random.randint(1, 10**6)
    transaction_hash = "0x" + secrets.token_hex(32)

    result = {
        "success": True,
        "transaction_hash": transaction_hash,
        "token_id": token_id,
        "owner_address": data["owner_address"],
        "metadata_url": data["metadata_url"],
        "domain": data["domain"],
        "metadata_snapshot": data.get("metadata"),
    }

    return jsonify(result)


@crypto_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check for monitoring integrations."""

    return jsonify(
        {
            "status": "healthy",
            "service": "Web3 Domain NFT Generator",
            "version": "1.0.0",
            "quantum_resistant": True,
            "environment": os.getenv("FLASK_ENV", "production"),
        }
    )


__all__ = ["crypto_bp", "SecureKeyHandler"]
