"""Instruction execution tracing for the sandbox."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass(slots=True)
class InstructionTrace:
    opcode: str
    operand: int | None
    before_stack: Sequence[int]
    after_stack: Sequence[int]


class ExecutionTracer:
    """Records executed instructions for post-run analysis."""

    def __init__(self) -> None:
        self._entries: List[InstructionTrace] = []

    def record(
        self,
        opcode: str,
        operand: int | None,
        *,
        before_stack: Sequence[int],
        after_stack: Sequence[int],
    ) -> None:
        self._entries.append(
            InstructionTrace(opcode, operand, tuple(before_stack), tuple(after_stack))
        )

    def export(self) -> Iterable[InstructionTrace]:
        return list(self._entries)

    def last(self) -> InstructionTrace | None:
        return self._entries[-1] if self._entries else None


__all__ = ["ExecutionTracer", "InstructionTrace"]
