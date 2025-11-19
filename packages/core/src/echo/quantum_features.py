"""Utility helpers for deriving layered quantum feature sets."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import List, Sequence


@dataclass(frozen=True)
class QuantumFeature:
    """Represents a single derived measurement from a quantum state."""

    name: str
    complexity: int
    value: float


def _normalize_state(state: Sequence[complex]) -> List[complex]:
    if not state:
        raise ValueError("state must contain at least one amplitude")
    norm_sq = sum(abs(amplitude) ** 2 for amplitude in state)
    if norm_sq <= 0.0:
        raise ValueError("state must not be the zero vector")
    norm = math.sqrt(norm_sq)
    return [amplitude / norm for amplitude in state]


def _probabilities(state: Sequence[complex]) -> List[float]:
    return [float(abs(amplitude) ** 2) for amplitude in state]


def _variance(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def _adjacent_contrast(probabilities: Sequence[float]) -> float:
    if len(probabilities) < 2:
        return 0.0
    total = 0.0
    count = 0
    for index in range(len(probabilities)):
        neighbor = probabilities[(index + 1) % len(probabilities)]
        total += abs(probabilities[index] - neighbor)
        count += 1
    return total / count


def _phase_statistics(amplitudes: Sequence[complex], weights: Sequence[float]) -> tuple[float, float]:
    if not amplitudes:
        return (0.0, 0.0)
    cos_sum = 0.0
    sin_sum = 0.0
    for amplitude, weight in zip(amplitudes, weights):
        phase = math.atan2(amplitude.imag, amplitude.real)
        cos_sum += weight * math.cos(phase)
        sin_sum += weight * math.sin(phase)
    resultant = math.sqrt(cos_sum ** 2 + sin_sum ** 2)
    weight_total = max(sum(weights), 1e-12)
    coherence = resultant / weight_total
    variation = max(0.0, 1.0 - coherence)
    return (coherence, variation)


def _interference_energy(amplitudes: Sequence[complex]) -> float:
    energy = 0.0
    for index, left in enumerate(amplitudes):
        for right in amplitudes[index + 1 :]:
            energy += 2.0 * abs(left * right)
    return energy


def _uniform_overlap(amplitudes: Sequence[complex]) -> float:
    if not amplitudes:
        return 0.0
    dimension = len(amplitudes)
    uniform = [complex(1.0 / math.sqrt(dimension), 0.0) for _ in range(dimension)]
    overlap = sum(u.conjugate() * a for u, a in zip(uniform, amplitudes))
    return float(abs(overlap) ** 2)


def _complexity_index(probabilities: Sequence[float], variation: float) -> float:
    diversity = 1.0 - sum(probability ** 2 for probability in probabilities)
    return max(0.0, diversity * (0.5 + variation))


def _probability_moment(probabilities: Sequence[float], order: int) -> float:
    return sum(probability ** order for probability in probabilities)


def _probability_entropy(probabilities: Sequence[float]) -> float:
    entropy = 0.0
    for probability in probabilities:
        if probability > 0.0:
            entropy -= probability * math.log2(probability)
    return entropy


def _participation_ratio(probabilities: Sequence[float]) -> float:
    density = sum(probability ** 2 for probability in probabilities)
    if density <= 0.0:
        return 0.0
    return 1.0 / density


def generate_quantum_features(state: Sequence[complex], levels: int = 3) -> List[QuantumFeature]:
    """Return a layered set of quantum features up to ``levels`` depth."""

    if levels < 1:
        raise ValueError("levels must be at least 1")

    amplitudes = _normalize_state(state)
    probabilities = _probabilities(amplitudes)
    features: List[QuantumFeature] = []

    def _append(name: str, level: int, value: float) -> None:
        features.append(QuantumFeature(name=name, complexity=level, value=float(value)))

    # Level 1 – foundational probability measures
    _append("probability_mass", 1, sum(probabilities))
    _append("probability_variance", 1, _variance(probabilities))
    _append("amplitude_contrast", 1, max(probabilities) - min(probabilities))

    if levels >= 2:
        coherence, variation = _phase_statistics(amplitudes, probabilities)
        _append("phase_coherence", 2, coherence)
        _append("phase_variation", 2, variation)
        _append("adjacent_probability_contrast", 2, _adjacent_contrast(probabilities))
    else:
        coherence, variation = (0.0, 0.0)

    if levels >= 3:
        _append("interference_energy", 3, _interference_energy(amplitudes))
        _append("uniform_overlap", 3, _uniform_overlap(amplitudes))
        _append("complexity_index", 3, _complexity_index(probabilities, variation))
        _append("probability_entropy", 3, _probability_entropy(probabilities))
        _append("participation_ratio", 3, _participation_ratio(probabilities))

    for order in range(4, levels + 1):
        _append(f"probability_moment_{order}", order, _probability_moment(probabilities, order))

    return features


__all__ = ["QuantumFeature", "generate_quantum_features"]
