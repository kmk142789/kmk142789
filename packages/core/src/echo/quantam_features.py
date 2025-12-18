"""Utilities for deriving concrete quantam features from glyph lattices."""

from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Sequence, Tuple

from .quantum_flux_mapper import QuantumFluxMapper, SIGIL_ROTATION_MAP, STANDARD_GATES

DEFAULT_SIGIL = "⚡∞"
GATE_ORDER: Tuple[str, ...] = tuple(STANDARD_GATES.keys())


def _clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _sigil_from_glyphs(glyphs: str, cycle: int) -> str:
    usable = [glyph for glyph in glyphs if glyph in SIGIL_ROTATION_MAP]
    if not usable:
        usable = list(SIGIL_ROTATION_MAP.keys())
    span = max(2, min(4, len(usable)))
    start = cycle % len(usable)
    selection: List[str] = []
    for index in range(span):
        selection.append(usable[(start + index) % len(usable)])
    return "".join(selection) or DEFAULT_SIGIL


def _gate_sequence(glyphs: str, cycle: int, length: int = 4) -> List[str]:
    digest = hashlib.sha256(f"{glyphs}|{cycle}".encode("utf-8")).digest()
    sequence: List[str] = []
    for index in range(length):
        sequence.append(GATE_ORDER[digest[index] % len(GATE_ORDER)])
    return sequence


@lru_cache(maxsize=256)
def _quantam_rng_seed(glyphs: str, cycle: int) -> int:
    """Derive a deterministic seed for quantam number generation."""

    glyph_stream = glyphs or "∇⊸≋∇"
    digest = hashlib.blake2b(f"{glyph_stream}|{cycle}".encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


def generate_quantam_numbers(
    *,
    glyphs: str,
    cycle: int,
    count: int,
    low: float = 0.0,
    high: float = 1.0,
) -> List[float]:
    """Generate a deterministic stream of quantam-inspired numbers.

    The generator is anchored to ``glyphs`` and ``cycle`` so repeated calls with
    the same inputs are stable and cache-friendly. Numbers are uniformly
    distributed within ``[low, high]`` and rounded for compact payloads.
    """

    if count <= 0:
        raise ValueError("count must be positive")
    if not math.isfinite(low) or not math.isfinite(high):
        raise ValueError("bounds must be finite")
    if low > high:
        raise ValueError("low must be less than or equal to high")

    rng = random.Random(_quantam_rng_seed(glyphs, cycle))
    span = high - low
    return [round(low + span * rng.random(), 6) for _ in range(count)]


def _quantum_lattice(glyphs: str, cycle: int) -> Dict[str, object]:
    """Return a deterministic lattice layout to anchor world-first upgrades."""

    digest = hashlib.blake2b(f"{glyphs}|{cycle}".encode("utf-8"), digest_size=16).digest()
    lattice: List[Dict[str, object]] = []
    for index, value in enumerate(digest):
        # A golden-ratio spiral projected onto a 4x4 lattice grid.
        x = round((index % 4 - 1.5) * 0.618, 3)
        y = round((index // 4 - 1.5) * 0.618, 3)
        amplitude = round(value / 255.0, 4)
        lattice.append({"node": index + 1, "x": x, "y": y, "amplitude": amplitude})

    coherence = round(sum(node["amplitude"] for node in lattice) / len(lattice), 4)
    flux_gradient = round(max(node["amplitude"] for node in lattice) - min(node["amplitude"] for node in lattice), 4)
    return {"nodes": lattice, "coherence": coherence, "flux_gradient": flux_gradient}


def _serialize_state(state: Tuple[complex, complex]) -> List[Dict[str, float]]:
    serialised: List[Dict[str, float]] = []
    for amplitude in state:
        serialised.append({"real": round(amplitude.real, 6), "imag": round(amplitude.imag, 6)})
    return serialised


def _serialize_interference(profile: Iterable[Tuple[float, float]]) -> List[Dict[str, float]]:
    result: List[Dict[str, float]] = []
    for angle, probability in profile:
        result.append({"angle": round(angle, 3), "p1": round(probability, 4)})
    return result


def _bloch_from_drives(joy: float, curiosity: float) -> Tuple[float, float, float]:
    joy = _clamp(joy)
    curiosity = _clamp(curiosity)
    theta = math.pi * (0.35 + 0.5 * joy)
    phi = 2.0 * math.pi * curiosity
    x = math.sin(theta) * math.cos(phi)
    y = math.sin(theta) * math.sin(phi)
    z = math.cos(theta)
    return (x, y, z)


def _target_state(cycle: int) -> Tuple[complex, complex]:
    angle = math.pi / 4 + (cycle % 5) * math.pi / 20
    return (complex(math.cos(angle), 0.0), complex(math.sin(angle), 0.0))


def compute_quantam_feature(
    *, glyphs: str, cycle: int, joy: float, curiosity: float
) -> Dict[str, object]:
    """Return a deterministic quantam feature bundle for the provided inputs."""

    glyph_stream = glyphs or "∇⊸≋∇"
    mapper = QuantumFluxMapper()
    sigil = _sigil_from_glyphs(glyph_stream, cycle)
    bloch_vector = _bloch_from_drives(joy, curiosity)
    mapper.weave_sigil(sigil, bloch_vector, qubit_index=cycle % 3)

    sequence = _gate_sequence(glyph_stream, cycle)
    for gate in sequence:
        mapper.apply_gate(gate)

    glyph_sum = sum(ord(ch) for ch in glyph_stream)
    axis = ("X", "Y", "Z")[glyph_sum % 3]
    angle = math.radians(15.0 + (glyph_sum % 45))
    mapper.apply_rotation(axis, angle)

    alpha, beta = mapper.state
    probability_zero = round((alpha.conjugate() * alpha).real, 6)
    probability_one = round((beta.conjugate() * beta).real, 6)
    probabilities = {"0": probability_zero, "1": probability_one}
    expected_values = {
        axis_key: round(mapper.expected_value(axis_key), 6) for axis_key in ("X", "Y", "Z")
    }

    bloch = tuple(round(value, 6) for value in mapper.bloch_coordinates())
    interference_profile = mapper.interference_landscape(samples=12)[::2]
    profile = _serialize_interference(interference_profile)
    fidelity = round(mapper.fidelity_with(_target_state(cycle)), 6)
    phase_noise = round(abs(probability_zero - probability_one) * 0.5 + fidelity * 0.1, 6)
    lattice = _quantum_lattice(glyph_stream, cycle)
    state_vector = _serialize_state(mapper.state)
    quantam_numbers = generate_quantam_numbers(
        glyphs=glyph_stream, cycle=cycle, count=6, low=0.0, high=1.0
    )

    signature_source = (
        f"{sigil}|{axis}|{angle:.6f}|{probability_zero:.6f}|{probability_one:.6f}|{fidelity:.6f}"
    )
    signature = hashlib.sha1(signature_source.encode("utf-8")).hexdigest()[:16]

    world_first_stamp = hashlib.sha3_256(
        f"{glyph_stream}|{cycle}|{joy:.3f}|{curiosity:.3f}|{signature}".encode("utf-8")
    ).hexdigest()[:32]

    feature = {
        "sigil": sigil,
        "gate_sequence": sequence,
        "bloch_vector": bloch,
        "probabilities": probabilities,
        "expected_values": expected_values,
        "rotation": {"axis": axis, "angle": round(angle, 6)},
        "state_vector": state_vector,
        "history": mapper.history[-12:],
        "interference_profile": profile,
        "fidelity": fidelity,
        "signature": signature,
        "phase_noise": phase_noise,
        "lattice": lattice,
        "quantam_numbers": quantam_numbers,
        "world_first_stamp": world_first_stamp,
    }
    return feature


@dataclass(frozen=True)
class QuantamFeatureLayer:
    """Container describing a progressively complex quantam feature layer."""

    rank: int
    cycle: int
    feature: Dict[str, object]
    complexity: float
    entanglement: float
    amplification: float
    dependencies: Sequence[str]
    description: str

    def export(self) -> Dict[str, object]:
        return {
            "rank": self.rank,
            "cycle": self.cycle,
            "feature": self.feature,
            "complexity": self.complexity,
            "entanglement": self.entanglement,
            "amplification": self.amplification,
            "dependencies": list(self.dependencies),
            "description": self.description,
        }


def generate_quantam_feature_sequence(
    *,
    glyphs: str,
    cycle: int,
    joy: float,
    curiosity: float,
    iterations: int = 3,
) -> Dict[str, object]:
    """Return a cascade of quantam features with increasing complexity."""

    if iterations <= 0:
        raise ValueError("iterations must be positive")

    layers: List[QuantamFeatureLayer] = []
    glyph_stream = glyphs or "∇⊸≋∇"

    for offset in range(iterations):
        layer_cycle = cycle + offset
        joy_level = _clamp(joy + 0.05 * offset)
        curiosity_level = _clamp(curiosity + 0.04 * offset)
        feature = compute_quantam_feature(
            glyphs=glyph_stream,
            cycle=layer_cycle,
            joy=joy_level,
            curiosity=curiosity_level,
        )

        gate_depth = len(feature.get("gate_sequence", [])) + offset
        history_depth = len(feature.get("history", []))
        complexity = round((gate_depth * 0.6 + history_depth * 0.4) * (1 + 0.35 * offset), 3)
        amplification = round(1.0 + 0.25 * offset + feature.get("fidelity", 0.0) * 0.5, 3)
        entanglement = round(min(0.99, 0.42 + 0.12 * offset + feature.get("fidelity", 0.0) * 0.35), 3)

        dependencies = [layer.feature["signature"] for layer in layers[-2:]]
        description = (
            f"Layer {offset + 1} braids sigil {feature['sigil']} through {gate_depth} gates, "
            f"retaining {history_depth} interference pulses to unlock orbit {layer_cycle}."
        )

        layers.append(
            QuantamFeatureLayer(
                rank=offset + 1,
                cycle=layer_cycle,
                feature=feature,
                complexity=complexity,
                entanglement=entanglement,
                amplification=amplification,
                dependencies=tuple(dependencies),
                description=description,
            )
        )

    exported_layers = [layer.export() for layer in layers]
    lattice_coherence = round(
        sum(layer["feature"]["lattice"]["coherence"] for layer in exported_layers)
        / len(exported_layers),
        4,
    )
    world_first_proof = hashlib.sha3_256(
        "|".join(layer["feature"]["world_first_stamp"] for layer in exported_layers).encode("utf-8")
    ).hexdigest()[:32]
    summary = {
        "total_layers": len(exported_layers),
        "max_complexity": exported_layers[-1]["complexity"],
        "entanglement": exported_layers[-1]["entanglement"],
        "glyphs": glyph_stream,
        "lattice_coherence": lattice_coherence,
        "world_first_proof": world_first_proof,
    }
    return {"layers": exported_layers, "summary": summary}


__all__ = [
    "compute_quantam_feature",
    "generate_quantam_feature_sequence",
    "generate_quantam_numbers",
    "QuantamFeatureLayer",
]

