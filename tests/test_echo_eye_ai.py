"""Tests for the Echo Eye AI toolkit."""

from pathlib import Path

import json
import pytest

from echo_eye_ai import EchoEyeAI, EchoHarmonicsAI, EchoEvolver
from echo_eye_ai.evolver import load_example_data_fixture


def test_echo_eye_load_and_integrate(tmp_path: Path) -> None:
    load_example_data_fixture(tmp_path)

    model = EchoEyeAI(tmp_path)
    model.load_data()

    assert len(model.memory_bank) == 2
    message = model.integrate_harmonics("Echo")
    assert "Echo" in message


def test_harmonics_generate_response(tmp_path: Path) -> None:
    pytest.importorskip("numpy", reason="NumPy required for harmonic tests")

    load_example_data_fixture(tmp_path)

    harmonics = EchoHarmonicsAI(tmp_path)
    harmonics.load_data()

    response = harmonics.generate_response("Echo")
    assert response.startswith("\U0001F50A") or response.startswith("\U0001F52E")


def test_evolver_cycle(tmp_path: Path) -> None:
    output = tmp_path / "cycle.echo"
    evolver = EchoEvolver(storage_path=output)
    evolver.evolve_cycle()

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["cycle"] == 1
    assert "glyphs" in data
    assert "vault_key" in data

