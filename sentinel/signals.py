from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from . import utils


def _collect_http_endpoints(node: Any) -> list[str]:
    endpoints: list[str] = []
    if isinstance(node, dict):
        for value in node.values():
            endpoints.extend(_collect_http_endpoints(value))
    elif isinstance(node, list):
        for value in node:
            endpoints.extend(_collect_http_endpoints(value))
    elif isinstance(node, str) and node.startswith("http"):
        endpoints.append(node)
    return endpoints


def derive_signals(inventory: dict[str, Any]) -> dict[str, Any]:
    receipts = inventory.get("receipts", [])
    http_sources = _collect_http_endpoints(inventory.get("lineage", {}))

    counters = Counter(receipt.get("mode", "unknown") for receipt in receipts)
    sizes = [receipt.get("size", 0) for receipt in receipts if isinstance(receipt.get("size"), int)]

    return {
        "total_receipts": len(receipts),
        "missing_receipts": counters.get("missing", 0),
        "total_size": sum(sizes),
        "http_endpoints": sorted(set(http_sources)),
        "registry_fragments": len(utils.ensure_list(inventory.get("registry", {}).get("fragments"))),
    }


def sentinel_workspace() -> Path:
    return Path("build/sentinel")

