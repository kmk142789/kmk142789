"""Health checking utilities."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

import httpx

from atlas.core.logging import get_logger

from .registry import NodeRegistry


@dataclass
class HealthChecker:
    registry: NodeRegistry
    interval: float = 5.0
    timeout: float = 2.0

    def __post_init__(self) -> None:
        self.logger = get_logger("atlas.network.health")

    async def run_once(self) -> Dict[str, float]:
        results: Dict[str, float] = {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for node in self.registry.list():
                try:
                    start = datetime.now(timezone.utc)
                    response = await client.get(f"{node.url}/health")
                    response.raise_for_status()
                    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
                    weight = self._decay_weight(node.weight, elapsed)
                    self.registry.heartbeat(node.id, weight)
                    results[node.id] = weight
                except Exception as exc:  # pragma: no cover - network failure path
                    self.logger.warning("node_unhealthy", extra={"ctx_node": node.id, "ctx_error": repr(exc)})
                    self.registry.heartbeat(node.id, weight=0.0)
                    results[node.id] = 0.0
        return results

    @staticmethod
    def _decay_weight(current_weight: float, latency: float, half_life: float = 30.0) -> float:
        decay = 0.5 ** (latency / half_life)
        return max(0.0, min(1.0, (current_weight * decay) + (1 - decay)))


__all__ = ["HealthChecker"]
