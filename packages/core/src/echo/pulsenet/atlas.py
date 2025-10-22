"""Atlas attestation helpers for PulseNet integrations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from echo_atlas.service import AtlasService


@dataclass(frozen=True)
class WalletAttestation:
    """Metadata extracted from an Atlas attestation."""

    fingerprint: str
    extended_public_key: str
    derivation_path: str | None
    owner: str | None
    source: str

    def as_dict(self) -> Mapping[str, str | None]:
        return {
            "fingerprint": self.fingerprint,
            "extended_public_key": self.extended_public_key,
            "derivation_path": self.derivation_path,
            "owner": self.owner,
            "source": self.source,
        }


class AtlasAttestationResolver:
    """Aggregate wallet metadata from Atlas and local attestations."""

    def __init__(self, project_root: Path, atlas_service: AtlasService) -> None:
        self._project_root = Path(project_root)
        self._atlas_service = atlas_service
        self._cache: dict[str, WalletAttestation] = {}
        self.refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Refresh the cached metadata from Atlas and attestation files."""

        cache: dict[str, WalletAttestation] = {}
        for record in self._iter_atlas_wallets():
            cache.setdefault(record.fingerprint, record)
            cache.setdefault(record.extended_public_key, record)
        for record in self._iter_attestation_files():
            cache.setdefault(record.fingerprint, record)
            cache.setdefault(record.extended_public_key, record)
        self._cache = cache

    def lookup(self, identifier: str | None) -> WalletAttestation | None:
        if not identifier:
            return None
        key = identifier.strip()
        if not key:
            return None
        return self._cache.get(key)

    def wallets(self) -> list[Mapping[str, str | None]]:
        seen: set[str] = set()
        result: list[Mapping[str, str | None]] = []
        for record in self._cache.values():
            if record.fingerprint in seen:
                continue
            seen.add(record.fingerprint)
            result.append(record.as_dict())
        return sorted(result, key=lambda item: item.get("fingerprint") or "")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _iter_atlas_wallets(self) -> Iterable[WalletAttestation]:
        try:
            nodes = self._atlas_service.list_nodes()
        except Exception:  # pragma: no cover - defensive; Atlas may be offline
            return []
        records: list[WalletAttestation] = []
        for node in nodes:
            metadata = dict(getattr(node, "metadata", {}) or {})
            fingerprint = str(metadata.get("fingerprint") or metadata.get("id") or "").strip()
            xpub = str(metadata.get("extended_public_key") or "").strip()
            derivation = metadata.get("derivation_path")
            owner = metadata.get("owner") or metadata.get("project")
            if fingerprint and xpub:
                records.append(
                    WalletAttestation(
                        fingerprint=fingerprint,
                        extended_public_key=xpub,
                        derivation_path=str(derivation) if derivation else None,
                        owner=str(owner) if owner else None,
                        source="atlas",
                    )
                )
        return records

    def _iter_attestation_files(self) -> Iterable[WalletAttestation]:
        roots = [self._project_root / "attestations", self._project_root / "artifacts", self._project_root]
        for root in roots:
            if not root.exists():
                continue
            for path in root.glob("**/*.json"):
                yield from self._extract_wallets(path)

    def _extract_wallets(self, path: Path) -> Iterable[WalletAttestation]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):  # pragma: no cover - defensive
            return []
        wallets: list[WalletAttestation] = []
        ledger = data.get("ledger") if isinstance(data, dict) else None
        if isinstance(ledger, dict):
            wallets_map = ledger.get("wallets")
            if isinstance(wallets_map, dict):
                wallets.extend(self._parse_wallet_mapping(wallets_map, path))
        raw_wallets = data.get("wallets") if isinstance(data, dict) else None
        if isinstance(raw_wallets, list):
            wallets.extend(self._parse_wallet_sequence(raw_wallets, path, owner=data.get("owner")))
        return wallets

    @staticmethod
    def _parse_wallet_mapping(mapping: Mapping[str, object], path: Path) -> Iterable[WalletAttestation]:
        for fingerprint, payload in mapping.items():
            if not isinstance(payload, Mapping):
                continue
            metadata = payload.get("metadata")
            if isinstance(metadata, Mapping):
                xpub = metadata.get("extended_public_key") or payload.get("xpub")
                derivation = metadata.get("derivation_path") or payload.get("derivation_path")
            else:
                xpub = payload.get("xpub")
                derivation = payload.get("derivation_path")
            if not isinstance(xpub, str) or not xpub.strip():
                continue
            record = WalletAttestation(
                fingerprint=str(fingerprint),
                extended_public_key=xpub.strip(),
                derivation_path=str(derivation) if isinstance(derivation, str) and derivation else None,
                owner=str(payload.get("owner")) if payload.get("owner") else None,
                source=str(path.name),
            )
            yield record

    @staticmethod
    def _parse_wallet_sequence(
        sequence: Iterable[Mapping[str, object]],
        path: Path,
        *,
        owner: str | None = None,
    ) -> Iterable[WalletAttestation]:
        for item in sequence:
            if not isinstance(item, Mapping):
                continue
            fingerprint = item.get("fingerprint")
            xpub = item.get("xpub") or item.get("extended_public_key")
            derivation = item.get("derivation_path")
            if not isinstance(fingerprint, str) or not isinstance(xpub, str):
                continue
            yield WalletAttestation(
                fingerprint=fingerprint,
                extended_public_key=xpub,
                derivation_path=str(derivation) if isinstance(derivation, str) and derivation else None,
                owner=str(owner) if owner else None,
                source=str(path.name),
            )


__all__ = ["AtlasAttestationResolver", "WalletAttestation"]
