"""Scheduler service orchestrating job execution."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Awaitable, Callable, Dict, Optional

from atlas.core.logging import get_logger
from atlas.core.service import Service

from .job import Job, JobStatus
from .store import JobStore


class SchedulerService(Service):
    def __init__(
        self,
        store: JobStore,
        executor: Callable[[Job], Awaitable[None]],
        tenant_quotas: Optional[Dict[str, int]] = None,
        poll_interval: float = 1.0,
    ):
        super().__init__("atlas.scheduler")
        self.store = store
        self.executor = executor
        self.poll_interval = poll_interval
        self.tenant_quotas = tenant_quotas or {}
        self.logger = get_logger(self.name)

    async def run(self) -> None:
        while True:
            try:
                await self._dispatch()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # pragma: no cover - safety net
                self.logger.error("dispatch_error", extra={"ctx_error": repr(exc)})
            await asyncio.sleep(self.poll_interval)

    async def _dispatch(self) -> None:
        for job in self.store.get_due_jobs():
            if not self._can_schedule(job):
                continue
            self.store.mark_running(job.id)
            job.status = JobStatus.RUNNING
            asyncio.create_task(self._execute(job), name=f"job:{job.id}")

    def _can_schedule(self, job: Job) -> bool:
        quota = self.tenant_quotas.get(job.tenant)
        if quota is None:
            return True
        active = self.store.count_active_for_tenant(job.tenant)
        if active >= quota:
            return False
        return True

    async def _execute(self, job: Job) -> None:
        started_at = datetime.now(timezone.utc)
        try:
            if job.runtime_limit:
                await asyncio.wait_for(self.executor(job), timeout=job.runtime_limit)
            else:
                await self.executor(job)
        except asyncio.TimeoutError:
            job.attempts += 1
            job.last_error = "runtime_limit_exceeded"
            if job.attempts >= job.retry_policy.max_attempts:
                job.status = JobStatus.DEAD_LETTER
                self.store.upsert(job)
            else:
                job.schedule_next()
                self.store.upsert(job)
        except Exception as exc:  # pragma: no cover - executor failure path
            job.attempts += 1
            job.last_error = repr(exc)
            if job.attempts >= job.retry_policy.max_attempts:
                job.status = JobStatus.DEAD_LETTER
                self.store.upsert(job)
            else:
                job.schedule_next()
                self.store.upsert(job)
        else:
            job.status = JobStatus.COMPLETED
            job.updated_at = datetime.now(timezone.utc)
            self.store.upsert(job)
        finally:
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            self.logger.info(
                "job_finished",
                extra={
                    "ctx_job": job.id,
                    "ctx_tenant": job.tenant,
                    "ctx_status": job.status.value,
                    "ctx_elapsed": elapsed,
                },
            )


__all__ = ["SchedulerService"]
