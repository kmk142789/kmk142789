"""Utilities for deriving concrete quantam features from glyph lattices."""

from __future__ import annotations

import hashlib
import math
from typing import Dict, Iterable, List, Tuple

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
    state_vector = _serialize_state(mapper.state)

    signature_source = (
        f"{sigil}|{axis}|{angle:.6f}|{probability_zero:.6f}|{probability_one:.6f}|{fidelity:.6f}"
    )
    signature = hashlib.sha1(signature_source.encode("utf-8")).hexdigest()[:16]

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
    }
    return feature


__all__ = ["compute_quantam_feature"]

