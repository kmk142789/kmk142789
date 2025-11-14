from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import pytest
import requests


def _scenario_directory() -> Path:
    env_value = os.environ.get("E2E_SCENARIO_DIR")
    if env_value:
        return Path(env_value)
    return Path(__file__).parent / "scenarios"


def _load_scenarios() -> list[tuple[str, dict[str, object], Path]]:
    directory = _scenario_directory()
    scenarios: list[tuple[str, dict[str, object], Path]] = []
    for path in sorted(directory.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name") or path.stem
        data.setdefault("name", name)
        scenarios.append((name, data, path))
    if not scenarios:
        raise FileNotFoundError(f"No scenarios discovered in {directory}")
    return scenarios


_SCENARIOS = _load_scenarios()
_SCENARIO_IDS = [name for name, _, _ in _SCENARIOS]


@pytest.fixture(scope="session")
def e2e_artifact_dir() -> Path:
    env_value = os.environ.get("E2E_ARTIFACT_DIR")
    if env_value:
        path = Path(env_value)
        path.mkdir(parents=True, exist_ok=True)
        return path
    temp_dir = Path(tempfile.mkdtemp(prefix="e2e-artifacts-"))
    return temp_dir


def _apply_base_url_overrides(name: str, default_url: str) -> str:
    override = os.environ.get("E2E_BASE_URL")
    if override:
        return override.rstrip("/")
    scoped_key = f"E2E_BASE_URL_{name.upper().replace('-', '_')}"
    scoped_value = os.environ.get(scoped_key)
    if scoped_value:
        return scoped_value.rstrip("/")
    return default_url.rstrip("/")


def _truncate_body(body: str, limit: int = 4096) -> str:
    if len(body) <= limit:
        return body
    return body[:limit] + "...<truncated>"


@pytest.mark.parametrize("name,data,path", _SCENARIOS, ids=_SCENARIO_IDS)
def test_scenario(name: str, data: dict[str, object], path: Path, e2e_artifact_dir: Path) -> None:
    base_url_value = data.get("base_url")
    if not isinstance(base_url_value, str):
        raise AssertionError(f"Scenario {name} is missing a base_url")
    base_url = _apply_base_url_overrides(name, base_url_value)
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise AssertionError(f"Scenario {name} does not define any steps")

    session = requests.Session()
    results: list[dict[str, object]] = []

    try:
        for index, raw_step in enumerate(steps):
            if not isinstance(raw_step, dict):
                raise AssertionError(f"Scenario {name} step {index} is not a mapping")
            method = str(raw_step.get("method", "")).upper()
            path_fragment = str(raw_step.get("path", ""))
            timeout = float(raw_step.get("timeout", 15.0))
            expected_status = int(raw_step.get("expected_status", 200))
            url = urljoin(base_url + "/", path_fragment.lstrip("/"))

            kwargs: dict[str, object] = {}
            if "body" in raw_step:
                kwargs["json"] = raw_step["body"]
            if "headers" in raw_step:
                kwargs["headers"] = raw_step["headers"]
            if "params" in raw_step:
                kwargs["params"] = raw_step["params"]

            started = time.perf_counter()
            response = session.request(method, url, timeout=timeout, **kwargs)
            duration_ms = (time.perf_counter() - started) * 1000.0

            assert (
                response.status_code == expected_status
            ), f"{name} step {raw_step.get('name', path_fragment)} expected status {expected_status} but received {response.status_code}"

            if "expected_keys" in raw_step:
                payload = response.json()
                missing = [key for key in raw_step["expected_keys"] if key not in payload]
                assert not missing, f"{name} step {raw_step.get('name', path_fragment)} missing keys: {missing}"

            if "expected_text" in raw_step:
                expected_texts: Iterable[str]
                if isinstance(raw_step["expected_text"], str):
                    expected_texts = [raw_step["expected_text"]]
                else:
                    expected_texts = raw_step["expected_text"]  # type: ignore[assignment]
                for snippet in expected_texts:
                    assert isinstance(snippet, str)
                    assert (
                        snippet in response.text
                    ), f"{name} step {raw_step.get('name', path_fragment)} expected response to contain {snippet!r}"

            results.append(
                {
                    "step": raw_step.get("name", f"step-{index}"),
                    "method": method,
                    "url": url,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "response_headers": dict(response.headers),
                    "response_preview": _truncate_body(response.text),
                }
            )
    finally:
        session.close()

    artifact_path = e2e_artifact_dir / f"{name}_results.json"
    artifact_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    metadata = {
        "scenario": name,
        "definition": str(path.resolve()),
        "base_url": base_url,
        "steps": len(results),
    }
    (e2e_artifact_dir / f"{name}_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
