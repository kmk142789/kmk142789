from __future__ import annotations

import json
import threading
import time
from http.client import HTTPConnection

from vault_api import build_server


def run_server(server):
    with server:
        server.serve_forever()


def request(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    host, port = "127.0.0.1", request.port
    conn = HTTPConnection(host, port, timeout=5)
    headers = {"Content-Type": "application/json"}
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    conn.request(method, path, body=payload, headers=headers if payload else {})
    response = conn.getresponse()
    data = json.loads(response.read().decode("utf-8"))
    conn.close()
    return response.status, data


def setup_module(module):
    server = build_server("127.0.0.1", 0)
    request.port = server.server_address[1]
    thread = threading.Thread(target=run_server, args=(server,), daemon=True)
    thread.start()
    time.sleep(0.1)
    module._server = server
    module._thread = thread


def teardown_module(module):
    module._server.shutdown()
    module._thread.join(timeout=1)


def test_store_and_query_cycle():
    status, payload = request("POST", "/vault/items", {"content": "alpha", "metadata": {"tag": "demo"}})
    assert status == 201
    first_address = payload["address"]
    assert payload["version"] == 1

    status, payload = request("POST", "/vault/items", {"content": "alpha", "metadata": {"owner": "qa"}})
    assert status == 201
    assert payload["address"] == first_address
    assert payload["version"] == 2

    status, payload = request("GET", "/vault/items?tag=demo")
    assert status == 200
    assert payload["items"]
    assert payload["items"][0]["address"] == first_address

    status, payload = request("GET", "/vault/integrity")
    assert status == 200
    assert payload["scanned"] >= 1

    status, payload = request("GET", "/vault/history")
    assert status == 200
    assert len(payload["history"]) >= 2


def test_config_endpoint_reflects_version():
    status, payload = request("GET", "/vault/config")
    assert status == 200
    assert payload["version"] == 2
