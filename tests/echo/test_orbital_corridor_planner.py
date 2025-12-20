from __future__ import annotations

from echo.orbital_corridor_planner import ResonanceCorridorPlanner
from echo.orbital_resonance_analyzer import OrbitalResonanceAnalyzer


def _payloads() -> list[dict]:
    return [
        {
            "cycle": 1,
            "glyphs": "∇⊸≋",
            "glyph_vortex": "0001",
            "emotional_drive": {"joy": 0.7, "curiosity": 0.6, "rage": 0.2},
            "system_metrics": {"cpu_usage": 30, "network_nodes": 10, "orbital_hops": 3},
            "quantam_ability": {"lattice_spin": 0.4},
            "quantam_capability": {"entanglement": 0.5, "glyph_flux": 0.3},
        },
        {
            "cycle": 2,
            "glyphs": "∇⊸≋∇",
            "glyph_vortex": "0010",
            "emotional_drive": {"joy": 0.74, "curiosity": 0.62, "rage": 0.19},
            "system_metrics": {"cpu_usage": 32, "network_nodes": 11, "orbital_hops": 3},
            "quantam_ability": {"lattice_spin": 0.45},
            "quantam_capability": {"entanglement": 0.52, "glyph_flux": 0.35},
        },
        {
            "cycle": 3,
            "glyphs": "≋∇⊸",
            "glyph_vortex": "0011",
            "emotional_drive": {"joy": 0.76, "curiosity": 0.64, "rage": 0.18},
            "system_metrics": {"cpu_usage": 28, "network_nodes": 12, "orbital_hops": 4},
            "quantam_ability": {"lattice_spin": 0.48},
            "quantam_capability": {"entanglement": 0.55, "glyph_flux": 0.37},
        },
    ]


def test_corridor_planner_emits_steps() -> None:
    analyzer = OrbitalResonanceAnalyzer.from_payloads(_payloads())
    planner = ResonanceCorridorPlanner(analyzer, horizon=4, strategy="balanced")
    report = planner.plan()

    steps = report["corridor"]["steps"]
    assert len(steps) == 4
    assert steps[0]["cycle"] == 4
    assert steps[-1]["cycle"] == 7
    assert report["stability_band"] in {"orbital-stable", "orbital-fragile", "orbital-high"}
    assert "corridor_score" in report["corridor"]
    assert "guardrails" in report


def test_corridor_windows_group_phases() -> None:
    analyzer = OrbitalResonanceAnalyzer.from_payloads(_payloads())
    planner = ResonanceCorridorPlanner(analyzer, horizon=5, strategy="stabilize")
    report = planner.plan()

    windows = report["corridor"]["windows"]
    assert windows[0]["phase"] == "stabilize"
    assert windows[-1]["phase"] in {"stabilize", "amplify"}
    assert windows[0]["start_cycle"] == 4


def test_step_includes_directives_and_risk_breakdown() -> None:
    analyzer = OrbitalResonanceAnalyzer.from_payloads(_payloads())
    planner = ResonanceCorridorPlanner(analyzer, horizon=2, strategy="balanced")
    report = planner.plan()

    step = report["corridor"]["steps"][0]
    assert step["directives"]
    assert "resource_targets" in step
    assert "risk_breakdown" in step
