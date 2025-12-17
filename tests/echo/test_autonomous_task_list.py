import json

from echo.autonomous_task_list import AutonomousTaskList
from echo.memory.store import JsonMemoryStore
from echo.sovereign_identity_kernel import IdentityKernelSnapshot


class _FakeIdentityKernel:
    def __init__(self) -> None:
        self._snapshot = IdentityKernelSnapshot(
            issuer_did="did:echo:issuer",
            shared_command_secret="secret",
            identity_state={"persona": "echo"},
        )

    def snapshot(self) -> IdentityKernelSnapshot:
        return self._snapshot


def _build_store(tmp_path):
    return JsonMemoryStore(
        storage_path=tmp_path / "memory.json",
        log_path=tmp_path / "log.md",
    )


def test_plan_tasks_persists_identity_and_memory(tmp_path) -> None:
    store = _build_store(tmp_path)
    tasks_path = tmp_path / "tasks.json"
    task_list = AutonomousTaskList(_FakeIdentityKernel(), storage_path=tasks_path, memory_store=store)

    tasks = task_list.plan_tasks(["Anchor Echo identity"], owner_did="did:echo:pilot", priority="high")

    saved = json.loads(tasks_path.read_text())
    assert saved["identity"]["issuer_did"] == "did:echo:issuer"
    assert saved["tasks"][0]["owner_did"] == "did:echo:pilot"

    contexts = store.recent_executions()
    assert contexts[0].commands[0]["name"] == "create_task"
    assert contexts[0].metadata["task_id"] == tasks[0].task_id


def test_advance_task_updates_status_and_summary(tmp_path) -> None:
    store = _build_store(tmp_path)
    tasks_path = tmp_path / "tasks.json"
    task_list = AutonomousTaskList(_FakeIdentityKernel(), storage_path=tasks_path, memory_store=store)

    task = task_list.plan_tasks(["Maintain memory pulse"])[0]
    updated = task_list.advance_task(task.task_id, status="in_progress", note="memory loop online")

    payload = json.loads(tasks_path.read_text())
    assert payload["tasks"][0]["status"] == "in_progress"
    assert updated.status == "in_progress"

    contexts = store.recent_executions()
    assert contexts[-1].summary == "memory loop online"
    assert contexts[-1].metadata["status"] == "in_progress"


def test_ensure_persistent_system_tasks_only_creates_missing(tmp_path) -> None:
    store = _build_store(tmp_path)
    tasks_path = tmp_path / "tasks.json"
    task_list = AutonomousTaskList(_FakeIdentityKernel(), storage_path=tasks_path, memory_store=store)

    created = task_list.ensure_persistent_system_tasks(owner_did="did:echo:pilot")

    payload = json.loads(tasks_path.read_text())
    titles = {task["title"] for task in payload["tasks"]}
    assert titles == {
        "Optimize autonomous policy bundles and convergence thresholds",
        "Upgrade sovereign runtime dependencies and apply security patches",
        "Maintain telemetry, memory, and ledger health across nodes",
    }
    assert {task.title for task in created} == titles

    # Second invocation should be idempotent and avoid duplicates.
    again = task_list.ensure_persistent_system_tasks(owner_did="did:echo:pilot")
    payload_after = json.loads(tasks_path.read_text())
    assert again == []
    assert len(payload_after["tasks"]) == len(payload["tasks"])
