import json
import time

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
