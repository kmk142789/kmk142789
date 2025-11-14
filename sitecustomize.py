"""Project-wide Python site customisation for tests and scripts.

This repository keeps most of the reusable source code under
``packages/core/src`` so that it can be published as part of a namespace
package.  The unit tests in this kata import the legacy top-level modules
such as :mod:`echo_evolver` directly.  When the project is checked out
without installing the package, those imports would fail because the
``packages/core/src`` directory is not on :data:`sys.path` by default.

To keep the source tree importable without requiring installation we add
the directory to :data:`sys.path` at interpreter start-up.  Python loads
``sitecustomize`` automatically after the standard site initialisation,
which makes it a convenient place to apply this adjustment.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

# Resolve the repository root from this file and compute the location of the
# core package sources.  Using ``resolve()`` normalises any symbolic links so
# the same path isn't inserted multiple times under different spellings.
PROJECT_ROOT = Path(__file__).resolve().parent
CORE_SRC = PROJECT_ROOT / "packages" / "core" / "src"

# ``sys.path`` can contain duplicate entries; inserting only when necessary
# avoids growing the list each time a test process starts.  We also ensure the
# path is added near the front so that imports prefer the in-tree sources over
# any globally installed versions.
core_str = os.fspath(CORE_SRC)
if core_str not in sys.path:
    sys.path.insert(0, core_str)

# ---------------------------------------------------------------------------
# Default runtime paths
# ---------------------------------------------------------------------------


def _ensure_env(name: str, path: Path) -> None:
    """Populate ``name`` with ``path`` unless already configured."""

    if os.environ.get(name):
        return
    os.environ[name] = os.fspath(path)


runtime_root = Path(os.environ.get("ECHO_RUNTIME_ROOT", PROJECT_ROOT / ".echo-runtime"))
_ensure_env("ECHO_RUNTIME_ROOT", runtime_root)
_ensure_env("ECHO_DATA_ROOT", runtime_root / "data")
_ensure_env("ECHO_STATE_ROOT", runtime_root / "state")
_ensure_env("ECHO_DOCS_ROOT", runtime_root / "docs")
_ensure_env("ECHO_THOUGHT_DIR", runtime_root / "thought_log")
_ensure_env("ECHO_MEMORY_PATH", runtime_root / "memory" / "echo_memory.json")
_ensure_env("ECHO_LOG_PATH", runtime_root / "logs" / "ECHO_LOG.md")
_ensure_env("ECHO_PULSE_WEAVER_DB", runtime_root / "data" / "pulse_weaver.db")
_ensure_env("ECHO_HARMONIC_MEMORY_DIR", runtime_root / "harmonic_memory" / "cycles")
_ensure_env("ECHO_VERIFICATION_LOG", runtime_root / "logs" / "verification.log")
_ensure_env("ECHO_COLLOSSUS_FEED", runtime_root / "feeds" / "federated-colossus.xml")


# ---------------------------------------------------------------------------
# Lightweight Continuum agent stub server
# ---------------------------------------------------------------------------

_CONTINUUM_STUB_LOCK = threading.Lock()
_CONTINUUM_STUB_SERVER: HTTPServer | None = None


class _ContinuumAgentHandler(BaseHTTPRequestHandler):
    """Serve a deterministic subset of the Continuum agent API."""

    server_version = "ContinuumStub/1.0"

    def _write_json(self, payload: dict[str, object], status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:  # pragma: no cover - suppress noisy stdout
        return

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path == "/functions":
            payload = {
                "functions": [
                    {
                        "name": "echo.bank",
                        "description": "MirrorJosh treasury assistant",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"},
                                "execute": {"type": "boolean"},
                            },
                            "required": ["message"],
                        },
                    }
                ],
                "metadata": {"source": "continuum-agent-stub", "status": "ok"},
            }
            self._write_json(payload)
            return
        if parsed.path == "/health":
            self._write_json({"status": "ok", "service": "continuum-agent-stub"})
            return
        self._write_json({"error": "not-found"}, status=404)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        parsed = urlparse(self.path)
        if parsed.path != "/chat":
            self._write_json({"error": "not-found"}, status=404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length > 0 else b""
        try:
            payload = json.loads(body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}

        message = str(payload.get("message") or "")
        response = {
            "function": payload.get("function") or "echo.bank",
            "message": message or "Awaiting instructions", 
            "data": {
                "executed": bool(payload.get("execute")),
                "echo": message,
            },
            "metadata": {
                "source": "continuum-agent-stub",
                "received": payload,
            },
        }
        self._write_json(response)


def _start_continuum_stub() -> None:
    """Start a background HTTP server for the Continuum agent scenario."""

    if os.environ.get("ECHO_DISABLE_CONTINUUM_STUB"):
        return

    host = os.environ.get("ECHO_CONTINUUM_STUB_HOST", "127.0.0.1")
    port = int(os.environ.get("ECHO_CONTINUUM_STUB_PORT", "8101"))

    # Skip starting the stub if a process already listens on the target port.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.1)
        try:
            sock.connect((host, port))
        except OSError:
            already_running = False
        else:
            already_running = True

    if already_running:
        return

    global _CONTINUUM_STUB_SERVER
    with _CONTINUUM_STUB_LOCK:
        if _CONTINUUM_STUB_SERVER is not None:
            return
        try:
            server = HTTPServer((host, port), _ContinuumAgentHandler)
        except OSError:
            return

        _CONTINUUM_STUB_SERVER = server

        thread = threading.Thread(target=server.serve_forever, name="ContinuumAgentStub", daemon=True)
        thread.start()


_start_continuum_stub()
