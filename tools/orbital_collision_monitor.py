"""Advanced orbital conjunction monitor with resilient fetching and simulation.

This module translates the "ECHO ORBITAL DOMINION" concept into a maintainable
utility that can be run as a CLI or imported for programmatic use.  It focuses on
three pillars:

* Reliable TLE retrieval with caching and age validation.
* Deterministic, simulation-friendly collision prediction that scales to large
  constellations without external ephemeris dependencies.
* Export and alert surfaces so downstream tooling can consume conjunction events.

The simulator intentionally uses deterministic pseudo-orbital paths derived from
TLE line checksums.  This keeps the tool self contained for environments where
physics-grade propagators (e.g., ``sgp4`` or ``skyfield``) are unavailable while
still surfacing consistent miss-distance trends for observability or testing
workflows.
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import logging
from logging.handlers import RotatingFileHandler
import math
import os
import random
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass(slots=True)
class CollisionMonitorConfig:
    """Configuration for :class:`OrbitalCollisionMonitor`.

    Defaults mirror the original ECHO Orbital Dominion sketch while remaining
    practical for local runs.
    """

    observer_lat: float = 40.7128
    observer_lon: float = -74.0060
    observer_alt_km: float = 0.01

    update_interval: int = 300
    prediction_horizon_hours: int = 48
    temporal_resolution: int = 720

    collision_threshold_km: float = 5.0
    high_risk_threshold_km: float = 1.0
    critical_threshold_km: float = 0.5

    state_file: Path = Path("echo_collision_state.json")
    log_file: Path = Path("echo_collision_system.log")
    csv_export: Path = Path("conjunction_events.csv")
    tle_cache_dir: Path = Path("tle_cache")

    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5

    max_workers: int = 8
    tle_fetch_timeout: int = 20
    tle_max_age_hours: int = 24
    cell_size_km: float = 80.0

    enable_email_alerts: bool = False
    enable_webhook: bool = False
    webhook_url: Optional[str] = None

    tle_sources: Mapping[str, str] = dataclasses.field(
        default_factory=lambda: {
            "Starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            "Iridium": "https://celestrak.org/NORAD/elements/gp.php?GROUP=iridium-NEXT&FORMAT=tle",
            "OneWeb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
        }
    )


@dataclass(slots=True)
class TLERecord:
    """Simple container for a two-line element set."""

    name: str
    line1: str
    line2: str
    norad_id: Optional[int]
    fetched_at: datetime

    def cache_payload(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "line1": self.line1,
            "line2": self.line2,
            "norad_id": self.norad_id,
            "fetched_at": self.fetched_at.isoformat(),
        }


@dataclass(slots=True)
class ConjunctionEvent:
    """Data class for conjunction events."""

    sat1_name: str
    sat2_name: str
    sat1_norad: Optional[int]
    sat2_norad: Optional[int]
    tca: datetime
    distance_km: float
    rel_velocity_kms: float
    probability_collision: float
    risk_level: str
    detection_time: datetime

    def to_row(self) -> Dict[str, str | float]:
        return {
            "sat1_name": self.sat1_name,
            "sat2_name": self.sat2_name,
            "sat1_norad": self.sat1_norad or "",
            "sat2_norad": self.sat2_norad or "",
            "tca": self.tca.isoformat(),
            "distance_km": round(self.distance_km, 6),
            "rel_velocity_kms": round(self.rel_velocity_kms, 6),
            "probability_collision": round(self.probability_collision, 6),
            "risk_level": self.risk_level,
            "detection_time": self.detection_time.isoformat(),
        }


class OrbitalCollisionMonitor:
    """High-level controller for fetching, predicting, and exporting events."""

    def __init__(
        self,
        config: Optional[CollisionMonitorConfig] = None,
        *,
        session: Optional[Session] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config or CollisionMonitorConfig()
        self.session = session or self._create_session()
        self.log = logger or self._setup_logging()
        self.tle_cache: MutableMapping[str, List[TLERecord]] = defaultdict(list)
        self.metadata: Dict[str, Dict[str, object]] = {}
        self.state_lock = threading.Lock()
        self.config.tle_cache_dir.mkdir(exist_ok=True)
        self.log.debug("OrbitalCollisionMonitor initialised with %d sources", len(self.config.tle_sources))

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger("orbital-collision-monitor")
        logger.setLevel(getattr(logging, self.config.log_level.upper(), logging.INFO))

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            rotating = RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.log_max_bytes,
                backupCount=self.config.log_backup_count,
            )
            rotating.setFormatter(formatter)
            logger.addHandler(rotating)

            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.addHandler(console)

        return logger

    @staticmethod
    def _create_session() -> Session:
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_maxsize=20)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    # ------------------------------------------------------------------
    # TLE retrieval and caching
    # ------------------------------------------------------------------

    def _cache_path(self, source: str) -> Path:
        safe_name = source.lower().replace(" ", "_")
        return self.config.tle_cache_dir / f"{safe_name}.json"

    def _load_cache(self, source: str) -> List[TLERecord]:
        path = self._cache_path(source)
        if not path.exists():
            return []
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return []

        records: List[TLERecord] = []
        for item in payload:
            try:
                records.append(
                    TLERecord(
                        name=item["name"],
                        line1=item["line1"],
                        line2=item["line2"],
                        norad_id=item.get("norad_id"),
                        fetched_at=datetime.fromisoformat(item["fetched_at"]),
                    )
                )
            except (KeyError, ValueError):
                continue
        return records

    def _write_cache(self, source: str, records: Sequence[TLERecord]) -> None:
        payload = [record.cache_payload() for record in records]
        path = self._cache_path(source)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        self.log.debug("Cached %d TLEs for %s", len(records), source)

    def _parse_tle_lines(self, lines: Sequence[str], source: str) -> List[TLERecord]:
        records: List[TLERecord] = []
        fetched_at = datetime.now(timezone.utc)
        index = 0
        while index + 2 < len(lines):
            maybe_name, line1, line2 = lines[index : index + 3]
            if not (line1.startswith("1 ") and line2.startswith("2 ")):
                index += 1
                continue
            name = maybe_name if not maybe_name.startswith("1 ") else f"{source}-{len(records)}"
            try:
                norad_id = int(line1.split()[1].rstrip("U"))
            except (IndexError, ValueError):
                norad_id = None
            records.append(TLERecord(name=name, line1=line1, line2=line2, norad_id=norad_id, fetched_at=fetched_at))
            index += 3
        return records

    def _fetch_source(self, source: str, url: str) -> Tuple[str, List[TLERecord]]:
        self.log.info("Fetching %s TLEs", source)
        try:
            response: Response = self.session.get(url, timeout=self.config.tle_fetch_timeout)
            response.raise_for_status()
            lines = [line.strip() for line in response.text.splitlines() if line.strip()]
            records = self._parse_tle_lines(lines, source)
            self._write_cache(source, records)
            return source, records
        except Exception as exc:  # noqa: BLE001
            cached = self._load_cache(source)
            if cached:
                self.log.warning("Using cached %d TLEs for %s after fetch failure: %s", len(cached), source, exc)
                return source, cached
            self.log.error("Failed to fetch %s TLEs: %s", source, exc)
            return source, []

    def fetch_all_tles(self, *, force_refresh: bool = False) -> List[TLERecord]:
        start = time.perf_counter()
        should_refresh = force_refresh or self._cache_stale()

        if not should_refresh:
            cached_records = []
            for source in self.config.tle_sources:
                cached_records.extend(self._load_cache(source))
            if cached_records:
                self.log.info("Loaded %d satellites from cache", len(cached_records))
                return cached_records

        records: List[TLERecord] = []
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._fetch_source, source, url): source
                for source, url in self.config.tle_sources.items()
            }
            for future in as_completed(futures):
                _, subset = future.result()
                records.extend(subset)

        elapsed = time.perf_counter() - start
        self.log.info("Loaded %d satellites in %.2fs", len(records), elapsed)
        return records

    def _cache_stale(self) -> bool:
        threshold = timedelta(hours=self.config.tle_max_age_hours)
        for source in self.config.tle_sources:
            cache = self._load_cache(source)
            if not cache:
                return True
            newest = max(record.fetched_at for record in cache)
            if datetime.now(timezone.utc) - newest > threshold:
                return True
        return False

    # ------------------------------------------------------------------
    # Prediction helpers
    # ------------------------------------------------------------------

    def _seed_for_record(self, record: TLERecord) -> int:
        digest = hashlib.sha256(f"{record.name}:{record.line1}:{record.line2}".encode()).hexdigest()
        return int(digest[:16], 16)

    def _simulate_positions(
        self,
        record: TLERecord,
        *,
        start: datetime,
        resolution: int,
        horizon_hours: int,
    ) -> List[np.ndarray]:
        seed = self._seed_for_record(record)
        rng = random.Random(seed)
        base_radius = 6800 + (seed % 400)  # km
        theta0 = (seed % 360) * math.pi / 180
        angular_velocity = 2 * math.pi / (90 * 60)  # rad per minute
        step_minutes = (horizon_hours * 60) / resolution

        positions: List[np.ndarray] = []
        for idx in range(resolution):
            theta = theta0 + angular_velocity * (step_minutes * idx)
            inclination = (seed % 63) * math.pi / 180
            radius = base_radius + math.sin(idx / 50) * 25
            x = radius * math.cos(theta) * math.cos(inclination)
            y = radius * math.sin(theta) * math.cos(inclination)
            z = radius * math.sin(inclination)
            # jitter keeps relative velocity non-zero
            jitter = np.array([rng.uniform(-0.5, 0.5) for _ in range(3)])
            positions.append(np.array([x, y, z]) + jitter)
        return positions

    def _build_spatial_index(self, positions: Mapping[str, np.ndarray]) -> Dict[Tuple[int, int, int], List[str]]:
        index: Dict[Tuple[int, int, int], List[str]] = defaultdict(list)
        cell = self.config.cell_size_km
        for name, vector in positions.items():
            key = (int(vector[0] // cell), int(vector[1] // cell), int(vector[2] // cell))
            index[key].append(name)
        return index

    def _candidate_pairs(self, index: Mapping[Tuple[int, int, int], List[str]]) -> Iterable[Tuple[str, str]]:
        neighbours = [(-1, -1, -1), (-1, -1, 0), (-1, -1, 1), (-1, 0, -1), (-1, 0, 0), (-1, 0, 1), (-1, 1, -1), (-1, 1, 0), (-1, 1, 1),
                      (0, -1, -1), (0, -1, 0), (0, -1, 1), (0, 0, -1), (0, 0, 0), (0, 0, 1), (0, 1, -1), (0, 1, 0), (0, 1, 1),
                      (1, -1, -1), (1, -1, 0), (1, -1, 1), (1, 0, -1), (1, 0, 0), (1, 0, 1), (1, 1, -1), (1, 1, 0), (1, 1, 1)]
        seen: set[Tuple[str, str]] = set()
        for key, names in index.items():
            for delta in neighbours:
                neighbour_key = (key[0] + delta[0], key[1] + delta[1], key[2] + delta[2])
                for other in index.get(neighbour_key, []):
                    for name in names:
                        if name == other:
                            continue
                        pair = tuple(sorted((name, other)))
                        if pair not in seen:
                            seen.add(pair)
                            yield pair

    def _distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        return float(np.linalg.norm(vec1 - vec2))

    def _probability(self, miss_distance: float) -> float:
        if miss_distance <= 0.001:
            return 1.0
        sigma = 0.1
        return float(min(1.0, max(0.0, math.exp(-(miss_distance**2) / (2 * sigma**2)))))

    def predict_conjunctions(self, records: Sequence[TLERecord]) -> List[ConjunctionEvent]:
        if len(records) < 2:
            self.log.warning("Insufficient satellites for conjunction analysis")
            return []

        start_time = datetime.now(timezone.utc)
        resolution = self.config.temporal_resolution
        positions_at_t0: Dict[str, np.ndarray] = {}
        trajectories: Dict[str, List[np.ndarray]] = {}

        for record in records:
            path = self._simulate_positions(
                record,
                start=start_time,
                resolution=resolution,
                horizon_hours=self.config.prediction_horizon_hours,
            )
            trajectories[record.name] = path
            positions_at_t0[record.name] = path[0]
            self.metadata[record.name] = {"norad_id": record.norad_id, "fetched_at": record.fetched_at}

        index = self._build_spatial_index(positions_at_t0)
        candidates = list(self._candidate_pairs(index))
        self.log.info("Evaluating %d candidate pairs", len(candidates))

        events: List[ConjunctionEvent] = []
        for sat1_name, sat2_name in candidates:
            sat1_path = trajectories[sat1_name]
            sat2_path = trajectories[sat2_name]

            miss_distance = math.inf
            tca_index = 0
            for idx in range(resolution):
                d = self._distance(sat1_path[idx], sat2_path[idx])
                if d < miss_distance:
                    miss_distance = d
                    tca_index = idx

            if miss_distance >= self.config.collision_threshold_km:
                continue

            # Approximate relative velocity using adjacent sample
            prev_index = max(tca_index - 1, 0)
            delta_pos = sat1_path[tca_index] - sat1_path[prev_index]
            delta_pos -= sat2_path[tca_index] - sat2_path[prev_index]
            rel_velocity = np.linalg.norm(delta_pos) / (
                (self.config.prediction_horizon_hours * 3600) / self.config.temporal_resolution
            )

            probability = self._probability(miss_distance)
            if miss_distance < self.config.critical_threshold_km:
                risk = "CRITICAL"
            elif miss_distance < self.config.high_risk_threshold_km:
                risk = "HIGH"
            else:
                risk = "WARNING"

            tca = start_time + timedelta(
                seconds=(tca_index / self.config.temporal_resolution) * (self.config.prediction_horizon_hours * 3600)
            )

            events.append(
                ConjunctionEvent(
                    sat1_name=sat1_name,
                    sat2_name=sat2_name,
                    sat1_norad=self.metadata[sat1_name].get("norad_id"),
                    sat2_norad=self.metadata[sat2_name].get("norad_id"),
                    tca=tca,
                    distance_km=miss_distance,
                    rel_velocity_kms=float(rel_velocity),
                    probability_collision=probability,
                    risk_level=risk,
                    detection_time=start_time,
                )
            )

        events.sort(key=lambda e: e.distance_km)
        self.log.info("Conjunction analysis complete: %d events detected", len(events))
        return events

    # ------------------------------------------------------------------
    # Export and alerting
    # ------------------------------------------------------------------

    def export_to_csv(self, events: Sequence[ConjunctionEvent]) -> None:
        if not events:
            return

        fieldnames = list(events[0].to_row().keys())
        file_exists = self.config.csv_export.exists()
        with self.config.csv_export.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            for event in events:
                writer.writerow(event.to_row())
        self.log.info("Exported %d events to %s", len(events), self.config.csv_export)

    def send_alerts(self, events: Sequence[ConjunctionEvent]) -> None:
        critical = [event for event in events if event.risk_level == "CRITICAL"]
        if not critical:
            return
        if self.config.enable_webhook and self.config.webhook_url:
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "critical_events": [event.to_row() for event in critical],
            }
            try:
                response = self.session.post(self.config.webhook_url, json=payload, timeout=10)
                response.raise_for_status()
                self.log.info("Webhook alert sent for %d critical events", len(critical))
            except Exception as exc:  # noqa: BLE001
                self.log.error("Webhook alert failed: %s", exc)

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def save_state(self, events: Sequence[ConjunctionEvent]) -> None:
        state = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "events": [event.to_row() for event in events],
            "statistics": {
                "total_satellites": len(self.metadata),
                "events_detected": len(events),
            },
        }
        with self.config.state_file.open("w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
        self.log.debug("State persisted to %s", self.config.state_file)

    # ------------------------------------------------------------------
    # Public orchestration
    # ------------------------------------------------------------------

    def run_once(self, *, force_refresh: bool = False) -> List[ConjunctionEvent]:
        records = self.fetch_all_tles(force_refresh=force_refresh)
        events = self.predict_conjunctions(records)
        self.export_to_csv(events)
        self.send_alerts(events)
        self.save_state(events)
        return events


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Orbital collision monitor")
    parser.add_argument("--force-refresh", action="store_true", help="Bypass cache age checks for TLE downloads")
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    args = parser.parse_args(argv)

    config = CollisionMonitorConfig(log_level=args.log_level)
    monitor = OrbitalCollisionMonitor(config)
    events = monitor.run_once(force_refresh=args.force_refresh)

    if events:
        top = events[0]
        monitor.log.info(
            "Closest approach: %s vs %s — %.3f km at %s",
            top.sat1_name,
            top.sat2_name,
            top.distance_km,
            top.tca.isoformat(),
        )
    else:
        monitor.log.info("No conjunctions detected within horizon")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
