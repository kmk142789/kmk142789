from dataclasses import dataclass, field
import math
import random
from typing import Dict, Iterable, List, Tuple

ComplexVector = Tuple[complex, complex]
ComplexMatrix = Tuple[ComplexVector, ComplexVector]


def _rotation_matrix(axis: str, angle: float) -> ComplexMatrix:
    """Return the single-qubit rotation matrix for ``axis`` and ``angle``."""

    axis = axis.upper()
    half_angle = angle / 2.0
    cos_half = math.cos(half_angle)
    sin_half = math.sin(half_angle)

    if axis == "X":
        return (
            (complex(cos_half, 0.0), complex(0.0, -sin_half)),
            (complex(0.0, -sin_half), complex(cos_half, 0.0)),
        )
    if axis == "Y":
        return (
            (complex(cos_half, 0.0), complex(-sin_half, 0.0)),
            (complex(sin_half, 0.0), complex(cos_half, 0.0)),
        )
    if axis == "Z":
        return (
            (complex(cos_half, -sin_half), 0 + 0j),
            (0 + 0j, complex(cos_half, sin_half)),
        )
    raise ValueError("axis must be one of 'X', 'Y', or 'Z'")


def _normalize(state: ComplexVector) -> ComplexVector:
    """Return ``state`` scaled so that ``|alpha|^2 + |beta|^2 == 1``."""

    alpha, beta = state
    norm = math.sqrt((alpha.conjugate() * alpha).real + (beta.conjugate() * beta).real)
    if norm == 0:
        raise ValueError("Quantum state cannot be the zero vector.")
    return (alpha / norm, beta / norm)


def _apply_matrix(state: ComplexVector, matrix: ComplexMatrix) -> ComplexVector:
    """Return the new state obtained by applying ``matrix`` to ``state``."""

    (a00, a01), (a10, a11) = matrix
    alpha, beta = state
    return (
        a00 * alpha + a01 * beta,
        a10 * alpha + a11 * beta,
    )


STANDARD_GATES: Dict[str, ComplexMatrix] = {
    "I": ((1 + 0j, 0 + 0j), (0 + 0j, 1 + 0j)),
    "X": ((0 + 0j, 1 + 0j), (1 + 0j, 0 + 0j)),
    "Y": ((0 + 0j, -1j), (1j, 0 + 0j)),
    "Z": ((1 + 0j, 0 + 0j), (0 + 0j, -1 + 0j)),
    "H": ((1 / math.sqrt(2), 1 / math.sqrt(2)), (1 / math.sqrt(2), -1 / math.sqrt(2))),
    "S": ((1 + 0j, 0 + 0j), (0 + 0j, 1j)),
    "T": ((1 + 0j, 0 + 0j), (0 + 0j, complex(math.cos(math.pi / 4), math.sin(math.pi / 4)))),
}

SIGIL_ROTATION_MAP: Dict[str, Tuple[str, float]] = {
    "⟁": ("Y", math.radians(120.0)),
    "ϟ": ("X", math.radians(72.0)),
    "♒": ("Z", math.radians(54.0)),
    "➶": ("X", math.radians(144.0)),
    "✶": ("Z", math.radians(180.0)),
    "⋆": ("Y", math.radians(210.0)),
    "𖤐": ("X", math.radians(96.0)),
    "⚯": ("Z", math.radians(36.0)),
    "⚡": ("Y", math.radians(60.0)),
    "∞": ("Z", math.radians(108.0)),
}


def _state_from_bloch(bloch_vector: Tuple[float, float, float]) -> ComplexVector:
    """Return a normalised state for the provided Bloch coordinates."""

    if len(bloch_vector) != 3:
        raise ValueError("bloch_vector must contain three values")
    x, y, z = bloch_vector
    norm = math.sqrt(x * x + y * y + z * z)
    if norm == 0:
        raise ValueError("bloch_vector magnitude must be non-zero")
    if not math.isclose(norm, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        x, y, z = (x / norm, y / norm, z / norm)

    clamped_z = max(-1.0, min(1.0, z))
    theta = math.acos(clamped_z)
    phi = math.atan2(y, x)
    alpha = complex(math.cos(theta / 2.0), 0.0)
    beta = complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0)
    return _normalize((alpha, beta))


@dataclass
class QuantumFluxMapper:
    """Single-qubit simulator for exploring quantum-inspired narratives.

    The mapper keeps track of a qubit state and a descriptive history so the
    calling code can weave creative stories around the transformations.
    ``apply_gate`` works with the standard gate catalog while
    :meth:`apply_custom_gate` allows arbitrary 2x2 unitary matrices.
    """

    state: ComplexVector = (1 + 0j, 0 + 0j)
    history: List[str] = field(default_factory=list)

    def apply_gate(self, name: str) -> ComplexVector:
        """Apply a named gate from :data:`STANDARD_GATES`."""

        if name not in STANDARD_GATES:
            raise KeyError(f"Unknown gate {name!r}.")
        matrix = STANDARD_GATES[name]
        self.state = _normalize(_apply_matrix(self.state, matrix))
        self.history.append(f"Applied {name} gate")
        return self.state

    def apply_custom_gate(self, name: str, matrix: ComplexMatrix) -> ComplexVector:
        """Apply ``matrix`` and record ``name`` in the history."""

        self.state = _normalize(_apply_matrix(self.state, matrix))
        self.history.append(f"Applied custom gate {name}")
        return self.state

    def apply_sequence(self, gates: Iterable[str]) -> ComplexVector:
        """Sequentially apply a collection of named gates."""

        for gate in gates:
            self.apply_gate(gate)
        return self.state

    def apply_rotation(self, axis: str, angle: float) -> ComplexVector:
        """Apply a continuous rotation around the chosen Bloch axis."""

        axis = axis.upper()
        if axis not in {"X", "Y", "Z"}:
            raise ValueError("axis must be one of 'X', 'Y', or 'Z'")
        if not math.isfinite(angle):
            raise ValueError("angle must be finite")

        matrix = _rotation_matrix(axis, angle)
        self.state = _normalize(_apply_matrix(self.state, matrix))
        self.history.append(f"Applied R{axis} rotation ({angle} rad)")
        return self.state

    def weave_sigil(
        self,
        sigil: str,
        bloch_vector: Tuple[float, float, float],
        *,
        qubit_index: int | None = None,
    ) -> ComplexVector:
        """Project ``sigil`` rotations onto ``bloch_vector`` and update history."""

        if not sigil:
            raise ValueError("sigil must not be empty")
        self.state = _state_from_bloch(bloch_vector)
        for glyph in sigil:
            axis, angle = SIGIL_ROTATION_MAP.get(glyph, ("Z", math.radians(45.0)))
            matrix = _rotation_matrix(axis, angle)
            self.state = _normalize(_apply_matrix(self.state, matrix))
            descriptor = f"R{axis} {angle:.3f} rad"
            if qubit_index is not None:
                descriptor += f" on q{qubit_index}"
            self.history.append(f"Wove sigil {glyph} via {descriptor}")
        self.history.append(f"Completed sigil weave for {sigil!r}")
        return self.state

    def bloch_coordinates(self) -> Tuple[float, float, float]:
        """Return ``(x, y, z)`` on the Bloch sphere for the current state."""

        alpha, beta = self.state
        x = 2 * (alpha.conjugate() * beta).real
        y = 2 * (alpha.conjugate() * beta).imag
        z = (alpha.conjugate() * alpha).real - (beta.conjugate() * beta).real
        return (x, y, z)

    def measure(self) -> str:
        """Measure the qubit in the computational basis and collapse the state."""

        alpha, beta = self.state
        p_zero = (alpha.conjugate() * alpha).real
        outcome = "0" if random.random() < p_zero else "1"
        self.state = (1 + 0j, 0 + 0j) if outcome == "0" else (0 + 0j, 1 + 0j)
        self.history.append(f"Measured |{outcome}⟩")
        return outcome

    def expected_value(self, operator: str) -> float:
        """Return the expectation value of the X, Y, or Z Pauli operator."""

        operator = operator.upper()
        if operator not in {"X", "Y", "Z"}:
            raise ValueError("Expectation only implemented for X, Y, or Z.")
        alpha, beta = self.state
        if operator == "X":
            value = (alpha.conjugate() * beta + beta.conjugate() * alpha).real
        elif operator == "Y":
            value = (-1j * alpha.conjugate() * beta + 1j * beta.conjugate() * alpha).real
        else:  # "Z"
            value = (alpha.conjugate() * alpha - beta.conjugate() * beta).real
        return float(value)

    def interference_landscape(self, samples: int = 36) -> List[Tuple[float, float]]:
        """Sweep phase rotations to map an interference pattern."""

        if samples <= 0:
            raise ValueError("samples must be positive")

        alpha, beta = self.state
        results: List[Tuple[float, float]] = []
        for index in range(samples):
            angle = 2 * math.pi * index / samples
            rotation = (
                (1 + 0j, 0 + 0j),
                (0 + 0j, complex(math.cos(angle), math.sin(angle))),
            )
            rotated = _normalize(_apply_matrix((alpha, beta), rotation))
            probability_one = (rotated[1].conjugate() * rotated[1]).real
            results.append((angle, probability_one))
        self.history.append(f"Mapped interference landscape with {samples} samples")
        return results


__all__ = [
    "QuantumFluxMapper",
    "STANDARD_GATES",
    "SIGIL_ROTATION_MAP",
]
