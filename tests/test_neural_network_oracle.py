"""Tests for the neural network oracle."""

from __future__ import annotations

from echo.neural_network_oracle import (
    NeuralNetworkOracle,
    OracleTrainingSample,
    forge_neural_oracle,
)


def _build_samples() -> list[OracleTrainingSample]:
    samples = []
    for x in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for y in (-1.0, 0.0, 1.0):
            target = 0.5 * x - 0.25 * y
            samples.append(OracleTrainingSample(features=[x, y], targets=[target]))
    return samples


def test_oracle_training_reduces_loss() -> None:
    samples = _build_samples()
    oracle = NeuralNetworkOracle(input_size=2, hidden_layers=(6, 4), output_size=1, seed=7)

    initial_loss = oracle.evaluate_loss(samples)
    report = oracle.train(samples, epochs=150, shuffle=True)

    assert report.final_loss < initial_loss


def test_oracle_prediction_is_structured() -> None:
    samples = _build_samples()
    oracle, _report = forge_neural_oracle(input_size=2, samples=samples, seed=3, epochs=120)

    prediction = oracle.predict([0.2, -0.4])

    assert 0.0 < prediction.confidence < 1.0
    assert len(prediction.vector) == 1
    assert "hidden layers" in prediction.narrative


def test_oracle_is_deterministic_with_seed() -> None:
    samples = _build_samples()
    oracle_one, _ = forge_neural_oracle(input_size=2, samples=samples, seed=11, epochs=80)
    oracle_two, _ = forge_neural_oracle(input_size=2, samples=samples, seed=11, epochs=80)

    prediction_one = oracle_one.predict([0.1, 0.2])
    prediction_two = oracle_two.predict([0.1, 0.2])

    assert prediction_one.vector == prediction_two.vector
