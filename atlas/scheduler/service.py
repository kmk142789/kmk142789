"""Scheduler service orchestrating job execution."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import perf_counter
from typing import Awaitable, Callable, Dict, Optional

from atlas.core.logging import get_logger
from atlas.core.service import Service
from opentelemetry import metrics, trace
from opentelemetry.trace import Status, StatusCode

from .job import Job, JobStatus
from .store import JobStore


_meter = metrics.get_meter("atlas.scheduler")
_tracer = trace.get_tracer("atlas.scheduler")
_jobs_started = _meter.create_counter(
    "atlas_jobs_started_total",
    description="Number of jobs dispatched for execution.",
)
_jobs_completed = _meter.create_counter(
    "atlas_jobs_completed_total",
    description="Number of jobs that completed successfully.",
)
_jobs_failed = _meter.create_counter(
    "atlas_jobs_failed_total",
    description="Number of jobs that exhausted retries or failed execution.",
)
_active_jobs = _meter.create_up_down_counter(
    "atlas_jobs_active",
    description="Current number of in-flight jobs handled by the scheduler.",
)
_job_duration = _meter.create_histogram(
    "atlas_job_duration_seconds",
    unit="s",
    description="Observed runtime for executed jobs.",
)


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
        attributes = {
            "atlas.job.id": job.id,
            "atlas.job.tenant": job.tenant,
            "atlas.job.payload_type": str(job.payload.get("type", "unknown")),
        }
        _jobs_started.add(1, attributes=attributes)
        _active_jobs.add(1, attributes=attributes)
        timer = perf_counter()
        started_at = datetime.now(timezone.utc)
        span_attributes = {
            "atlas.job.id": job.id,
            "atlas.job.tenant": job.tenant,
            "atlas.job.payload_type": attributes["atlas.job.payload_type"],
        }
        with _tracer.start_as_current_span("atlas.scheduler.execute", attributes=span_attributes) as span:
            try:
                if job.runtime_limit:
                    await asyncio.wait_for(self.executor(job), timeout=job.runtime_limit)
                else:
                    await self.executor(job)
            except asyncio.TimeoutError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, "runtime_limit_exceeded"))
                job.attempts += 1
                job.last_error = "runtime_limit_exceeded"
                if job.attempts >= job.retry_policy.max_attempts:
                    job.status = JobStatus.DEAD_LETTER
                    self.store.upsert(job)
                    _jobs_failed.add(1, attributes=attributes)
                else:
                    job.schedule_next()
                    self.store.upsert(job)
            except Exception as exc:  # pragma: no cover - executor failure path
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, "executor_failure"))
                job.attempts += 1
                job.last_error = repr(exc)
                if job.attempts >= job.retry_policy.max_attempts:
                    job.status = JobStatus.DEAD_LETTER
                    self.store.upsert(job)
                    _jobs_failed.add(1, attributes=attributes)
                else:
                    job.schedule_next()
                    self.store.upsert(job)
            else:
                job.status = JobStatus.COMPLETED
                job.updated_at = datetime.now(timezone.utc)
                self.store.upsert(job)
                _jobs_completed.add(1, attributes=attributes)
            finally:
                elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
                duration = perf_counter() - timer
                _job_duration.record(duration, attributes=attributes)
                _active_jobs.add(-1, attributes=attributes)
                span.set_attribute("atlas.job.duration.seconds", duration)
                span.set_attribute("atlas.job.status", job.status.value)
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
