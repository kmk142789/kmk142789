"""Atlas core runtime orchestration."""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass


from atlas.core.config import load_config
from atlas.core.logging import configure_logging, get_logger
from atlas.core.supervisor import Supervisor
from atlas.identity import DIDCache, DIDResolver
from atlas.metrics import MetricsRegistry, MetricsService
from atlas.network import NodeRegistry, Pathfinder, RoutingTable
from atlas.scheduler import Job, JobStore, SchedulerService
from atlas.storage import StorageService
from observability import configure_otel


@dataclass
class AtlasContext:
    store: JobStore
    storage: StorageService
    registry: NodeRegistry
    routing: RoutingTable
    resolver: DIDResolver
    metrics: MetricsRegistry
    pathfinder: Pathfinder


async def _execute_job(job: Job) -> None:
    logger = get_logger("atlas.executor")
    logger.info("job_execute", extra={"ctx_job": job.id})


async def build_supervisor() -> Supervisor:
    configure_logging()
    config = load_config()
    configure_otel(
        "atlas-core",
        service_namespace="echo",
        service_version="0.1.0",
        deployment_environment=config.env.get("ENV") or os.getenv("DEPLOYMENT_ENVIRONMENT"),
    )
    store = JobStore(config.scheduler_db)
    metrics_registry = MetricsRegistry()
    storage = StorageService(config.settings, config.storage_dir)
    registry = NodeRegistry()
    routing = RoutingTable()
    pathfinder = Pathfinder(registry, routing)
    cache = DIDCache(config.identity_cache)
    resolver = DIDResolver(cache)
    metrics_service = MetricsService(metrics_registry, host=config.metrics_host, port=config.metrics_port)

    scheduler = SchedulerService(store, executor=_execute_job)

    context = AtlasContext(
        store=store,
        storage=storage,
        registry=registry,
        routing=routing,
        resolver=resolver,
        metrics=metrics_registry,
        pathfinder=pathfinder,
    )

    supervisor = Supervisor([scheduler, metrics_service])
    supervisor.context = context  # type: ignore[attr-defined]
    return supervisor


async def main() -> None:
    supervisor = await build_supervisor()
    await supervisor.run()


if __name__ == "__main__":
    asyncio.run(main())
