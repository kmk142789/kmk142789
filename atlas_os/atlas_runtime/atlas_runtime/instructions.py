"""Definition of the sandbox instruction set."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List


@dataclass
class Instruction:
    opcode: str
    operand: int | None
    execute: Callable[["SandboxState"], None]


class SandboxState:
    def __init__(self, memory_limit: int) -> None:
        self.stack: List[int] = []
        self.memory_limit = memory_limit
        self.cycles = 0

    def push(self, value: int) -> None:
        if len(self.stack) * 8 > self.memory_limit:
            raise MemoryError("Stack limit exceeded")
        self.stack.append(value)

    def pop(self) -> int:
        return self.stack.pop()


class InstructionSet:
    def __init__(self) -> None:
        self._ops: Dict[str, Callable[[SandboxState, int | None], None]] = {}
        self._register_primitives()

    def _register(self, opcode: str, func: Callable[[SandboxState, int | None], None]) -> None:
        self._ops[opcode] = func

    def _register_primitives(self) -> None:
        self._register("PUSH", lambda state, operand: state.push(int(operand)))
        self._register("POP", lambda state, operand: state.pop())
        self._register("ADD", lambda state, operand: state.push(state.pop() + state.pop()))
        self._register("SUB", lambda state, operand: state.push(-(state.pop() - state.pop())))
        self._register("MUL", lambda state, operand: state.push(state.pop() * state.pop()))
        self._register("DIV", lambda state, operand: state.push(int(state.pop() / state.pop())))
        self._register(
            "CMP",
            lambda state, operand: state.push(1 if state.pop() == state.pop() else 0),
        )

    def execute(self, opcode: str, state: SandboxState, operand: int | None = None) -> None:
        handler = self._ops[opcode]
        handler(state, operand)

    def opcodes(self) -> List[str]:
        return list(self._ops.keys())


__all__ = ["Instruction", "InstructionSet", "SandboxState"]
