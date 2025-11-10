from __future__ import annotations

from pathlib import Path

from echo.grand_crucible import GrandCrucibleBuilder
from echo.grand_crucible import blueprint as blueprint_module
from echo.grand_crucible.lattice import build_lattice
from echo.grand_crucible.storycraft import build_phase_heatmap, render_heatmap_ascii, storyline_from_lattice
from echo.grand_crucible.telemetry import capture_blueprint_metrics


def test_default_blueprint_structure():
    blueprint = blueprint_module.build_default_blueprint()

    assert blueprint.title.startswith("Grand Crucible")
    assert blueprint.epoch_names == ["Genesis Orbit", "Transcendent Spiral"]
    assert blueprint.total_duration() == blueprint.total_duration_precise()
    blueprint.validate()


def test_lattice_storyline_consistency():
    blueprint = blueprint_module.build_default_blueprint()
    lattice = build_lattice(blueprint)
    storyline = storyline_from_lattice(lattice)

    assert len(storyline) == sum(len(r.phases) for e in blueprint.epochs for r in e.rituals)
    assert any("Genesis Orbit" in beat for beat in storyline)


def test_heatmap_and_telemetry_alignment():
    blueprint = blueprint_module.build_default_blueprint()
    lattice = build_lattice(blueprint)
    heatmap = build_phase_heatmap(blueprint)
    telemetry = capture_blueprint_metrics(blueprint, lattice)

    total_heatmap_phases = sum(sum(counts) for counts in heatmap.values())
    assert total_heatmap_phases == telemetry.total_phases
    assert telemetry.energy_sum > 0
    assert render_heatmap_ascii(heatmap)


def test_builder_run_and_persistence(tmp_path: Path):
    outputs = tmp_path / "grand_crucible"
    builder = GrandCrucibleBuilder()
    builder.with_default_blueprint()

    artifacts_record = []

    def observer(artifacts):
        artifacts_record.append(artifacts)
        artifacts.persist(outputs)

    builder.add_observer(observer)
    crucible = builder.build()
    artifacts = crucible.run()

    assert artifacts_record
    assert (outputs / "overview.txt").exists()
    assert (outputs / "heatmap.txt").exists()
    assert (outputs / "storyline.txt").exists()
    assert (outputs / "telemetry.json").exists()
    assert "Lattice points" in (outputs / "overview.txt").read_text()
    assert artifacts.telemetry.total_phases > 0
