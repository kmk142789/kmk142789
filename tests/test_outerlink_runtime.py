import json

from outerlink.runtime import OuterLinkRuntime
from outerlink.utils import SafeModeConfig


def test_flush_events_handles_trimmed_history(tmp_path):
    config = SafeModeConfig(
        event_log=tmp_path / "events.log",
        offline_cache_dir=tmp_path / "cache",
        event_history_limit=3,
    )
    runtime = OuterLinkRuntime(config=config)
    runtime.offline_state.mark_online()

    for i in range(5):
        runtime.event_bus.emit("test", {"i": i})

    runtime.flush_events()

    runtime.event_bus.emit("test", {"i": 5})
    runtime.flush_events()

    lines = config.event_log.read_text().splitlines()
    assert len(lines) == 4
    payloads = [json.loads(line) for line in lines]
    assert payloads[-1]["payload"]["i"] == 5
