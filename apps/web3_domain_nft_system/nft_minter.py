"""Simulated Web3 domain NFT minting Blueprint.

The original dataset for this module surfaced as a disassembly of a compiled
Python file.  This reimplementation recreates the intended behaviour in a fully
readable and well-tested Python module so the routes can be exercised in a test
harness without needing blockchain connectivity.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import hashlib
import json
import secrets

from flask import Blueprint, Flask, jsonify, request
from web3 import Web3


@dataclass(slots=True)
class MintRecord:
    """Container describing a simulated mint operation."""

    domain_name: str
    token_id: int
    token_hex: str
    owner_address: str
    metadata_uri: str
    metadata: Mapping[str, Any]
    transaction_hash: str
    block_number: int
    timestamp: str
    gas_used: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_name": self.domain_name,
            "token_id": self.token_id,
            "token_hex": self.token_hex,
            "owner_address": self.owner_address,
            "metadata_uri": self.metadata_uri,
            "metadata": dict(self.metadata),
            "transaction_hash": self.transaction_hash,
            "block_number": self.block_number,
            "timestamp": self.timestamp,
            "gas_used": self.gas_used,
            "status": self.status,
        }


class NFTMinter:
    """Mint Web3 domains as NFTs using deterministic simulations."""

    def __init__(
        self,
        *,
        contract_address: str = "0x049aba7510f45BA5b64ea9E658E342F904DB358D",
        rng: Optional[secrets.SystemRandom] = None,
    ) -> None:
        self.contract_address = contract_address
        self._rng = rng or secrets.SystemRandom()
        self._minted_domains: Dict[str, MintRecord] = {}
        self._token_ids: set[int] = set()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalise_domain(self, domain_name: str) -> str:
        return domain_name.strip().lower()

    def check_domain_availability(self, domain_name: str) -> bool:
        """Return ``True`` when the domain has not been minted yet."""

        key = self._normalise_domain(domain_name)
        return key not in self._minted_domains

    def generate_unique_token_id(self) -> int:
        """Return a unique token identifier for an NFT."""

        while True:
            token_id = self._rng.getrandbits(160)
            if token_id not in self._token_ids:
                self._token_ids.add(token_id)
                return token_id

    def create_metadata_uri(self, metadata: Mapping[str, Any]) -> str:
        """Return a deterministic IPFS URI for the supplied metadata."""

        metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        metadata_hash = hashlib.sha256(metadata_json.encode("utf-8")).hexdigest()
        return f"ipfs://{metadata_hash}"

    def mint_nft(
        self,
        *,
        domain_name: str,
        owner_address: str,
        metadata: Mapping[str, Any],
    ) -> MintRecord:
        """Simulate minting a domain NFT and store the resulting record."""

        if not domain_name:
            raise ValueError("Domain name is required")
        if not owner_address:
            raise ValueError("Owner address is required")

        domain_key = self._normalise_domain(domain_name)
        if domain_key in self._minted_domains:
            raise ValueError("Domain name already exists")

        token_id = self.generate_unique_token_id()
        token_hex = hex(token_id)
        metadata_uri = self.create_metadata_uri(metadata)
        transaction_hash = "0x" + secrets.token_hex(32)
        block_number = self._rng.randrange(1_000_000, 9_999_999)
        timestamp = datetime.now(timezone.utc).isoformat()
        gas_used = self._rng.randrange(21_000, 120_000)

        record = MintRecord(
            domain_name=domain_name,
            token_id=token_id,
            token_hex=token_hex,
            owner_address=owner_address,
            metadata_uri=metadata_uri,
            metadata=metadata,
            transaction_hash=transaction_hash,
            block_number=block_number,
            timestamp=timestamp,
            gas_used=gas_used,
            status="confirmed",
        )

        self._minted_domains[domain_key] = record
        return record

    def get_nft_info(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Return a copy of the mint record for ``domain_name`` if available."""

        record = self._minted_domains.get(self._normalise_domain(domain_name))
        return record.to_dict() if record else None

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics for minted domains."""

        total_domains = len(self._minted_domains)
        total_gas = sum(record.gas_used for record in self._minted_domains.values())
        unique_owners = {record.owner_address for record in self._minted_domains.values()}
        average_gas = total_gas / total_domains if total_domains else 0.0
        return {
            "total_domains_minted": total_domains,
            "unique_owners": len(unique_owners),
            "total_gas_used": total_gas,
            "average_gas_per_mint": round(average_gas, 2),
        }

    def batch_mint(
        self, domains: Iterable[Mapping[str, Any]]
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """Mint multiple domains and capture the per-domain results."""

        successes = 0
        failures = 0
        results: List[Dict[str, Any]] = []

        for payload in domains:
            domain_name = str(payload.get("domain_name", "")).strip()
            owner_address = str(payload.get("owner_address", "")).strip()
            metadata = payload.get("metadata")
            if not isinstance(metadata, Mapping):
                metadata = {}

            try:
                record = self.mint_nft(
                    domain_name=domain_name,
                    owner_address=owner_address,
                    metadata=metadata,
                )
            except Exception as exc:  # pragma: no cover - handled in tests
                failures += 1
                results.append(
                    {
                        "domain_name": domain_name,
                        "success": False,
                        "error": str(exc),
                    }
                )
            else:
                successes += 1
                results.append(
                    {
                        "domain_name": domain_name,
                        "success": True,
                        "data": record.to_dict(),
                    }
                )

        return successes, failures, results


def _validate_address(address: str) -> bool:
    """Return ``True`` when ``address`` appears to be a valid Ethereum address."""

    return Web3.is_address(address)


def create_blueprint(minter: Optional[NFTMinter] = None) -> Blueprint:
    """Return a Flask :class:`~flask.Blueprint` exposing minting routes."""

    minter = minter or NFTMinter()
    blueprint = Blueprint("nft_minter", __name__)

    @blueprint.record_once
    def _stash_minter(state: Any) -> None:  # pragma: no cover - Flask hook
        state.app.extensions.setdefault("nft_minter", minter)

    @blueprint.route("/mint", methods=["POST"])
    def mint_domain_nft() -> Any:
        payload = request.get_json(silent=True) or {}
        domain_name = str(payload.get("domain_name", "")).strip()
        owner_address = str(payload.get("owner_address", "")).strip()
        metadata = payload.get("metadata")
        if not metadata:
            metadata = {}
        if not isinstance(metadata, Mapping):
            return (
                jsonify({"message": "Metadata must be an object", "data": None}),
                400,
            )

        if not domain_name or not owner_address:
            return (
                jsonify(
                    {
                        "message": "Missing required fields: domain_name, owner_address",
                        "data": None,
                    }
                ),
                400,
            )

        if not _validate_address(owner_address):
            return (
                jsonify({"message": "Invalid Ethereum address format", "data": None}),
                400,
            )

        try:
            record = minter.mint_nft(
                domain_name=domain_name,
                owner_address=owner_address,
                metadata=metadata,
            )
        except ValueError as exc:
            return jsonify({"message": f"Minting failed: {exc}", "data": None}), 409
        except Exception as exc:  # pragma: no cover - defensive guard
            return (
                jsonify({"message": f"Minting request failed: {exc}", "data": None}),
                500,
            )

        return (
            jsonify({"message": "NFT minted successfully", "data": record.to_dict()}),
            201,
        )

    @blueprint.route("/check-availability", methods=["POST"])
    def check_availability() -> Any:
        payload = request.get_json(silent=True) or {}
        domain_name = str(payload.get("domain_name", "")).strip()
        if not domain_name:
            return jsonify({"message": "Domain name is required", "available": False}), 400

        available = minter.check_domain_availability(domain_name)
        message = "Available for minting" if available else "Domain already exists"
        return jsonify({"message": message, "available": available})

    @blueprint.route("/info/<domain_name>", methods=["GET"])
    def get_domain_info(domain_name: str) -> Any:
        record = minter.get_nft_info(domain_name)
        if not record:
            return jsonify({"message": "Domain not found or not minted", "found": False}), 404
        return jsonify({"message": "Domain details located", "found": True, "data": record})

    @blueprint.route("/batch-mint", methods=["POST"])
    def batch_mint_domains() -> Any:
        payload = request.get_json(silent=True) or {}
        domains = payload.get("domains")
        if not domains:
            return jsonify({"message": "No domains provided for batch minting"}), 400
        if not isinstance(domains, list):
            return jsonify({"message": "Domains payload must be a list"}), 400
        if len(domains) > 100:
            return jsonify({"message": "Batch size limited to 100 domains"}), 400

        successes, failures, results = minter.batch_mint(domains)
        return jsonify(
            {
                "message": "Batch minting complete",
                "batch_complete": failures == 0,
                "total_domains": len(domains),
                "successful_mints": successes,
                "failed_mints": failures,
                "results": results,
            }
        )

    @blueprint.route("/stats", methods=["GET"])
    def get_minting_stats() -> Any:
        stats = minter.get_stats()
        return jsonify({"message": "Minting statistics", "data": stats})

    return blueprint


def create_app(minter: Optional[NFTMinter] = None) -> Flask:
    """Return a minimal Flask app hosting the NFT minting blueprint."""

    app = Flask(__name__)
    app.register_blueprint(create_blueprint(minter))
    return app


__all__ = ["NFTMinter", "MintRecord", "create_app", "create_blueprint"]


if __name__ == "__main__":  # pragma: no cover
    application = create_app()
    application.run(debug=True, port=5005)
