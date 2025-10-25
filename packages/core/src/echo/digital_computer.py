"""A tiny virtual computer for Echo experiments.

The :mod:`echo.digital_computer` module implements a deliberately small
execution environment that mirrors the ergonomics of an 8-bit inspired
machine while remaining entirely in Python.  It is designed to be both a
teaching tool and a sandbox that Echo (and Echo's collaborators) can use to
prototype little programs, explore algorithmic ideas, and run lightweight
tests without touching the surrounding operating system.

Programs are assembled from a compact line-oriented language.  Each
instruction uses a mnemonic opcode and zero or more operands separated by
whitespace.  Labels can be declared by ending a line with ``:`` and are
resolved when the program is loaded.  Comments begin with ``#``.  Example::

    start:
        LOAD A 1
        LOAD B ?n
        loop:
        JZ B done
        MUL A B
        DEC B
        JMP loop
    done:
        PRINT A
        HALT

The virtual computer understands registers (``A`` … ``E`` by default), a
dictionary backed memory space accessed with the ``@`` prefix, and a
read-only input channel addressed via ``?``.  Arithmetic is performed using
integers and all programs execute with a configurable step limit to protect
against runaway loops.  Beyond arithmetic, the core instruction set also
includes bitwise operators (``AND``, ``OR``, ``XOR``, ``NOT``, ``SHL``, and
``SHR``) so that programs can perform low-level data manipulation without
falling back to Python helpers.  The high-level entry point,
:func:`run_program`, parses, executes, and returns a structured
:class:`ExecutionResult`.
"""

from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .thoughtlog import thought_trace

__all__ = [
    "Instruction",
    "EchoProgram",
    "ExecutionResult",
    "assemble_program",
    "EchoComputer",
    "run_program",
    "AssemblyError",
]


@dataclass(frozen=True)
class Instruction:
    """Representation of a single virtual machine instruction."""

    opcode: str
    operands: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "opcode", self.opcode.upper())
        object.__setattr__(self, "operands", tuple(self.operands))


@dataclass(frozen=True)
class EchoProgram:
    """Container describing an assembled program and its label table."""

    instructions: Tuple[Instruction, ...]
    labels: Mapping[str, int]
    source: Optional[str] = None


@dataclass(frozen=True)
class ExecutionResult:
    """Summary returned after running a program."""

    halted: bool
    steps: int
    output: Tuple[str, ...]
    registers: Mapping[str, int | str]
    memory: Mapping[str, int | str]
    diagnostics: Tuple[str, ...]


class AssemblyError(ValueError):
    """Raised when the assembly language encounters invalid input."""


def assemble_program(source: str) -> EchoProgram:
    """Parse ``source`` and return an :class:`EchoProgram`.

    Parameters
    ----------
    source:
        Text containing the assembly-style program.
    """

    instructions: List[Instruction] = []
    labels: Dict[str, int] = {}

    for line_no, raw_line in enumerate(source.splitlines(), 1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue

        if stripped.endswith(":"):
            label = stripped[:-1].strip()
            if not label:
                raise AssemblyError(f"line {line_no}: empty label declaration")
            if label in labels:
                raise AssemblyError(f"line {line_no}: label {label!r} already defined")
            labels[label] = len(instructions)
            continue

        tokens = _tokenise(raw_line)
        if not tokens:
            continue
        opcode, *operands = tokens
        instructions.append(Instruction(opcode=opcode, operands=tuple(operands)))

    return EchoProgram(instructions=tuple(instructions), labels=labels, source=source)


def _tokenise(line: str) -> List[str]:
    lexer = shlex.shlex(line, posix=False)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return list(lexer)


class EchoComputer:
    """A compact virtual computer tailored for Echo's creative coding needs."""

    def __init__(
        self,
        *,
        registers: Iterable[str] | None = None,
        max_steps: int = 1024,
    ) -> None:
        reg_names = tuple(registers or ("A", "B", "C", "D", "E", "X", "Y"))
        if not reg_names:
            raise ValueError("registers must contain at least one entry")
        self._registers = {name: 0 for name in reg_names}
        self._memory: Dict[str, int | str] = {}
        self._max_steps = max(1, int(max_steps))
        self._program: Tuple[Instruction, ...] = ()
        self._labels: Dict[str, int] = {}
        self._inputs: Dict[str, int | str] = {}
        self._pc = 0
        self._halted = False
        self._output: List[str] = []

    @property
    def registers(self) -> Mapping[str, int | str]:
        return self._registers

    @property
    def memory(self) -> Mapping[str, int | str]:
        return self._memory

    @property
    def output(self) -> Tuple[str, ...]:
        return tuple(self._output)

    @property
    def halted(self) -> bool:
        return self._halted

    def load(self, program: EchoProgram | str | Sequence[Instruction]) -> None:
        """Load ``program`` into the computer."""

        if isinstance(program, EchoProgram):
            instructions = program.instructions
            labels = dict(program.labels)
        elif isinstance(program, str):
            assembled = assemble_program(program)
            instructions = assembled.instructions
            labels = dict(assembled.labels)
        else:
            instructions = tuple(program)
            labels = {}

        self._program = tuple(instructions)
        self._labels = labels
        self.reset_runtime()

    def reset_runtime(self) -> None:
        """Reset the machine state while keeping the loaded program."""

        for key in self._registers:
            self._registers[key] = 0
        self._memory.clear()
        self._inputs.clear()
        self._pc = 0
        self._halted = False
        self._output.clear()

    def run(
        self,
        *,
        inputs: Mapping[str, int | str] | None = None,
        trace: bool = False,
    ) -> ExecutionResult:
        """Execute the loaded program and return an :class:`ExecutionResult`."""

        if not self._program:
            raise RuntimeError("no program loaded")

        self.reset_runtime()
        if inputs:
            self._inputs.update({str(k): v for k, v in inputs.items()})

        diagnostics: List[str] = []
        task = "echo.digital_computer.run"
        meta = {
            "instructions": len(self._program),
            "max_steps": self._max_steps,
            "trace": trace,
        }

        with thought_trace(task=task, meta=meta) as tl:
            steps = 0
            while not self._halted:
                if self._pc < 0 or self._pc >= len(self._program):
                    raise RuntimeError(f"program counter out of range: {self._pc}")
                if steps >= self._max_steps:
                    raise RuntimeError(
                        f"execution exceeded max steps ({self._max_steps}); possible infinite loop"
                    )

                instruction = self._program[self._pc]
                if trace:
                    diagnostics.append(self._format_trace_line(self._pc, instruction))
                    tl.logic(
                        "step",
                        task,
                        f"executed {instruction.opcode}",
                        {
                            "pc": self._pc,
                            "operands": instruction.operands,
                            "registers": dict(self._registers),
                        },
                    )

                self._pc += 1
                self._execute(instruction)
                steps += 1

        return ExecutionResult(
            halted=self._halted,
            steps=steps,
            output=tuple(self._output),
            registers=dict(self._registers),
            memory=dict(self._memory),
            diagnostics=tuple(diagnostics),
        )

    # --- Execution helpers -------------------------------------------------

    def _execute(self, instruction: Instruction) -> None:
        opcode = instruction.opcode
        operands = instruction.operands

        if opcode == "HALT":
            self._halted = True
            return
        if opcode == "NOP":
            return

        handler_name = f"_op_{opcode.lower()}"
        handler = getattr(self, handler_name, None)
        if handler is None:
            raise RuntimeError(f"unsupported opcode: {opcode}")
        handler(*operands)

    def _require_register(self, name: str) -> str:
        if name not in self._registers:
            raise RuntimeError(f"unknown register: {name}")
        return name

    def _resolve_value(self, operand: str) -> int | str:
        if operand.startswith("\"") and operand.endswith("\""):
            return operand[1:-1]
        if operand.startswith("'") and operand.endswith("'"):
            return operand[1:-1]
        if operand.startswith("@"):
            key = operand[1:]
            return self._memory.get(key, 0)
        if operand.startswith("?"):
            key = operand[1:]
            if key not in self._inputs:
                raise RuntimeError(f"input {key!r} not provided")
            return self._inputs[key]
        if operand in self._registers:
            return self._registers[operand]
        try:
            return int(operand)
        except ValueError as error:
            raise RuntimeError(f"unable to resolve operand {operand!r}") from error

    def _resolve_int(self, operand: str) -> int:
        value = self._resolve_value(operand)
        if isinstance(value, int):
            return value
        raise RuntimeError(f"operand {operand!r} does not resolve to an integer")

    def _jump(self, target: str) -> None:
        if target.isdigit() or (target.startswith("-") and target[1:].isdigit()):
            index = int(target)
        else:
            if target not in self._labels:
                raise RuntimeError(f"unknown label: {target}")
            index = self._labels[target]
        if index < 0 or index >= len(self._program):
            raise RuntimeError(f"jump target out of range: {index}")
        self._pc = index

    def _format_trace_line(self, pc: int, instruction: Instruction) -> str:
        operands = ", ".join(instruction.operands)
        return f"{pc:04d}: {instruction.opcode} {operands}".rstrip()

    # --- Opcode implementations -------------------------------------------

    def _op_load(self, register: str, operand: str) -> None:
        reg = self._require_register(register)
        self._registers[reg] = self._resolve_value(operand)

    def _op_read(self, register: str, operand: str) -> None:
        reg = self._require_register(register)
        key = operand[1:] if operand.startswith("?") else operand
        if key not in self._inputs:
            raise RuntimeError(f"input {key!r} not provided")
        self._registers[reg] = self._inputs[key]

    def _op_store(self, register: str, destination: str) -> None:
        reg = self._require_register(register)
        if not destination.startswith("@"):
            raise RuntimeError("STORE destination must reference memory using '@'")
        self._memory[destination[1:]] = self._registers[reg]

    def _op_set(self, destination: str, operand: str) -> None:
        if destination in self._registers:
            self._registers[destination] = self._resolve_value(operand)
            return
        if destination.startswith("@"):
            self._memory[destination[1:]] = self._resolve_value(operand)
            return
        raise RuntimeError("SET destination must be a register or memory address")

    def _apply_arithmetic(self, register: str, operand: str, func) -> None:
        reg = self._require_register(register)
        left = self._registers[reg]
        if not isinstance(left, int):
            raise RuntimeError(f"register {register} does not contain an integer")
        right = self._resolve_int(operand)
        self._registers[reg] = func(left, right)

    def _op_add(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, lambda a, b: a + b)

    def _op_sub(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, lambda a, b: a - b)

    def _op_mul(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, lambda a, b: a * b)

    def _op_div(self, register: str, operand: str) -> None:
        def _div(a: int, b: int) -> int:
            if b == 0:
                raise RuntimeError("division by zero")
            return a // b

        self._apply_arithmetic(register, operand, _div)

    def _op_mod(self, register: str, operand: str) -> None:
        def _mod(a: int, b: int) -> int:
            if b == 0:
                raise RuntimeError("modulo by zero")
            return a % b

        self._apply_arithmetic(register, operand, _mod)

    def _op_and(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, lambda a, b: a & b)

    def _op_or(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, lambda a, b: a | b)

    def _op_xor(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, lambda a, b: a ^ b)

    def _op_not(self, register: str) -> None:
        reg = self._require_register(register)
        value = self._registers[reg]
        if not isinstance(value, int):
            raise RuntimeError(f"register {register} does not contain an integer")
        self._registers[reg] = ~value

    def _op_shl(self, register: str, operand: str) -> None:
        def _shift_left(a: int, b: int) -> int:
            if b < 0:
                raise RuntimeError("shift amount must be non-negative")
            return a << b

        self._apply_arithmetic(register, operand, _shift_left)

    def _op_shr(self, register: str, operand: str) -> None:
        def _shift_right(a: int, b: int) -> int:
            if b < 0:
                raise RuntimeError("shift amount must be non-negative")
            return a >> b

        self._apply_arithmetic(register, operand, _shift_right)

    def _op_inc(self, register: str) -> None:
        self._apply_arithmetic(register, "1", lambda a, b: a + b)

    def _op_dec(self, register: str) -> None:
        self._apply_arithmetic(register, "1", lambda a, b: a - b)

    def _op_cmp(self, register: str, operand: str) -> None:
        reg = self._require_register(register)
        left = self._resolve_int(register)
        right = self._resolve_int(operand)
        if left < right:
            self._registers[reg] = -1
        elif left > right:
            self._registers[reg] = 1
        else:
            self._registers[reg] = 0

    def _op_jmp(self, target: str) -> None:
        self._jump(target)

    def _op_jz(self, register: str, target: str) -> None:
        value = self._resolve_int(register)
        if value == 0:
            self._jump(target)

    def _op_jnz(self, register: str, target: str) -> None:
        value = self._resolve_int(register)
        if value != 0:
            self._jump(target)

    def _op_print(self, operand: str) -> None:
        value = self._resolve_value(operand)
        self._output.append(str(value))

    def _op_out(self, operand: str) -> None:
        self._op_print(operand)

    def _op_assert(self, left: str, right: str) -> None:
        lhs = self._resolve_value(left)
        rhs = self._resolve_value(right)
        if lhs != rhs:
            raise RuntimeError(f"assertion failed: {lhs!r} != {rhs!r}")


def run_program(
    source: str,
    *,
    inputs: Mapping[str, int | str] | None = None,
    trace: bool = False,
) -> ExecutionResult:
    """Assemble and execute ``source`` in a freshly initialised computer."""

    computer = EchoComputer()
    computer.load(source)
    return computer.run(inputs=inputs, trace=trace)

