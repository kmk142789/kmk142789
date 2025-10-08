import json
import random
from pathlib import Path
from tempfile import TemporaryDirectory

from echo_cascade import EchoCascadeResult, export_cascade, generate_cascade
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


def test_generate_cascade_builds_all_components() -> None:
    tmp = TemporaryDirectory()
    try:
        result = generate_cascade(
            evolver=_fresh_evolver(tmp),
            agent=_fresh_agent(tmp),
            private_keys=[TEST_KEY],
            manifest_chars=80,
            glyph_cycle="∇⊸≋",
            timestamp=1_700_000_000,
            enable_network=False,
            persist_artifact=False,
            ascii_width=21,
            ascii_height=11,
        )

        assert isinstance(result, EchoCascadeResult)
        assert result.state.cycle == 1
        assert result.manifest.key_count == 1
        assert result.constellation.cycle == result.state.cycle
        assert "Constellation :: Anchor=" in result.ascii_map
        assert "cycle-1-core" in result.ascii_map
        assert json.loads(result.manifest_json)["key_count"] == 1
        assert json.loads(result.constellation_json)["cycle"] == result.state.cycle
        assert result.artifact_path is None
    finally:
        tmp.cleanup()


def test_export_cascade_writes_text_payloads(tmp_path: Path) -> None:
    tmp = TemporaryDirectory()
    try:
        cascade = generate_cascade(
            evolver=_fresh_evolver(tmp),
            agent=_fresh_agent(tmp),
            private_keys=[TEST_KEY],
            manifest_chars=60,
            glyph_cycle="∇⊸",
            timestamp=1_700_000_000,
            enable_network=False,
            persist_artifact=False,
            ascii_width=21,
            ascii_height=11,
        )
    finally:
        tmp.cleanup()

    paths = export_cascade(cascade, tmp_path)

    manifest_path = paths["manifest"]
    constellation_path = paths["constellation"]
    ascii_path = paths["ascii"]

    assert manifest_path.exists()
    assert constellation_path.exists()
    assert ascii_path.exists()

    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    constellation_payload = json.loads(constellation_path.read_text(encoding="utf-8"))
    ascii_payload = ascii_path.read_text(encoding="utf-8")

    assert manifest_payload["key_count"] == 1
    assert constellation_payload["cycle"] == cascade.state.cycle
    assert "Constellation :: Anchor=" in ascii_payload
