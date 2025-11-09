from __future__ import annotations

from pathlib import Path

from pulse_weaver.service import PulseWeaverService


def test_monolith_report_builds_monument(tmp_path: Path) -> None:
    service = PulseWeaverService(tmp_path)
    service.record_success(
        key="alpha",
        message="Alpha spark",
        cycle="cycle-001",
        atlas_node="Atlas::North",
    )
    service.record_failure(
        key="beta",
        message="Beta fracture",
        cycle="cycle-002",
        phantom_trace="Ghost-9",
    )
    service.record_failure(
        key="gamma",
        message="Gamma turbulence",
        cycle="cycle-002",
        phantom_trace="Ghost-9",
    )

    report = service.monolith(limit=50)
    payload = report.to_dict()

    assert payload["schema"] == "pulse.weaver/monolith-v1"
    assert payload["magnitude"] == 3
    assert payload["statuses"]["failure"] == 2
    assert "cycle-001" in payload["cycles"]
    cycle_two = next(item for item in payload["timeline"] if item["cycle"] == "cycle-002")
    assert cycle_two["total"] == 2
    assert cycle_two["by_status"]["failure"] == 2
    assert any("Beta fracture" in text for text in cycle_two["highlights"])
    assert payload["atlas"]["Atlas::North"] == 1
    assert payload["phantom"]["Ghost-9"] == 2
    assert payload["proclamation"].startswith("Pulse Weaver Monolith")
    assert "Gamma turbulence" in " ".join(cycle_two["highlights"])
    assert "Atlas" in payload["proclamation"]
