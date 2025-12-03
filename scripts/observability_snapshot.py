"""Quick observability snapshot helper.

This utility captures lightweight host metrics so on-call engineers can
quickly confirm a machine's baseline health without attaching to the full
observability stack. It prints JSON by default and supports a readable text
mode for ad-hoc debugging.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import socket
import time
from dataclasses import dataclass, asdict
from typing import Iterable

PSUTIL_AVAILABLE = importlib.util.find_spec("psutil") is not None
if PSUTIL_AVAILABLE:
    import psutil  # type: ignore


@dataclass
class Snapshot:
    cpu_percent: float
    process_count: int
    node_count: int
    hostname: str
    timestamp_utc: str
    load_average: tuple[float, float, float]
    uptime_seconds: float
    memory_percent: float

    @classmethod
    def collect(cls, sample_seconds: float = 0.25) -> "Snapshot":
        cpu_percent = _cpu_percent(sample_seconds)
        process_count = _process_count()
        node_count = _node_count()
        hostname = socket.gethostname()
        timestamp_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        load_average = _load_average()
        uptime_seconds = _uptime_seconds()
        memory_percent = _memory_percent()
        return cls(
            cpu_percent=round(cpu_percent, 2),
            process_count=process_count,
            node_count=node_count,
            hostname=hostname,
            timestamp_utc=timestamp_utc,
            load_average=load_average,
            uptime_seconds=uptime_seconds,
            memory_percent=memory_percent,
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, indent=2)

    def to_text(self) -> str:
        return (
            f"Observability snapshot @ {self.timestamp_utc}\n"
            f"Host: {self.hostname}\n"
            f"CPU usage: {self.cpu_percent:.2f}%\n"
            f"Load average (1/5/15m): {self._format_load()}\n"
            f"Memory usage: {self.memory_percent:.1f}%\n"
            f"Process count: {self.process_count}\n"
            f"Uptime: {self.uptime_seconds:.0f}s\n"
            f"Network nodes (interfaces with addresses): {self.node_count}\n"
        )

    def _format_load(self) -> str:
        return "/".join(f"{value:.2f}" for value in self.load_average)


def _cpu_percent(sample_seconds: float) -> float:
    if PSUTIL_AVAILABLE:
        # psutil measures over the provided interval to avoid stale values.
        return float(psutil.cpu_percent(interval=sample_seconds))

    if hasattr(os, "getloadavg"):
        load1, _, _ = os.getloadavg()
        cores = os.cpu_count() or 1
        return min(100.0, (load1 / cores) * 100)

    return 0.0


def _process_count() -> int:
    if PSUTIL_AVAILABLE:
        return len(psutil.pids())

    proc_dir = "/proc"
    if os.path.exists(proc_dir):
        return sum(1 for entry in os.listdir(proc_dir) if entry.isdigit())

    return 0


def _node_count() -> int:
    if PSUTIL_AVAILABLE:
        return _count_addressable_interfaces(psutil.net_if_addrs().items())

    sys_net = "/sys/class/net"
    if os.path.exists(sys_net):
        return _count_addressable_interfaces(
            (name, []) for name in os.listdir(sys_net)
        )

    return 1


def _count_addressable_interfaces(items: Iterable) -> int:
    count = 0
    for name, addrs in items:
        if name.startswith("lo"):
            continue
        if not addrs:
            count += 1
            continue
        has_address = any(
            getattr(addr, "family", None) in {socket.AF_INET, socket.AF_INET6}
            for addr in addrs
        )
        if has_address:
            count += 1
    return max(count, 1)


def _load_average() -> tuple[float, float, float]:
    if hasattr(os, "getloadavg"):
        try:
            load1, load5, load15 = os.getloadavg()
            return (round(load1, 2), round(load5, 2), round(load15, 2))
        except OSError:
            return (0.0, 0.0, 0.0)
    return (0.0, 0.0, 0.0)


def _uptime_seconds() -> float:
    if PSUTIL_AVAILABLE:
        try:
            return float(time.time() - psutil.boot_time())
        except (OSError, AttributeError, TypeError):
            pass

    proc_uptime = "/proc/uptime"
    if os.path.exists(proc_uptime):
        try:
            with open(proc_uptime, "r", encoding="utf-8") as handle:
                first_fragment = handle.read().split()[0]
                return float(first_fragment)
        except (OSError, ValueError):
            return 0.0

    return 0.0


def _memory_percent() -> float:
    if PSUTIL_AVAILABLE:
        try:
            return float(psutil.virtual_memory().percent)
        except (OSError, AttributeError, TypeError):
            pass

    meminfo_path = "/proc/meminfo"
    if os.path.exists(meminfo_path):
        try:
            values = {}
            with open(meminfo_path, "r", encoding="utf-8") as handle:
                for line in handle:
                    key, _, raw_value = line.partition(":")
                    if not raw_value:
                        continue
                    value_str = raw_value.strip().split()[0]
                    values[key] = float(value_str)
            total = values.get("MemTotal")
            available = values.get("MemAvailable")
            if total and available:
                used = total - available
                return max(0.0, min(100.0, (used / total) * 100.0))
        except (OSError, ValueError):
            return 0.0

    return 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Emit a lightweight observability snapshot with CPU, process, "
            "and node counts."
        )
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format. JSON is emitted by default for downstream tooling.",
    )
    parser.add_argument(
        "--sample-seconds",
        type=float,
        default=0.25,
        help=(
            "Sampling window for CPU measurement. Increase for steadier "
            "averages on noisy hosts."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot = Snapshot.collect(sample_seconds=args.sample_seconds)
    if args.format == "json":
        print(snapshot.to_json())
    else:
        print(snapshot.to_text())


if __name__ == "__main__":
    main()
