import json
from pathlib import Path

from scripts.cycle_orchestrator import orchestrate_cycle


def test_cycle_orchestrator_generates_outputs(tmp_path: Path) -> None:
    result = orchestrate_cycle(
        3,
        output_root=tmp_path,
        puzzle_limit=2,
        federate=False,
    )

    assert result.cycle == 3
    assert len(result.entries) == 2
    assert result.graph_path.exists()
    assert result.dedupe_path.exists()
    assert result.search_index.exists()
    assert result.markdown_path.exists()
    assert result.json_path.exists()
    assert result.voyage_json.exists()
    assert result.logs["voyage"].exists()
    payload = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert "structured_filters" in payload
    assert payload["structured_filters"]
