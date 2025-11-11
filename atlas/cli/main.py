"""Atlas CLI entrypoints."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import click

from atlas.core import AtlasConfig, load_config
from atlas.identity import CredentialIssuer, CredentialVerifier, DIDCache, RotatingKeyManager
from atlas.metrics import MetricsRegistry
from atlas.network import NodeInfo, NodeRegistry, Pathfinder, RoutingTable
from atlas.scheduler import Job, JobStore
from atlas.storage import StorageReceipt, StorageService


def _load_config() -> AtlasConfig:
    return load_config()


def _load_node_registry(config: AtlasConfig) -> NodeRegistry:
    registry = NodeRegistry()
    path = config.data_dir / "nodes.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        for node in data:
            info = NodeInfo(
                id=node["id"],
                host=node["host"],
                port=int(node["port"]),
                weight=float(node.get("weight", 1.0)),
                meta=node.get("meta", {}),
            )
            if node.get("last_seen"):
                info.last_seen = datetime.fromisoformat(node["last_seen"])
            registry.register(info)
    return registry


def _persist_node_registry(config: AtlasConfig, registry: NodeRegistry) -> None:
    payload = []
    for node in registry.list():
        payload.append(
            {
                "id": node.id,
                "host": node.host,
                "port": node.port,
                "weight": node.weight,
                "meta": node.meta,
                "last_seen": node.last_seen.isoformat(),
            }
        )
    (config.data_dir / "nodes.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _storage_service(config: AtlasConfig) -> StorageService:
    return StorageService(config.settings, config.storage_dir)


def _job_store(config: AtlasConfig) -> JobStore:
    return JobStore(config.scheduler_db)


def _routing_table(config: AtlasConfig) -> RoutingTable:
    table = RoutingTable()
    path = config.data_dir / "routing.json"
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        table.weights = {tuple(k.split("->")): v for k, v in data.items()}
    return table


def _persist_routing(config: AtlasConfig, routing: RoutingTable) -> None:
    path = config.data_dir / "routing.json"
    payload = {"->".join(k): v for k, v in routing.weights.items()}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _identity_paths(config: AtlasConfig) -> tuple[Path, Path]:
    key_path = config.data_dir / "issuer.key"
    did_path = config.data_dir / "issuer.did"
    if not key_path.exists():
        manager = RotatingKeyManager.generate()
        key, _ = manager.derive()
        key_path.write_bytes(key)
        did_path.write_text("did:example:atlas", encoding="utf-8")
    return key_path, did_path


@click.group()
def app() -> None:
    """Atlas OS orchestration CLI."""


@app.group()
def node() -> None:
    """Node registry commands."""


@node.command("add")
@click.option("--node-id", required=True)
@click.option("--host", required=True)
@click.option("--port", type=int, required=True)
@click.option("--weight", type=float, default=1.0)
def node_add(node_id: str, host: str, port: int, weight: float) -> None:
    config = _load_config()
    registry = _load_node_registry(config)
    registry.register(NodeInfo(id=node_id, host=host, port=port, weight=weight))
    _persist_node_registry(config, registry)
    click.echo(f"registered {node_id}")


@node.command("list")
def node_list() -> None:
    config = _load_config()
    registry = _load_node_registry(config)
    for node in registry.list():
        click.echo(f"{node.id} -> {node.url} (weight={node.weight})")


@app.group()
def storage() -> None:
    """Storage operations."""


@storage.command("put")
@click.option("--driver", default="fs")
@click.option("--path", required=True)
@click.option("--data", required=True, help="String payload to store")
def storage_put(driver: str, path: str, data: str) -> None:
    config = _load_config()
    service = _storage_service(config)
    receipt = service.put(driver, path, data.encode("utf-8"))
    receipt_path = config.data_dir / "last_receipt.json"
    receipt_path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
    click.echo(json.dumps(receipt.to_dict(), indent=2))


@storage.command("get")
@click.option("--driver", default=None)
@click.option("--receipt", type=click.Path(), required=False)
def storage_get(driver: str | None, receipt: str | None) -> None:
    config = _load_config()
    service = _storage_service(config)
    receipt_path = Path(receipt) if receipt else config.data_dir / "last_receipt.json"
    info = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    stored = StorageReceipt(**info)
    chosen_driver = driver or stored.driver
    data = service.get(chosen_driver, stored)
    click.echo(data.decode("utf-8"))


@app.group()
def schedule() -> None:
    """Job scheduling commands."""


@schedule.command("create")
@click.option("--job-id", required=True)
@click.option("--tenant", required=True)
@click.option("--payload", required=True)
def schedule_create(job_id: str, tenant: str, payload: str) -> None:
    config = _load_config()
    store = _job_store(config)
    job = Job(id=job_id, tenant=tenant, payload=json.loads(payload))
    store.upsert(job)
    click.echo(f"job {job_id} created")


@schedule.command("due")
@click.option("--limit", type=int, default=10)
def schedule_due(limit: int) -> None:
    config = _load_config()
    store = _job_store(config)
    jobs = store.get_due_jobs(limit)
    click.echo(json.dumps([job.to_record() for job in jobs], indent=2))


@app.group()
def route() -> None:
    """Routing utilities."""


@route.command("set")
@click.option("--source", required=True)
@click.option("--dest", required=True)
@click.option("--weight", type=float, required=True)
def route_set(source: str, dest: str, weight: float) -> None:
    config = _load_config()
    routing = _routing_table(config)
    registry = _load_node_registry(config)
    src = registry.get(source)
    dst = registry.get(dest)
    if not src or not dst:
        raise click.UsageError("Nodes must exist")
    routing.update(src, dst, weight)
    _persist_routing(config, routing)
    click.echo("route updated")


@route.command("path")
@click.option("--source", required=True)
@click.option("--dest", required=True)
def route_path(source: str, dest: str) -> None:
    config = _load_config()
    routing = _routing_table(config)
    registry = _load_node_registry(config)
    finder = Pathfinder(registry, routing)
    click.echo(" -> ".join(finder.best_path(source, dest)))


@app.group()
def id() -> None:
    """Identity commands."""


@id.command("issue")
@click.option("--subject", required=True)
@click.option("--claims", required=True)
def id_issue(subject: str, claims: str) -> None:
    config = _load_config()
    key_path, did_path = _identity_paths(config)
    issuer = CredentialIssuer.from_seed(key_path.read_bytes(), did_path.read_text(encoding="utf-8"))
    credential = issuer.issue(subject, json.loads(claims))
    cred_path = config.data_dir / "last_credential.json"
    cred_path.write_text(json.dumps(credential, indent=2), encoding="utf-8")
    click.echo(json.dumps(credential, indent=2))


@id.command("verify")
@click.option("--credential", type=click.Path(), required=False)
def id_verify(credential: str | None) -> None:
    config = _load_config()
    cred_path = Path(credential) if credential else config.data_dir / "last_credential.json"
    data = json.loads(cred_path.read_text(encoding="utf-8"))
    key_path, _ = _identity_paths(config)
    verifier = CredentialVerifier.from_bytes(CredentialIssuer.from_seed(key_path.read_bytes(), "did:example:atlas").export_public_key())
    click.echo("valid" if verifier.verify(data) else "invalid")


@app.group()
def metrics() -> None:
    """Metrics utilities."""


@metrics.command("snapshot")
def metrics_snapshot() -> None:
    registry = MetricsRegistry()
    loop = asyncio.new_event_loop()
    try:
        counter = loop.run_until_complete(registry.counter("atlas_jobs_total"))
        counter.inc(5)
        timer = loop.run_until_complete(registry.timer("atlas_job_duration_seconds"))
        timer.observe(0.1)
        timer.observe(0.2)
        snapshot = loop.run_until_complete(registry.snapshot())
    finally:
        loop.close()
    click.echo(json.dumps(snapshot, indent=2))


@app.group()
def diag() -> None:
    """Diagnostic utilities."""


@diag.command("config")
def diag_config() -> None:
    config = _load_config()
    payload: Dict[str, Any] = {
        "root": str(config.root),
        "data_dir": str(config.data_dir),
        "settings": config.settings,
        "env": config.env,
    }
    click.echo(json.dumps(payload, indent=2))


if __name__ == "__main__":
    app()
