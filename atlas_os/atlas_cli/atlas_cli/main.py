"""Atlas OS management CLI with rich inspection commands."""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from atlas_network import RoutingTable
from atlas_storage import TransactionLog


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="atlas", description="Atlas OS management CLI")
    parser.add_argument("--metrics", default="metrics.json", help="Path to kernel metrics snapshot")
    parser.add_argument("--manifest", default="manifest.json", help="Path to routing table snapshot")
    parser.add_argument(
        "--log",
        default="transactions.log",
        help="Path to the distributed storage transaction log",
    )

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show kernel metrics")

    nodes = sub.add_parser("nodes", help="List discovered network nodes")
    nodes.add_argument("--show-path", nargs=2, metavar=("SRC", "DST"), help="Compute best path between nodes")

    storage = sub.add_parser("storage", help="Inspect distributed storage")
    storage_sub = storage.add_subparsers(dest="storage_command")
    storage_sub.add_parser("list", help="List logical files from the transaction log")
    storage_sub.add_parser("summary", help="Show aggregated storage statistics")

    sub.add_parser("logs", help="Tail the transaction log")
    return parser


# ---------------------------------------------------------------------------
def _load_json(path: str) -> Dict:
    target = Path(path)
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON document: {path}: {exc}") from exc


def _print_table(headers: Iterable[str], rows: Iterable[Iterable[str]]) -> None:
    headers = list(headers)
    rows = [list(row) for row in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))
    fmt = "  ".join(f"{{:{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


# ---------------------------------------------------------------------------
def cmd_status(args: argparse.Namespace) -> None:
    metrics = _load_json(args.metrics)
    if not metrics:
        print("No metrics recorded yet. Run the kernel metrics exporter first.")
        return

    rows: List[Tuple[str, str, str]] = []
    for name, sample in sorted(metrics.items()):
        timestamp = datetime.fromtimestamp(sample.get("timestamp", 0)).isoformat()
        value = f"{sample.get('value', 0):.3f}"
        rows.append((name, value, timestamp))
    _print_table(["Metric", "Value", "Timestamp"], rows)


def _populate_routing_table(manifest: Dict) -> RoutingTable:
    table = RoutingTable()
    nodes = manifest.get("nodes") or manifest
    for node_id, info in nodes.items():
        if not isinstance(info, dict):
            continue
        table.update(
            node_id,
            info.get("host", "127.0.0.1"),
            int(info.get("port", 0)),
            priority=int(info.get("priority", 5)),
            latency_ms=float(info.get("latency_ms", 1.0)),
            packet_loss=float(info.get("packet_loss", 0.0)),
            bandwidth_mbps=float(info.get("bandwidth_mbps", 100.0)),
        )
        for neighbor, link_info in info.get("links", {}).items():
            table.update_link(
                node_id,
                neighbor,
                latency_ms=float(link_info.get("latency_ms", info.get("latency_ms", 1.0))),
                packet_loss=float(link_info.get("packet_loss", 0.0)),
                bandwidth_mbps=float(link_info.get("bandwidth_mbps", info.get("bandwidth_mbps", 100.0))),
                hops=int(link_info.get("hops", 1)),
            )
    return table


def cmd_nodes(args: argparse.Namespace) -> None:
    manifest = _load_json(args.manifest)
    if not manifest:
        print("No routing manifest found. Run the discovery daemon first.")
        return

    table = _populate_routing_table(manifest)
    rows = []
    for entry in table.to_list():
        age = max(0.0, time.time() - entry.last_seen)
        rows.append(
            (
                entry.node_id,
                f"{entry.host}:{entry.port}",
                str(entry.priority),
                f"{entry.latency_ms:.1f} ms",
                f"{entry.packet_loss:.2%}",
                f"{entry.bandwidth_mbps:.1f}",
                f"{age:.1f}s",
            )
        )
    _print_table(
        ["Node", "Endpoint", "Prio", "Latency", "Loss", "Throughput", "Age"],
        rows,
    )

    if args.show_path:
        src, dst = args.show_path
        try:
            path = table.compute_path(src, dst)
        except Exception as exc:  # pragma: no cover - user interaction path
            print(f"Failed to compute path: {exc}")
        else:
            print(" -> ".join(path))


def _replay_storage_log(tx: TransactionLog) -> Tuple[Dict[str, Dict], List[Tuple[str, Dict]]]:
    files: Dict[str, Dict] = {}
    history: List[Tuple[str, Dict]] = []
    for entry in tx:
        history.append((entry.action, entry.payload))
        if entry.action == "write":
            files[entry.payload["path"]] = {
                "bytes": entry.payload.get("bytes", 0),
                "node": entry.payload.get("node_id", "unknown"),
            }
        elif entry.action == "delete":
            files.pop(entry.payload.get("path", ""), None)
    return files, history


def cmd_storage_list(args: argparse.Namespace) -> None:
    tx = TransactionLog(args.log)
    files, _ = _replay_storage_log(tx)
    if not files:
        print("No stored objects found in transaction log.")
        return
    rows = []
    for path, info in sorted(files.items()):
        rows.append((path, info.get("node", "?"), str(info.get("bytes", 0))))
    _print_table(["Path", "Node", "Bytes"], rows)


def cmd_storage_summary(args: argparse.Namespace) -> None:
    tx = TransactionLog(args.log)
    files, history = _replay_storage_log(tx)
    total_bytes = sum(info.get("bytes", 0) for info in files.values())
    per_node = Counter(info.get("node", "unknown") for info in files.values())
    print(f"Tracked objects: {len(files)}")
    print(f"Total logical bytes: {total_bytes}")
    print("Distribution by node:")
    for node, count in sorted(per_node.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {node}: {count} objects")
    print(f"History entries: {len(history)}")


def cmd_logs(args: argparse.Namespace) -> None:
    tx = TransactionLog(args.log)
    tail = list(tx.tail(20))
    if not tail:
        print("Transaction log is empty.")
        return
    for entry in tail:
        timestamp = datetime.fromtimestamp(entry.timestamp).isoformat()
        payload = json.dumps(entry.payload, sort_keys=True)
        print(f"{timestamp} {entry.action:<12s} {payload}")


def main(argv: List[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command == "status":
        cmd_status(args)
    elif args.command == "nodes":
        cmd_nodes(args)
    elif args.command == "storage":
        if args.storage_command == "list":
            cmd_storage_list(args)
        elif args.storage_command == "summary":
            cmd_storage_summary(args)
        else:
            parser.error("Storage command requires a subcommand")
    elif args.command == "logs":
        cmd_logs(args)
    else:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

