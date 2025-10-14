from datetime import datetime

from echo_meta_agent import memory


def test_log_last_and_find(tmp_path, monkeypatch) -> None:
    temp_path = tmp_path / "memory.json"
    monkeypatch.setattr(memory, "_MEMORY_PATH", temp_path)

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "plugin": "template",
        "tool": "hello",
        "args": ["Echo"],
        "kwargs": {"name": "Echo"},
        "success": True,
        "result_summary": "Hello, Echo!",
    }
    memory.log(event)

    recent = memory.last()
    assert len(recent) == 1
    assert recent[0]["plugin"] == "template"

    matches = memory.find("Echo")
    assert len(matches) == 1
    assert matches[0]["tool"] == "hello"
