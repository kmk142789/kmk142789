"""Sandbox runner executing Wasm-like instruction programs."""

from __future__ import annotations

import signal
import time
from dataclasses import dataclass
from typing import Iterable, List, Tuple

from .instructions import InstructionSet, SandboxState


@dataclass
class SandboxResult:
    stack: List[int]
    cycles: int
    duration: float


class Sandbox:
    def __init__(self, *, instruction_set: InstructionSet | None = None) -> None:
        self._instruction_set = instruction_set or InstructionSet()

    def execute(
        self,
        program: Iterable[Tuple[str, int | None]],
        *,
        memory_limit: int = 1024,
        timeout: float = 0.2,
    ) -> SandboxResult:
        state = SandboxState(memory_limit)
        start = time.monotonic()
        for opcode, operand in program:
            elapsed = time.monotonic() - start
            if elapsed > timeout:
                raise TimeoutError("Sandbox timeout")
            if opcode not in self._instruction_set.opcodes():
                raise ValueError(f"Invalid opcode {opcode}")
            self._instruction_set.execute(opcode, state, operand)
            state.cycles += 1
        duration = time.monotonic() - start
        return SandboxResult(list(state.stack), state.cycles, duration)


__all__ = ["Sandbox", "SandboxResult"]
