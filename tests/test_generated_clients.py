"""Smoke tests for the generated API clients."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict

import pytest

from clients.python.echo_computer_agent_client.echo_computer_agent_client import (
    EchoComputerAgentClient,
)


class _MockAgentHandler(BaseHTTPRequestHandler):
    function_payload: Dict[str, object] = {
        "functions": [
            {
                "name": "launch_application",
                "description": "Describe how to launch an Echo application.",
                "parameters": {"type": "object"},
                "metadata": {"category": "operations"},
            }
        ]
    }
    chat_payload: Dict[str, object] = {
        "function": "launch_application",
        "message": "launching echo.bank",
        "data": {"application": "echo.bank", "status": "ok"},
        "metadata": {"confidence": 1.0},
    }

    def do_GET(self) -> None:  # noqa: N802 - inherited name
        if self.path == "/functions":
            body = json.dumps(self.function_payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802 - inherited name
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            response = dict(self.chat_payload)
            if payload.get("message", "").lower().startswith("solve"):
                response.update({
                    "function": "solve_puzzle",
                    "message": "solved",
                })
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - signature defined by BaseHTTPRequestHandler
        # Silence noisy server logging during tests.
        return


@pytest.fixture(scope="module")
def mock_agent_server() -> str:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockAgentHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    # Give the server a short moment to start accepting connections.
    time.sleep(0.1)
    yield base_url
    server.shutdown()
    thread.join(timeout=5)


def test_python_client_smoke(mock_agent_server: str) -> None:
    client = EchoComputerAgentClient(mock_agent_server)
    try:
        functions = client.list_functions()
        assert functions["functions"], "function list should not be empty"
        response = client.chat("Launch echo.bank", execute=True)
        assert response["function"] == "launch_application"
    finally:
        client.close()


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Node invocation path differs on Windows")
def test_typescript_client_smoke(mock_agent_server: str) -> None:
    project_dir = Path("clients/typescript/echo-computer-agent-client").resolve()
    env = os.environ.copy()
    subprocess.run([
        "npx",
        "--yes",
        "tsc",
        "-p",
        str(project_dir),
    ], check=True, env=env)

    script = f"""
import {{ EchoComputerAgentClient }} from '{(project_dir / 'dist' / 'index.js').as_uri()}';
const client = new EchoComputerAgentClient('{mock_agent_server}');
const functions = await client.listFunctions();
if (!Array.isArray(functions.functions) || functions.functions.length === 0) {{
  throw new Error('empty function list');
}}
const chat = await client.chat({{ message: 'launch echo.bank', execute: true }});
if (chat.function !== 'launch_application') {{
  throw new Error('unexpected function: ' + chat.function);
}}
"""
    subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        env=env,
    )


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Go smoke harness uses POSIX paths")
def test_go_client_smoke(mock_agent_server: str) -> None:
    go_dir = Path("clients/go/echo_computer_agent_client").resolve()
    env = os.environ.copy()
    env.setdefault("GO111MODULE", "on")
    subprocess.run(
        [
            "go",
            "run",
            "./cmd/smoke",
            "-base-url",
            mock_agent_server,
        ],
        cwd=go_dir,
        check=True,
        env=env,
    )
