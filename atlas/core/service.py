"""Service lifecycle primitives."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum, auto
from typing import AsyncIterator, Awaitable, Callable, Optional

from .logging import get_logger


class ServiceState(Enum):
    INIT = auto()
    RUNNING = auto()
    STOPPED = auto()


@dataclass
class Service:
    name: str
    _task: Optional[asyncio.Task] = None
    _state: ServiceState = ServiceState.INIT

    async def start(self) -> None:
        if self._state is not ServiceState.INIT:
            return
        self._state = ServiceState.RUNNING
        self._task = asyncio.create_task(self.run(), name=self.name)

    async def run(self) -> None:  # pragma: no cover - to be implemented by subclasses
        raise NotImplementedError

    async def stop(self) -> None:
        if self._state is ServiceState.STOPPED:
            return
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._state = ServiceState.STOPPED


@asynccontextmanager
async def graceful(service: Service) -> AsyncIterator[Service]:
    logger = get_logger(service.name)
    await service.start()
    logger.debug("service_started")
    try:
        yield service
    finally:
        await service.stop()
        logger.debug("service_stopped")


async def run_supervised(factory: Callable[[], Service]) -> None:
    service = factory()
    async with graceful(service):
        if service._task is not None:
            await service._task


__all__ = ["Service", "ServiceState", "graceful", "run_supervised"]
