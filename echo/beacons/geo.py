"""Geographic-aware beacon selection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from echo.beacons.base import Beacon


@dataclass(frozen=True, slots=True)
class GeoHint:
    """Lightweight description of a beacon's geographic placement."""

    region: str
    latency_ms: float
    reliability: float


class GeoAwareSelector:
    """Select beacons that are geographically diverse."""

    def __init__(self) -> None:
        self.hints: Dict[str, GeoHint] = {
            "gist": GeoHint("us-east", 50, 0.999),
            "ipfs_infura": GeoHint("us-east", 150, 0.99),
            "ipfs_pinata": GeoHint("us-west", 180, 0.98),
            "arweave": GeoHint("distributed", 300, 0.995),
            "nostr_relay_1": GeoHint("eu-west", 120, 0.97),
            "nostr_relay_2": GeoHint("asia-pacific", 200, 0.96),
        }

    def select_diverse(self, beacons: List[Beacon], n: int) -> List[Beacon]:
        if n <= 0 or not beacons:
            return []

        by_region: Dict[str, List[Beacon]] = {}
        for beacon in beacons:
            hint = self.hints.get(beacon.name, GeoHint("unknown", 500, 0.9))
            by_region.setdefault(hint.region, []).append(beacon)

        regions = [region for region, bucket in by_region.items() if bucket]
        if not regions:
            return []

        selected: List[Beacon] = []
        while len(selected) < n and regions:
            for region in list(regions):
                bucket = by_region.get(region, [])
                if not bucket:
                    regions = [r for r in regions if r != region]
                    continue
                selected.append(bucket.pop(0))
                if len(selected) >= n:
                    break
            regions = [region for region in regions if by_region.get(region)]

        return selected[:n]
