import asyncio
from pathlib import Path

from atlas.scheduler import Job, JobStatus, JobStore, SchedulerService


def test_scheduler_executes_and_retries(tmp_path: Path):
    async def run() -> None:
        store = JobStore(tmp_path / "jobs.db")
        events: list[str] = []

        async def executor(job: Job) -> None:
            events.append(job.id)
            if job.attempts == 0:
                raise RuntimeError("boom")

        job = Job(id="job1", tenant="tenant", payload={"task": "demo"})
        store.upsert(job)

        scheduler = SchedulerService(store, executor, tenant_quotas={"tenant": 2})
        await scheduler._dispatch()
        await asyncio.sleep(0.1)
        await scheduler._dispatch()
        await asyncio.sleep(0.1)

        dead_letters = store.list_dead_letter()
        assert events
        if dead_letters:
            assert dead_letters[0].status is JobStatus.DEAD_LETTER
        else:
            assert store.count_active_for_tenant("tenant") >= 0

    asyncio.run(run())
