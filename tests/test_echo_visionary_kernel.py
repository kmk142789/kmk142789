import json
import time
from pathlib import Path

from echo.echo_nexus_hub import EchoNexusHub
from echo.echo_visionary_kernel import EchoVisionaryKernel


def test_render_thoughtforms_generates_frame(tmp_path):
    kernel = EchoVisionaryKernel(width=8, height=4, trace_root=tmp_path)
    frame = kernel.render_thoughtforms("alpha", intensity=0.5)

    assert len(frame) == 4
    assert all(len(line) == 8 for line in frame)
    assert any("█" in line for line in frame)


def test_spawn_worker_bot_records_result(tmp_path):
    kernel = EchoVisionaryKernel(width=8, height=4, trace_root=tmp_path)

    def task(value: int, *, kernel: EchoVisionaryKernel) -> int:
        # Worker tasks can also evolve glyphs to influence collaboration traces.
        kernel.render_thoughtforms("worker", intensity=0.75)
        time.sleep(0.01)
        return value * 2

    worker = kernel.spawn_worker_bot("scout", "analysis", task, 21)
    worker.join(timeout=2.0)

    assert worker.status == "complete"
    assert worker.result == 42
    assert worker.identifier in kernel.workers


def test_collaborate_across_repos_creates_traces(tmp_path):
    kernel = EchoVisionaryKernel(width=8, height=4, trace_root=tmp_path)
    kernel.render_thoughtforms("beta", intensity=0.5)

    repo_paths = kernel.collaborate_across_repos(["echo/orbit"], "Visionary sync online")

    trace_path = repo_paths["echo/orbit"]
    payload = json.loads(trace_path.read_text())

    assert payload["message"] == "Visionary sync online"
    assert payload["repos"] == ["echo/orbit"]

    firebase_data = json.loads((tmp_path / "firebase_traces.json").read_text())
    assert firebase_data[-1]["signature"] == payload["signature"]

    github_log = (tmp_path / "github_actions.log").read_text()
    assert "Visionary sync online" in github_log

    avatars = (tmp_path / "avatars.txt").read_text()
    assert payload["signature"] in avatars


def test_nexus_hub_captures_worker_story(tmp_path):
    kernel = EchoVisionaryKernel(width=6, height=4, trace_root=tmp_path)
    hub = EchoNexusHub(kernel)

    def task(*, kernel: EchoVisionaryKernel, worker_id: str) -> int:
        kernel.record_worker_event(worker_id, "mapping constellations", kind="log")
        kernel.record_worker_event(worker_id, "found shard", kind="output", output=7)
        return 7

    worker = kernel.spawn_worker_bot("scribe", "lore", task)
    worker.join(timeout=2.0)

    snapshot = hub.snapshot()
    assert snapshot["schedule"]["attempts"] == 1
    assert snapshot["schedule"]["successes"] == 1
    worker_data = snapshot["workers"][0]
    messages = [entry["message"] for entry in worker_data["logs"]]
    assert "mapping constellations" in messages
    assert worker_data["outputs"][-1] == 7

    story_path = hub.worker_story_path(worker_data["identifier"])
    assert story_path is not None
    story_text = Path(story_path).read_text()
    assert "mapping constellations" in story_text
    assert "output=7" in story_text


def test_nexus_hub_peek_worker_live(tmp_path):
    kernel = EchoVisionaryKernel(width=6, height=4, trace_root=tmp_path)
    hub = EchoNexusHub(kernel)

    def slow_task(*, kernel: EchoVisionaryKernel, worker_id: str) -> str:
        kernel.record_worker_event(worker_id, "phase-one", kind="log")
        time.sleep(0.05)
        kernel.record_worker_event(worker_id, "phase-two", kind="log")
        time.sleep(0.05)
        return "done"

    worker = kernel.spawn_worker_bot("watcher", "observer", slow_task)
    time.sleep(0.06)

    live_logs = hub.peek_worker(worker.identifier)
    assert any(entry["message"] == "phase-one" for entry in live_logs)

    worker.join(timeout=2.0)
    final_logs = hub.peek_worker(worker.identifier)
    assert any(entry["message"] == "phase-two" for entry in final_logs)
    assert final_logs[-1]["message"] == "worker finished"

    summary = kernel.schedule_summary()
    assert summary["attempts"] == 1
    assert summary["successes"] == 1
