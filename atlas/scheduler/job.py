"""Job specification and retry policy definitions."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 5.0
    backoff_factor: float = 2.0
    max_delay: float = 300.0
    jitter: float = 1.0

    def next_delay(self, attempt: int) -> float:
        delay = min(self.initial_delay * (self.backoff_factor ** (attempt - 1)), self.max_delay)
        if self.jitter:
            jitter = ((attempt * 9301 + 49297) % 233280) / 233280.0
            delay += (jitter - 0.5) * self.jitter
        return max(0.0, delay)


@dataclass(slots=True)
class Job:
    id: str
    tenant: str
    payload: Dict[str, Any]
    schedule_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: JobStatus = JobStatus.PENDING
    attempts: int = 0
    last_error: Optional[str] = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    runtime_limit: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_record(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant": self.tenant,
            "payload": json.dumps(self.payload, sort_keys=True),
            "schedule_at": self.schedule_at.isoformat(),
            "status": self.status.value,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "retry_policy": json.dumps(asdict(self.retry_policy), sort_keys=True),
            "runtime_limit": self.runtime_limit,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_record(cls, record: Dict[str, Any]) -> "Job":
        return cls(
            id=record["id"],
            tenant=record["tenant"],
            payload=json.loads(record["payload"]),
            schedule_at=datetime.fromisoformat(record["schedule_at"]),
            status=JobStatus(record["status"]),
            attempts=record["attempts"],
            last_error=record.get("last_error"),
            retry_policy=RetryPolicy(**json.loads(record["retry_policy"])),
            runtime_limit=record.get("runtime_limit"),
            created_at=datetime.fromisoformat(record["created_at"]),
            updated_at=datetime.fromisoformat(record["updated_at"]),
        )

    def schedule_next(self) -> None:
        self.attempts += 1
        delay = self.retry_policy.next_delay(self.attempts)
        self.schedule_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        self.status = JobStatus.PENDING


__all__ = ["Job", "JobStatus", "RetryPolicy"]
