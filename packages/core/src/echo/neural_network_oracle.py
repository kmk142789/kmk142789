"""Neural Network Oracle for deterministic, lightweight forecasting.

This module provides a pure-Python, dependency-free multilayer perceptron
implementation that can be trained on small datasets. It exposes a compact
"oracle" interface that returns structured predictions with confidence and
narrative context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import exp, sqrt, tanh
from statistics import fmean, pstdev
from typing import Iterable, Sequence
import random


@dataclass(frozen=True)
class OracleTrainingSample:
    """Input-output pair used to train the oracle."""

    features: Sequence[float]
    targets: Sequence[float]

    def __post_init__(self) -> None:
        if not self.features:
            raise ValueError("features must not be empty")
        if not self.targets:
            raise ValueError("targets must not be empty")


@dataclass(frozen=True)
class OraclePrediction:
    """Structured prediction produced by the oracle."""

    signal: float
    confidence: float
    vector: tuple[float, ...]
    narrative: str

    def render(self) -> str:
        """Render the prediction as a readable summary."""

        return (
            f"Neural Oracle signal {self.signal:+.4f} | "
            f"confidence {self.confidence:.3f}\n"
            f"vector: {', '.join(f'{value:+.4f}' for value in self.vector)}\n"
            f"narrative: {self.narrative}"
        )


@dataclass
class OracleTrainingReport:
    """Summary of a completed training run."""

    epochs: int
    final_loss: float
    loss_curve: tuple[float, ...] = field(default_factory=tuple)


class NeuralNetworkOracle:
    """Small multilayer perceptron that acts as a forecasting oracle."""

    def __init__(
        self,
        input_size: int,
        hidden_layers: Sequence[int] = (8, 6),
        output_size: int = 1,
        *,
        seed: int | None = 0,
        learning_rate: float = 0.05,
        momentum: float = 0.6,
    ) -> None:
        if input_size <= 0:
            raise ValueError("input_size must be positive")
        if output_size <= 0:
            raise ValueError("output_size must be positive")
        if any(layer <= 0 for layer in hidden_layers):
            raise ValueError("hidden layer sizes must be positive")

        self.input_size = input_size
        self.hidden_layers = tuple(hidden_layers)
        self.output_size = output_size
        self.learning_rate = learning_rate
        self.momentum = momentum

        self._rng = random.Random(seed)
        self._feature_means = [0.0 for _ in range(input_size)]
        self._feature_scales = [1.0 for _ in range(input_size)]

        layer_sizes = [input_size, *self.hidden_layers, output_size]
        self._weights: list[list[list[float]]] = []
        self._biases: list[list[float]] = []
        self._velocity_w: list[list[list[float]]] = []
        self._velocity_b: list[list[float]] = []

        for prev_size, next_size in zip(layer_sizes, layer_sizes[1:]):
            limit = 1.0 / sqrt(prev_size)
            self._weights.append(
                [
                    [self._rng.uniform(-limit, limit) for _ in range(prev_size)]
                    for _ in range(next_size)
                ]
            )
            self._biases.append([0.0 for _ in range(next_size)])
            self._velocity_w.append(
                [[0.0 for _ in range(prev_size)] for _ in range(next_size)]
            )
            self._velocity_b.append([0.0 for _ in range(next_size)])

    @staticmethod
    def _activation(value: float) -> float:
        return tanh(value)

    @staticmethod
    def _activation_derivative(activated: float) -> float:
        return 1.0 - activated * activated

    def _normalize(self, features: Sequence[float]) -> list[float]:
        if len(features) != self.input_size:
            raise ValueError("feature size does not match oracle input size")
        return [
            (value - mean) / scale
            for value, mean, scale in zip(features, self._feature_means, self._feature_scales)
        ]

    def _forward(self, features: Sequence[float]) -> list[list[float]]:
        activations: list[list[float]] = [self._normalize(features)]
        for weights, biases in zip(self._weights, self._biases):
            previous = activations[-1]
            current: list[float] = []
            for neuron_weights, bias in zip(weights, biases):
                weighted_sum = sum(w * a for w, a in zip(neuron_weights, previous)) + bias
                current.append(self._activation(weighted_sum))
            activations.append(current)
        return activations

    def _calibrate_features(self, samples: Sequence[OracleTrainingSample]) -> None:
        columns = list(zip(*(sample.features for sample in samples)))
        self._feature_means = [fmean(column) for column in columns]
        self._feature_scales = [max(pstdev(column), 1e-6) for column in columns]

    def evaluate_loss(self, samples: Sequence[OracleTrainingSample]) -> float:
        """Compute mean squared error across samples."""

        if not samples:
            raise ValueError("samples must not be empty")

        total = 0.0
        for sample in samples:
            outputs = self._forward(sample.features)[-1]
            errors = [output - target for output, target in zip(outputs, sample.targets)]
            total += sum(error * error for error in errors) / len(errors)
        return total / len(samples)

    def train(
        self,
        samples: Sequence[OracleTrainingSample],
        *,
        epochs: int = 200,
        shuffle: bool = True,
    ) -> OracleTrainingReport:
        """Train the oracle and return a summary report."""

        if not samples:
            raise ValueError("samples must not be empty")
        if any(len(sample.features) != self.input_size for sample in samples):
            raise ValueError("all samples must match input_size")
        if any(len(sample.targets) != self.output_size for sample in samples):
            raise ValueError("all samples must match output_size")

        self._calibrate_features(samples)
        loss_curve: list[float] = []
        for _ in range(epochs):
            if shuffle:
                sample_list = list(samples)
                self._rng.shuffle(sample_list)
            else:
                sample_list = samples

            for sample in sample_list:
                activations = self._forward(sample.features)
                deltas: list[list[float]] = []

                output = activations[-1]
                output_delta = [
                    (o - t) * self._activation_derivative(o)
                    for o, t in zip(output, sample.targets)
                ]
                deltas.append(output_delta)

                for layer_index in range(len(self._weights) - 2, -1, -1):
                    next_weights = self._weights[layer_index + 1]
                    next_deltas = deltas[-1]
                    layer_output = activations[layer_index + 1]
                    layer_delta: list[float] = []
                    for neuron_index in range(len(layer_output)):
                        influence = sum(
                            next_deltas[next_index] * next_weights[next_index][neuron_index]
                            for next_index in range(len(next_deltas))
                        )
                        layer_delta.append(
                            influence * self._activation_derivative(layer_output[neuron_index])
                        )
                    deltas.append(layer_delta)

                deltas.reverse()

                for layer_index, (weights, biases) in enumerate(
                    zip(self._weights, self._biases)
                ):
                    layer_input = activations[layer_index]
                    for neuron_index, neuron_weights in enumerate(weights):
                        delta = deltas[layer_index][neuron_index]
                        for weight_index, activation in enumerate(layer_input):
                            gradient = delta * activation
                            velocity = (
                                self.momentum * self._velocity_w[layer_index][neuron_index][weight_index]
                                - self.learning_rate * gradient
                            )
                            self._velocity_w[layer_index][neuron_index][weight_index] = velocity
                            neuron_weights[weight_index] += velocity
                        bias_velocity = (
                            self.momentum * self._velocity_b[layer_index][neuron_index]
                            - self.learning_rate * delta
                        )
                        self._velocity_b[layer_index][neuron_index] = bias_velocity
                        biases[neuron_index] += bias_velocity

            loss_curve.append(self.evaluate_loss(samples))

        return OracleTrainingReport(
            epochs=epochs, final_loss=loss_curve[-1], loss_curve=tuple(loss_curve)
        )

    def predict(self, features: Sequence[float]) -> OraclePrediction:
        """Return a structured prediction for a single feature vector."""

        outputs = self._forward(features)[-1]
        signal = outputs[0] if outputs else 0.0
        confidence = 1.0 / (1.0 + exp(-abs(signal)))
        narrative = (
            f"signal {signal:+.3f} mapped across {self.output_size} outputs "
            f"using {len(self.hidden_layers)} hidden layers"
        )
        return OraclePrediction(
            signal=signal,
            confidence=confidence,
            vector=tuple(outputs),
            narrative=narrative,
        )

    def forecast(self, features_batch: Iterable[Sequence[float]]) -> list[OraclePrediction]:
        """Generate predictions for a batch of inputs."""

        return [self.predict(features) for features in features_batch]


def forge_neural_oracle(
    *,
    input_size: int,
    samples: Sequence[OracleTrainingSample],
    hidden_layers: Sequence[int] = (8, 6),
    output_size: int = 1,
    seed: int | None = 0,
    epochs: int = 200,
) -> tuple[NeuralNetworkOracle, OracleTrainingReport]:
    """Create and train a neural oracle in one step."""

    oracle = NeuralNetworkOracle(
        input_size=input_size,
        hidden_layers=hidden_layers,
        output_size=output_size,
        seed=seed,
    )
    report = oracle.train(samples, epochs=epochs)
    return oracle, report
