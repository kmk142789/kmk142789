"""HTTP server bootstrap for the content vault API."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict
from urllib.parse import parse_qs, urlparse

from .config import load_config
from .routers.vault import VaultRouter
from .services.metadata import ChangeJournal, MetadataIndex
from .services.storage import ContentAddressableStore


def _build_router() -> VaultRouter:
    store = ContentAddressableStore()
    index = MetadataIndex()
    journal = ChangeJournal()
    return VaultRouter(store=store, index=index, journal=journal)


class RequestHandler(BaseHTTPRequestHandler):
    router = _build_router()
    config = load_config(os.environ.get("VAULT_CONFIG_PATH"))

    def _write_json(self, status: HTTPStatus, payload: Dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler requirement)
        parsed = urlparse(self.path)
        if parsed.path == "/vault/items":
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            try:
                status, payload = self.router.handle_post_items(raw)
                self._write_json(HTTPStatus(status), payload)
            except ValueError as exc:
                status, payload = self.router.error(str(exc))
                self._write_json(HTTPStatus(status), payload)
        else:
            status, payload = self.router.error("unknown route", HTTPStatus.NOT_FOUND)
            self._write_json(HTTPStatus(status), payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        if parsed.path == "/vault/items":
            status, payload = self.router.handle_get_items(query)
        elif parsed.path == "/vault/history":
            status, payload = self.router.handle_get_history()
        elif parsed.path == "/vault/integrity":
            status, payload = self.router.handle_get_integrity()
        elif parsed.path == "/vault/config":
            status = HTTPStatus.OK
            payload = {"config": self.config, "version": self.config.get("version")}
        else:
            status, payload = self.router.error("unknown route", HTTPStatus.NOT_FOUND)
        self._write_json(HTTPStatus(status), payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Reduce noise in tests by suppressing default logging.
        return


def build_server(host: str = "127.0.0.1", port: int = 8080) -> HTTPServer:
    return HTTPServer((host, port), RequestHandler)


def serve_forever(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = build_server(host, port)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    serve_forever(
        host=os.environ.get("VAULT_HOST", "127.0.0.1"),
        port=int(os.environ.get("VAULT_PORT", "8080")),
    )
