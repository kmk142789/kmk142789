import json
import random
from pathlib import Path
from tempfile import TemporaryDirectory

from dominion.cascade import build_cascade_plan
from dominion.executor import PlanExecutor

from echo_evolver import EchoEvolver
from echo_universal_key_agent import UniversalKeyAgent


TEST_KEY = "4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d"


def _fresh_evolver(tmp: TemporaryDirectory) -> EchoEvolver:
    return EchoEvolver(
        artifact_path=Path(tmp.name) / "artifact.echo.json",
        rng=random.Random(1234),
        time_source=lambda: 987654321,
    )


def _fresh_agent(tmp: TemporaryDirectory) -> UniversalKeyAgent:
    return UniversalKeyAgent(vault_path=Path(tmp.name) / "vault.json")


def test_build_cascade_plan_produces_dominion_plan(tmp_path: Path) -> None:
    tmp = TemporaryDirectory()
    try:
        plan = build_cascade_plan(
            "build/cascade",
            private_keys=[TEST_KEY],
            manifest_chars=80,
            glyph_cycle="∇⊸≋",
            timestamp=1_700_000_000,
            ascii_width=21,
            ascii_height=11,
            enable_network=False,
            persist_artifact=False,
            evolver=_fresh_evolver(tmp),
            agent=_fresh_agent(tmp),
            source="tests.dominion.cascade",
        )
    finally:
        tmp.cleanup()

    assert plan.source == "tests.dominion.cascade"
    assert plan.metadata["intent_count"] == 3

    cascade_meta = plan.metadata["cascade"]
    assert cascade_meta["cycle"] == 1
    assert cascade_meta["output_dir"] == "build/cascade"
    assert cascade_meta["private_key_count"] == 1
    assert cascade_meta["ascii_dimensions"] == [21, 11]
    assert cascade_meta["manifest_chars"] == 80

    executor = PlanExecutor(root=tmp_path, workdir=tmp_path / "build" / "dominion")
    receipt = executor.apply(plan)
    assert receipt.summary["applied"] == 3

    manifest_path = tmp_path / "build/cascade/echo_manifest.json"
    constellation_path = tmp_path / "build/cascade/echo_constellation.json"
    ascii_path = tmp_path / "build/cascade/echo_constellation.txt"

    assert manifest_path.exists()
    assert constellation_path.exists()
    assert ascii_path.exists()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    constellation_payload = json.loads(constellation_path.read_text(encoding="utf-8"))
    ascii_payload = ascii_path.read_text(encoding="utf-8")

    assert manifest_payload["key_count"] == 1
    assert constellation_payload["cycle"] == cascade_meta["cycle"]
    assert "Constellation :: Anchor=" in ascii_payload

