"""Command-line interface for EchoField SwarmKit."""

from __future__ import annotations

import argparse
import logging
import os
from typing import Any, Dict

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

from .echo_node import EchoNode, EchoNodeConfig

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "echo_config.yaml")


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML config files.")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EchoField SwarmKit node agent")
    parser.add_argument("--node-id", required=False, help="Unique identifier for this node")
    parser.add_argument("--sync-path", help="Directory for file-drop sync adapter")
    parser.add_argument("--max-sync-age", type=int, help="Seconds before a peer snapshot is considered stale")
    parser.add_argument("--task-store", help="Path for persisted task ledger")
    parser.add_argument("--state-store", help="Path for node state storage")
    parser.add_argument("--health-interval", type=int, help="Seconds between health checks")
    parser.add_argument("--sync-interval", type=int, help="Seconds between swarm sync attempts")
    parser.add_argument("--peers", nargs="*", help="Peer node IDs to seed the swarm with")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to YAML config file")
    parser.add_argument("--run-once", action="store_true", help="Run a single health + sync cycle then exit")
    parser.add_argument("--log-level", default="INFO", help="Logging level (INFO, DEBUG, ...)")
    return parser


def merge_settings(args: argparse.Namespace, config: Dict[str, Any]) -> EchoNodeConfig:
    node_id = args.node_id or config.get("node_id") or "echo-node"
    task_store_path = args.task_store or config.get("task_store_path") or "~/.echo_field_swarmkit/tasks.json"
    state_store_path = args.state_store or config.get("state_store_path") or "~/.echo_field_swarmkit/state.json"
    sync_path = args.sync_path or config.get("sync_path") or "/tmp/swarm_sync"
    health_interval = args.health_interval or config.get("health_interval_seconds", 300)
    sync_interval = args.sync_interval or config.get("sync_interval_seconds", 60)
    max_sync_age = args.max_sync_age or config.get("max_sync_age_seconds", 900)
    peers = args.peers or config.get("peers") or []

    return EchoNodeConfig(
        node_id=node_id,
        task_store_path=task_store_path,
        state_store_path=state_store_path,
        sync_path=sync_path,
        health_interval=health_interval,
        sync_interval=sync_interval,
        max_sync_age=max_sync_age,
        peers=peers,
    )


def main():
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    config_data = load_config(args.config) if args.config else {}
    node_config = merge_settings(args, config_data)
    node = EchoNode(node_config)

    if args.run_once:
        checks = node.health.run_health_check_cycle()
        node.gecs.observe_and_correct(checks)
        node._sync_with_peers()
        node._execute_local_tasks()
    else:
        node.main_loop()


if __name__ == "__main__":
    main()
