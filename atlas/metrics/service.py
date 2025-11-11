"""Metrics service exposing Prometheus and websocket feeds."""
from __future__ import annotations

import asyncio
import json
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

from atlas.core.logging import get_logger
from atlas.core.service import Service

from .registry import MetricsRegistry


class MetricsService(Service):
    def __init__(self, registry: MetricsRegistry, host: str = "0.0.0.0", port: int = 9100, ws_port: int = 9101):
        super().__init__("atlas.metrics")
        self.registry = registry
        self.host = host
        self.port = port
        self.ws_port = ws_port
        self.logger = get_logger(self.name)
        self._websockets: Set[WebSocketServerProtocol] = set()
        self._http_server: asyncio.base_events.Server | None = None
        self._ws_server: websockets.server.Serve | None = None

    async def run(self) -> None:
        self._http_server = await asyncio.start_server(self._handle_http, host=self.host, port=self.port)
        self._ws_server = await websockets.serve(self._handle_ws, self.host, self.ws_port)
        self.logger.info("metrics_listening", extra={"ctx_port": self.port, "ctx_ws_port": self.ws_port})
        try:
            await self._http_server.serve_forever()
        finally:
            await self._shutdown()

    async def _handle_http(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.read(1024)
        data = await self.registry.export_prometheus()
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain; version=0.0.4\r\n"
            f"Content-Length: {len(data)}\r\n"
            "Connection: close\r\n\r\n"
            f"{data}"
        )
        writer.write(response.encode("utf-8"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def _handle_ws(self, socket: WebSocketServerProtocol) -> None:
        self._websockets.add(socket)
        try:
            await socket.send(json.dumps(await self.registry.snapshot()))
            async for _ in socket:
                await socket.send(json.dumps(await self.registry.snapshot()))
        finally:
            self._websockets.discard(socket)

    async def broadcast(self) -> None:
        if not self._websockets:
            return
        payload = json.dumps(await self.registry.snapshot())
        await asyncio.gather(*(ws.send(payload) for ws in list(self._websockets)))

    async def _shutdown(self) -> None:
        if self._ws_server:
            self._ws_server.ws_server.close()
            await self._ws_server.ws_server.wait_closed()
        if self._http_server:
            self._http_server.close()
            await self._http_server.wait_closed()


__all__ = ["MetricsService"]
