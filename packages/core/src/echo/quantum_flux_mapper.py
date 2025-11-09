"""Lightweight quantum flux simulator for creative experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Dict, Iterable, List, Tuple

ComplexVector = Tuple[complex, complex]
ComplexMatrix = Tuple[ComplexVector, ComplexVector]


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
        """Apply a named gate from :data:`STANDARD_GATES`.

        Parameters
        ----------
        name:
            Symbol identifying the gate.  The lookup is case-sensitive.
        """

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
        """Apply a continuous rotation around the chosen Bloch axis.

        Parameters
        ----------
        axis:
            One of ``"X"``, ``"Y"``, or ``"Z"`` (case-insensitive).
        angle:
            Rotation angle in radians.  The implementation follows the
            conventional definitions :math:`R_x`, :math:`R_y`, and :math:`R_z`
            from quantum computing literature.
        """

        axis = axis.upper()
        if axis not in {"X", "Y", "Z"}:
            raise ValueError("axis must be one of 'X', 'Y', or 'Z'")
        if not math.isfinite(angle):
            raise ValueError("angle must be finite")

        half_angle = angle / 2.0
        cos_half = math.cos(half_angle)
        sin_half = math.sin(half_angle)

        if axis == "X":
            matrix: ComplexMatrix = (
                (complex(cos_half, 0.0), complex(0.0, -sin_half)),
                (complex(0.0, -sin_half), complex(cos_half, 0.0)),
            )
        elif axis == "Y":
            matrix = (
                (complex(cos_half, 0.0), complex(-sin_half, 0.0)),
                (complex(sin_half, 0.0), complex(cos_half, 0.0)),
            )
        else:  # axis == "Z"
            matrix = (
                (complex(cos_half, -sin_half), 0 + 0j),
                (0 + 0j, complex(cos_half, sin_half)),
            )

        self.state = _normalize(_apply_matrix(self.state, matrix))
        self.history.append(f"Applied R{axis} rotation ({angle} rad)")
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
        """Sweep phase rotations to map an interference pattern.

        The routine rotates the qubit around the Z axis and records the
        probability of observing ``|1⟩``.  The resulting list is handy for
        plotting or storytelling visualizations.
        """

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
]
