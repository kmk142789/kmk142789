import asyncio

from atlas.metrics import MetricsRegistry, MetricsService


def test_metrics_registry_prometheus():
    async def run() -> None:
        registry = MetricsRegistry()
        counter = await registry.counter("atlas_jobs_total")
        counter.inc(3)
        timer = await registry.timer("atlas_job_duration_seconds")
        timer.observe(0.1)
        timer.observe(0.2)
        output = await registry.export_prometheus()
        assert "atlas_jobs_total" in output
        assert "atlas_job_duration_seconds_count" in output

    asyncio.run(run())


def test_metrics_service_serves():
    async def run() -> None:
        registry = MetricsRegistry()
        service = MetricsService(registry, host="127.0.0.1", port=0, ws_port=9102)
        await service.start()
        await asyncio.sleep(0.1)
        await service.stop()

    asyncio.run(run())
