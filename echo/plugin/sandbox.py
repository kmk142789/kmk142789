"""Sandboxed execution environment for plugins."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from .manifest import load_manifest
from .spec import PluginManifest


class Sandbox:
    """Launch and communicate with a plugin process using JSON-RPC over stdio."""

    def __init__(self, manifest_path: str | Path):
        self.manifest = load_manifest(manifest_path)
        entry = Path(self.manifest.entrypoint)
        if not entry.is_absolute():
            entry = Path(manifest_path).resolve().parent / entry
        if not entry.exists():
            raise FileNotFoundError(entry)
        self.proc = subprocess.Popen(
            [sys.executable, str(entry)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        if self.proc.stdin is None or self.proc.stdout is None:
            raise RuntimeError("Failed to create plugin sandbox pipes")

    def call(self, method: str, params: Iterable[Any] | None = None) -> Any:
        payload = {"jsonrpc": "2.0", "id": "1", "method": method, "params": list(params or [])}
        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError("Plugin terminated unexpectedly")
        response = json.loads(line)
        if "error" in response:
            raise RuntimeError(response["error"])
        return response.get("result")

    def capabilities(self) -> list[str]:
        return list(self.manifest.capabilities)

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
        if self.proc.stdin:
            self.proc.stdin.close()
        if self.proc.stdout:
            self.proc.stdout.close()

    def __enter__(self) -> "Sandbox":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


__all__ = ["Sandbox", "PluginManifest", "load_manifest", "main"]


def main(argv: Iterable[str] | None = None) -> int:  # pragma: no cover - CLI helper
    parser = argparse.ArgumentParser(description="Run an Echo plugin in a sandbox")
    parser.add_argument("manifest", type=str, help="Path to the plugin manifest")
    args = parser.parse_args(list(argv) if argv is not None else None)

    with Sandbox(args.manifest) as sandbox:
        print("capabilities:", ", ".join(sandbox.capabilities()))
        print("ping:", sandbox.call("echo.ping"))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI helper
    raise SystemExit(main())
