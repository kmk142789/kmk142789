"""Supervisor orchestration for multiple services."""
from __future__ import annotations

import asyncio
from typing import Iterable, List

from .logging import get_logger
from .service import Service


class Supervisor:
    def __init__(self, services: Iterable[Service]):
        self.services: List[Service] = list(services)
        self.logger = get_logger("atlas.supervisor")

    async def start(self) -> None:
        await asyncio.gather(*(svc.start() for svc in self.services))
        self.logger.info("supervisor_started", extra={"ctx_services": [svc.name for svc in self.services]})

    async def stop(self) -> None:
        await asyncio.gather(*(svc.stop() for svc in self.services))
        self.logger.info("supervisor_stopped")

    async def run(self) -> None:
        await self.start()
        try:
            await asyncio.gather(*(
                svc._task for svc in self.services if svc._task is not None
            ))
        finally:
            await self.stop()


__all__ = ["Supervisor"]
