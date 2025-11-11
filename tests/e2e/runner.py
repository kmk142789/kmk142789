from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import urlparse

DEFAULT_COMPOSE_FILE = Path("docker-compose.federation.yml")


class CommandError(RuntimeError):
    """Raised when an expected external command is not available."""


@dataclass
class StackController:
    """Base class for launching and tearing down an environment stack."""

    def start(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def wait_until_ready(self, endpoints: Sequence[tuple[str, int]], timeout: float) -> None:
        _wait_for_endpoints(endpoints, timeout=timeout)

    def collect_artifacts(self, destination: Path) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def stop(self) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class ComposeStack(StackController):
    compose_file: Path
    project_name: str
    build: bool = False

    def __post_init__(self) -> None:
        if shutil.which("docker") is None:
            raise CommandError("docker executable is required to launch the compose stack")

    def _base_cmd(self) -> list[str]:
        return [
            "docker",
            "compose",
            "-f",
            str(self.compose_file),
            "-p",
            self.project_name,
        ]

    def start(self) -> None:
        args = self._base_cmd() + ["up", "-d"]
        if self.build:
            args.append("--build")
        subprocess.run(args, check=True)

    def collect_artifacts(self, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        log_path = destination / "compose.log"
        with log_path.open("w", encoding="utf-8") as handle:
            subprocess.run(self._base_cmd() + ["logs"], stdout=handle, stderr=subprocess.STDOUT, check=False)
        ps_path = destination / "compose-services.txt"
        with ps_path.open("w", encoding="utf-8") as handle:
            subprocess.run(self._base_cmd() + ["ps"], stdout=handle, stderr=subprocess.STDOUT, check=False)

    def stop(self) -> None:
        subprocess.run(self._base_cmd() + ["down", "--volumes", "--remove-orphans"], check=False)


@dataclass
class KindStack(StackController):
    cluster_name: str
    manifest: Path | None = None
    keep_cluster: bool = False

    def __post_init__(self) -> None:
        if shutil.which("kind") is None:
            raise CommandError("kind executable is required to launch the kubernetes stack")
        if shutil.which("kubectl") is None:
            raise CommandError("kubectl executable is required when using the kind stack")
        self._created_cluster = False

    def start(self) -> None:
        clusters = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True, check=False)
        existing = set(clusters.stdout.split())
        if self.cluster_name not in existing:
            subprocess.run(["kind", "create", "cluster", "--name", self.cluster_name], check=True)
            self._created_cluster = True
        if self.manifest is not None:
            subprocess.run(["kubectl", "apply", "-f", str(self.manifest)], check=True)

    def collect_artifacts(self, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=True)
        summary = destination / "kubectl-resources.txt"
        with summary.open("w", encoding="utf-8") as handle:
            subprocess.run(["kubectl", "get", "all", "-A", "-o", "wide"], stdout=handle, stderr=subprocess.STDOUT, check=False)

    def stop(self) -> None:
        if self.manifest is not None:
            subprocess.run(["kubectl", "delete", "-f", str(self.manifest)], check=False)
        if self._created_cluster and not self.keep_cluster:
            subprocess.run(["kind", "delete", "cluster", "--name", self.cluster_name], check=False)


def _wait_for_endpoints(endpoints: Iterable[tuple[str, int]], timeout: float) -> None:
    start = time.monotonic()
    pending = set(endpoints)
    while pending:
        now = time.monotonic()
        if now - start > timeout:
            remaining = ", ".join(f"{host}:{port}" for host, port in sorted(pending))
            raise TimeoutError(f"Timed out waiting for endpoints: {remaining}")
        ready: set[tuple[str, int]] = set()
        for host, port in pending:
            try:
                with socket.create_connection((host, port), timeout=3):
                    ready.add((host, port))
            except OSError:
                continue
        pending -= ready
        if pending:
            time.sleep(1)


def _discover_endpoints(scenario_dir: Path) -> list[tuple[str, int]]:
    endpoints: set[tuple[str, int]] = set()
    for path in sorted(scenario_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        base_url = data.get("base_url")
        if not isinstance(base_url, str):
            continue
        parsed = urlparse(base_url)
        host = parsed.hostname or "127.0.0.1"
        if parsed.port is not None:
            port = parsed.port
        elif parsed.scheme == "https":
            port = 443
        else:
            port = 80
        endpoints.add((host, port))
    return sorted(endpoints)


def _run_pytest(artifact_dir: Path, scenario_dir: Path, extra_args: Sequence[str]) -> int:
    junit_path = artifact_dir / "pytest-e2e.xml"
    env = os.environ.copy()
    env["E2E_SCENARIO_DIR"] = str(scenario_dir)
    env["E2E_ARTIFACT_DIR"] = str(artifact_dir)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/e2e",
        "--junitxml",
        str(junit_path),
        *extra_args,
    ]
    result = subprocess.run(cmd, env=env)
    return result.returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="End-to-end test runner")
    parser.add_argument("--stack", choices=["compose", "kind"], default="compose", help="Stack orchestration backend to use")
    parser.add_argument("--compose-file", type=Path, default=DEFAULT_COMPOSE_FILE, help="Path to the docker compose file")
    parser.add_argument("--compose-project", default=f"echo-e2e-{int(time.time())}", help="Docker compose project name")
    parser.add_argument("--compose-build", action="store_true", help="Build compose services before starting")
    parser.add_argument("--kind-cluster", default="echo-e2e", help="Kind cluster name to create or reuse")
    parser.add_argument("--kind-manifest", type=Path, help="Optional manifest applied after the cluster is ready")
    parser.add_argument("--keep-kind", action="store_true", help="Keep the kind cluster after the test run")
    parser.add_argument("--scenario-dir", type=Path, default=Path("tests/e2e/scenarios"), help="Directory containing scenario definitions")
    parser.add_argument("--artifact-dir", type=Path, help="Directory to store artifacts; defaults to artifacts/e2e/<timestamp>")
    parser.add_argument("--timeout", type=float, default=180.0, help="Maximum time to wait for service endpoints to become ready")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Additional arguments passed through to pytest")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    artifact_dir = args.artifact_dir
    if artifact_dir is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        artifact_dir = Path("artifacts") / "e2e" / timestamp
    artifact_dir.mkdir(parents=True, exist_ok=True)

    scenario_dir = args.scenario_dir
    if not scenario_dir.exists():
        raise FileNotFoundError(f"Scenario directory {scenario_dir} does not exist")

    endpoints = _discover_endpoints(scenario_dir)

    try:
        if args.stack == "compose":
            stack: StackController = ComposeStack(
                compose_file=args.compose_file,
                project_name=args.compose_project,
                build=args.compose_build,
            )
        else:
            stack = KindStack(
                cluster_name=args.kind_cluster,
                manifest=args.kind_manifest,
                keep_cluster=args.keep_kind,
            )
    except CommandError as exc:
        print(f"[e2e] {exc}", file=sys.stderr)
        return 2

    try:
        stack.start()
        if endpoints:
            stack.wait_until_ready(endpoints, timeout=args.timeout)
        return_code = _run_pytest(artifact_dir, scenario_dir, args.pytest_args or [])
    finally:
        try:
            stack.collect_artifacts(artifact_dir)
        finally:
            stack.stop()

    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
