"""Simple DID resolver with offline cache."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import httpx

from atlas.core.logging import get_logger


@dataclass
class DIDCache:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def get(self, did: str) -> Optional[Dict[str, object]]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return data.get(did)

    def set(self, did: str, document: Dict[str, object]) -> None:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data[did] = document
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


class DIDResolver:
    def __init__(self, cache: DIDCache, endpoint: str = "https://resolver.did.example"):
        self.cache = cache
        self.endpoint = endpoint.rstrip("/")
        self.logger = get_logger("atlas.identity.did")

    async def resolve(self, did: str) -> Dict[str, object]:
        cached = self.cache.get(did)
        if cached:
            return cached
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{self.endpoint}/{did}")
            response.raise_for_status()
            document = response.json()
        self.cache.set(did, document)
        return document


__all__ = ["DIDCache", "DIDResolver"]
