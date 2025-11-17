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
falling back to Python helpers.  Flow-control instructions (``JZ``/``JNZ``)
are complemented by comparison-aware jumps (``JLT``, ``JGT``, ``JLE``,
``JGE``, ``JEQ``, and ``JNE``) so that programs can make expressive
branching decisions without resorting to manual ``CMP`` bookkeeping.  The
instruction set also offers quality-of-life helpers like ``MIN``/``MAX``
and ``ABS``/``NEG`` so that programs can clamp or normalise values in a
single step.  Randomness primitives (``RSEED``/``RAND``) and built-in
instruction profiling further expand the sandbox for more advanced
experiments.  The high-level entry point, :func:`run_program`, parses,
executes, and returns a structured :class:`ExecutionResult`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import random
import shlex
import textwrap
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import copy

from .thoughtlog import thought_trace
from .quantum_flux_mapper import QuantumFluxMapper

__all__ = [
    "Instruction",
    "EchoProgram",
    "ExecutionResult",
    "assemble_program",
    "EchoComputer",
    "run_program",
    "AssemblyError",
    "EvolutionCycle",
    "evolve_program",
    "AdvancementCycle",
    "advance_program",
    "AssistantSuggestion",
    "EchoComputerAssistant",
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
    quantum_registers: Mapping[str, Mapping[str, object]] = field(default_factory=dict)
    instruction_counts: Mapping[str, int] = field(default_factory=dict)
    random_state: Mapping[str, object] = field(default_factory=dict)
    stack: Tuple[int | str, ...] = field(default_factory=tuple)
    call_stack: Tuple[int, ...] = field(default_factory=tuple)
    state_capsules: Mapping[str, Mapping[str, object]] = field(default_factory=dict)


class AssemblyError(ValueError):
    """Raised when the assembly language encounters invalid input."""


@dataclass(frozen=True)
class EvolutionCycle:
    """Represents the outcome of a single evolution cycle."""

    cycle: int
    inputs: Mapping[str, int | str]
    result: ExecutionResult


@dataclass(frozen=True)
class AdvancementCycle:
    """Represents a stateful advancement cycle across persistent runs."""

    cycle: int
    inputs: Mapping[str, int | str]
    before_registers: Mapping[str, int | str]
    before_memory: Mapping[str, int | str]
    result: ExecutionResult


@dataclass(frozen=True)
class AssistantSuggestion:
    """Container describing an assistant generated program template."""

    description: str
    program: str
    required_inputs: Tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


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

        label_candidate = stripped
        if "#" in stripped:
            label_candidate = stripped.split("#", 1)[0].rstrip()

        if label_candidate.endswith(":"):
            label = label_candidate[:-1].strip()
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
        self._quantum_registers: Dict[str, QuantumFluxMapper] = {}
        self._max_steps = max(1, int(max_steps))
        self._program: Tuple[Instruction, ...] = ()
        self._labels: Dict[str, int] = {}
        self._inputs: Dict[str, int | str] = {}
        self._stack: List[int | str] = []
        self._call_stack: List[int] = []
        self._state_capsules: Dict[str, Dict[str, object]] = {}
        self._pc = 0
        self._halted = False
        self._output: List[str] = []
        self._instruction_counts: Dict[str, int] = {}
        self._rng = random.Random()
        self._rng_seed: int | None = None
        self._rng_history: List[int] = []
        self._opcode_handlers = self._initialise_opcode_handlers()

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
    def quantum_registers(self) -> Mapping[str, QuantumFluxMapper]:
        return self._quantum_registers

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

    def reset_runtime(self, *, preserve_state: bool = False) -> None:
        """Reset runtime bookkeeping while optionally preserving state."""

        if not preserve_state:
            for key in self._registers:
                self._registers[key] = 0
            self._memory.clear()
            self._quantum_registers.clear()
        self._inputs.clear()
        self._stack.clear()
        self._call_stack.clear()
        self._pc = 0
        self._halted = False
        self._output.clear()
        self._instruction_counts.clear()
        self._rng_history.clear()
        if not preserve_state:
            self._state_capsules.clear()

    def run(
        self,
        *,
        inputs: Mapping[str, int | str] | None = None,
        trace: bool = False,
        max_steps: int | None = None,
        persist_state: bool = False,
    ) -> ExecutionResult:
        """Execute the loaded program and return an :class:`ExecutionResult`.

        Parameters
        ----------
        inputs:
            Optional mapping of input values that will be exposed via the
            ``?`` operand prefix.
        trace:
            When ``True`` the computer records a trace of executed
            instructions and includes it in the returned diagnostics.
        max_steps:
            Optional override for the per-run execution limit.  When omitted
            the limit configured on the computer instance is used.  The value
            is clamped to a minimum of ``1`` to avoid runaway loops.
        persist_state:
            When ``True`` register and memory contents are preserved between
            runs.  The program counter, stacks, and transient output buffer are
            still reset so that each execution begins from the first
            instruction with a clean call stack.
        """

        if not self._program:
            raise RuntimeError("no program loaded")

        self.reset_runtime(preserve_state=persist_state)
        if inputs:
            self._inputs.update({str(k): v for k, v in inputs.items()})

        step_limit = self._max_steps if max_steps is None else max(1, int(max_steps))
        diagnostics: List[str] = []
        task = "echo.digital_computer.run"
        meta = {
            "instructions": len(self._program),
            "max_steps": step_limit,
            "trace": trace,
        }

        with thought_trace(task=task, meta=meta) as tl:
            steps = 0
            while not self._halted:
                if self._pc < 0 or self._pc >= len(self._program):
                    raise RuntimeError(f"program counter out of range: {self._pc}")
                if steps >= step_limit:
                    raise RuntimeError(
                        f"execution exceeded max steps ({step_limit}); possible infinite loop"
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
            quantum_registers=self._snapshot_quantum_registers(),
            instruction_counts=dict(self._instruction_counts),
            random_state=self._snapshot_random_state(),
            stack=tuple(self._stack),
            call_stack=tuple(self._call_stack),
            state_capsules=self._snapshot_capsules(),
        )

    # --- Execution helpers -------------------------------------------------

    def _execute(self, instruction: Instruction) -> None:
        opcode = instruction.opcode
        operands = instruction.operands

        handler = self._opcode_handlers.get(opcode)
        if handler is None:
            raise RuntimeError(f"unsupported opcode: {opcode}")
        handler(*operands)
        self._instruction_counts[opcode] = self._instruction_counts.get(opcode, 0) + 1

    def _initialise_opcode_handlers(self) -> Dict[str, Callable[..., None]]:
        """Build and cache opcode handlers for fast dispatch during execution."""

        handlers: Dict[str, Callable[..., None]] = {}
        for attr_name in dir(self.__class__):
            if not attr_name.startswith("_op_"):
                continue
            opcode = attr_name[4:].upper()
            method = getattr(self, attr_name)
            if callable(method):
                handlers[opcode] = method  # type: ignore[assignment]
        return handlers

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
            return int(operand, 0)
        except ValueError:
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

    def _require_qubit(self, identifier: str) -> QuantumFluxMapper:
        if identifier not in self._quantum_registers:
            raise RuntimeError(f"unknown quantum register: {identifier}")
        return self._quantum_registers[identifier]

    def _snapshot_quantum_registers(self) -> Dict[str, Mapping[str, object]]:
        snapshot: Dict[str, Mapping[str, object]] = {}
        for name, mapper in self._quantum_registers.items():
            alpha, beta = mapper.state
            snapshot[name] = {
                "state": (
                    (alpha.real, alpha.imag),
                    (beta.real, beta.imag),
                ),
                "bloch": tuple(mapper.bloch_coordinates()),
                "history": tuple(mapper.history),
            }
        return snapshot

    def _snapshot_random_state(self) -> Mapping[str, object]:
        return {
            "seed": self._rng_seed,
            "history": tuple(self._rng_history),
        }

    def _snapshot_capsules(self) -> Dict[str, Mapping[str, object]]:
        return {name: copy.deepcopy(payload) for name, payload in self._state_capsules.items()}

    def _coerce_capsule_identifier(self, operand: str) -> str:
        try:
            value = self._resolve_value(operand)
        except RuntimeError:
            value = operand
        name = str(value).strip()
        if not name:
            raise RuntimeError("capsule identifier must not be empty")
        return name

    def _coerce_capsule_metadata(self, operand: Optional[str]) -> Optional[str]:
        if operand is None:
            return None
        try:
            value = self._resolve_value(operand)
        except RuntimeError:
            value = operand
        text = str(value).strip()
        return text or None

    @staticmethod
    def _iso_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_state_capsule(self) -> Dict[str, object]:
        return {
            "captured_at": self._iso_timestamp(),
            "pc": self._pc,
            "halted": self._halted,
            "registers": dict(self._registers),
            "memory": dict(self._memory),
            "stack": list(self._stack),
            "call_stack": list(self._call_stack),
            "quantum": self._snapshot_quantum_registers(),
            "random": self._snapshot_random_state(),
        }

    def _apply_capsule(self, capsule: Mapping[str, object], *, include_control: bool = False) -> None:
        registers = capsule.get("registers")
        if isinstance(registers, Mapping):
            for name in self._registers:
                self._registers[name] = registers.get(name, 0)
        memory = capsule.get("memory")
        if isinstance(memory, Mapping):
            self._memory.clear()
            self._memory.update({str(k): v for k, v in memory.items()})
        stack = capsule.get("stack")
        if isinstance(stack, Iterable):
            self._stack = list(stack)
        call_stack = capsule.get("call_stack")
        if isinstance(call_stack, Iterable):
            self._call_stack = [int(value) for value in call_stack]
        if include_control:
            pc_value = capsule.get("pc")
            if isinstance(pc_value, int):
                self._pc = pc_value
            halted_value = capsule.get("halted")
            if isinstance(halted_value, bool):
                self._halted = halted_value
        quantum_snapshot = capsule.get("quantum")
        if isinstance(quantum_snapshot, Mapping):
            self._restore_quantum_registers(quantum_snapshot)
        random_snapshot = capsule.get("random")
        if isinstance(random_snapshot, Mapping):
            self._restore_random_state(random_snapshot)

    def _restore_quantum_registers(self, snapshot: Mapping[str, Mapping[str, object]]) -> None:
        self._quantum_registers.clear()
        for name, payload in snapshot.items():
            mapper = QuantumFluxMapper()
            state = payload.get("state")
            if isinstance(state, Iterable):
                state_pairs = list(state)
                if len(state_pairs) == 2:
                    try:
                        alpha_pair = tuple(state_pairs[0])
                        beta_pair = tuple(state_pairs[1])
                        alpha = complex(float(alpha_pair[0]), float(alpha_pair[1]))
                        beta = complex(float(beta_pair[0]), float(beta_pair[1]))
                        mapper.state = (alpha, beta)
                    except Exception:  # pragma: no cover - defensive fallback
                        mapper.state = (1 + 0j, 0 + 0j)
            history = payload.get("history")
            if isinstance(history, Iterable):
                mapper.history = [str(entry) for entry in history]
            self._quantum_registers[str(name)] = mapper

    def _restore_random_state(self, payload: Mapping[str, object]) -> None:
        history = payload.get("history")
        if isinstance(history, Iterable):
            self._rng_history = [int(entry) for entry in history]
        seed = payload.get("seed")
        if isinstance(seed, int):
            self._rng_seed = seed
            self._rng.seed(seed)
        else:
            self._rng_seed = None
            self._rng.seed()
    def _resolve_float(self, operand: str) -> float:
        try:
            value = self._resolve_value(operand)
        except RuntimeError:
            value = operand
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (TypeError, ValueError) as error:
            raise RuntimeError(f"operand {operand!r} does not resolve to a numeric value") from error

    def _initialise_qubit_basis(self, mapper: QuantumFluxMapper, descriptor: object) -> str:
        basis = str(descriptor).strip()
        if not basis:
            basis = "0"
        cleaned = basis.replace("|", "").replace("⟩", "").upper()
        if cleaned in {"0", "ZERO"}:
            mapper.state = (1 + 0j, 0 + 0j)
            return "|0⟩"
        if cleaned in {"1", "ONE"}:
            mapper.apply_gate("X")
            return "|1⟩"
        if cleaned in {"+", "PLUS"}:
            mapper.apply_gate("H")
            return "|+⟩"
        if cleaned in {"-", "MINUS"}:
            mapper.apply_gate("H")
            mapper.apply_gate("Z")
            return "|-⟩"
        raise RuntimeError("QINIT basis must be one of 0, 1, +, or -")

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

    def _op_capture(self, identifier: str, metadata: str | None = None) -> None:
        name = self._coerce_capsule_identifier(identifier)
        capsule = self._build_state_capsule()
        capsule["metadata"] = self._coerce_capsule_metadata(metadata)
        self._state_capsules[name] = capsule

    def _op_restore(self, identifier: str, mode: str | None = None) -> None:
        name = self._coerce_capsule_identifier(identifier)
        capsule = self._state_capsules.get(name)
        if capsule is None:
            raise RuntimeError(f"unknown capsule: {name}")
        include_control = False
        if mode is not None:
            try:
                resolved = self._resolve_value(mode)
            except RuntimeError:
                resolved = mode
            include_control = str(resolved).strip().upper() in {"WITHPC", "FULL"}
        self._apply_capsule(capsule, include_control=include_control)

    def _op_capdrop(self, identifier: str) -> None:
        name = self._coerce_capsule_identifier(identifier)
        self._state_capsules.pop(name, None)

    def _op_capcount(self, register: str) -> None:
        reg = self._require_register(register)
        self._registers[reg] = len(self._state_capsules)

    def _op_capexists(self, register: str, identifier: str) -> None:
        reg = self._require_register(register)
        name = self._coerce_capsule_identifier(identifier)
        self._registers[reg] = 1 if name in self._state_capsules else 0

    def _op_set(self, destination: str, operand: str) -> None:
        if destination in self._registers:
            self._registers[destination] = self._resolve_value(operand)
            return
        if destination.startswith("@"):
            self._memory[destination[1:]] = self._resolve_value(operand)
            return
        raise RuntimeError("SET destination must be a register or memory address")

    def _op_rseed(self, seed: str) -> None:
        value = self._resolve_int(seed)
        self._rng.seed(value)
        self._rng_seed = value

    def _op_rand(self, register: str, low: str, high: str) -> None:
        reg = self._require_register(register)
        lower = self._resolve_int(low)
        upper = self._resolve_int(high)
        if lower > upper:
            raise RuntimeError("RAND requires the lower bound to be <= upper bound")
        generated = self._rng.randint(lower, upper)
        self._registers[reg] = generated
        self._rng_history.append(generated)

    def _op_qinit(self, identifier: str, basis: str | None = None) -> None:
        name = identifier.strip()
        if not name:
            raise RuntimeError("QINIT requires a qubit identifier")
        mapper = QuantumFluxMapper()
        if basis is None:
            descriptor: object = "0"
        else:
            try:
                descriptor = self._resolve_value(basis)
            except RuntimeError:
                descriptor = basis
        prepared = self._initialise_qubit_basis(mapper, descriptor)
        mapper.history.append(f"Initialised {name} in {prepared}")
        self._quantum_registers[name] = mapper

    def _op_qgate(self, identifier: str, gate: str) -> None:
        mapper = self._require_qubit(identifier)
        gate_value = self._resolve_value(gate)
        gate_name = str(gate_value).strip().upper()
        if not gate_name:
            raise RuntimeError("QGATE requires a gate name")
        mapper.apply_gate(gate_name)

    def _op_qrot(self, identifier: str, axis: str, angle: str) -> None:
        mapper = self._require_qubit(identifier)
        axis_name = axis.strip().upper()
        if axis_name not in {"X", "Y", "Z"}:
            raise RuntimeError("QROT axis must be one of X, Y, or Z")
        angle_value = self._resolve_float(angle)
        mapper.apply_rotation(axis_name, angle_value)

    def _op_qmeasure(self, register: str, identifier: str) -> None:
        mapper = self._require_qubit(identifier)
        reg = self._require_register(register)
        outcome = mapper.measure()
        self._registers[reg] = int(outcome)

    def _apply_arithmetic(self, register: str, operand: str, func) -> None:
        reg = self._require_register(register)
        left = self._registers[reg]
        if not isinstance(left, int):
            raise RuntimeError(f"register {register} does not contain an integer")
        right = self._resolve_int(operand)
        self._registers[reg] = func(left, right)

    def _int_register_value(self, register: str) -> int:
        reg = self._require_register(register)
        value = self._registers[reg]
        if not isinstance(value, int):
            raise RuntimeError(f"register {register} does not contain an integer")
        return value

    def _jump_if_order(
        self,
        register: str,
        operand: str,
        target: str,
        comparator: Callable[[int, int], bool],
    ) -> None:
        left = self._int_register_value(register)
        right = self._resolve_int(operand)
        if comparator(left, right):
            self._jump(target)

    def _jump_if_equal(
        self,
        register: str,
        operand: str,
        target: str,
        *,
        negate: bool = False,
    ) -> None:
        self._require_register(register)
        left = self._resolve_value(register)
        right = self._resolve_value(operand)
        condition = left == right
        if negate:
            condition = not condition
        if condition:
            self._jump(target)

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

    def _op_min(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, min)

    def _op_max(self, register: str, operand: str) -> None:
        self._apply_arithmetic(register, operand, max)

    def _op_abs(self, register: str) -> None:
        reg = self._require_register(register)
        value = self._registers[reg]
        if not isinstance(value, int):
            raise RuntimeError(f"register {register} does not contain an integer")
        self._registers[reg] = abs(value)

    def _op_neg(self, register: str) -> None:
        reg = self._require_register(register)
        value = self._registers[reg]
        if not isinstance(value, int):
            raise RuntimeError(f"register {register} does not contain an integer")
        self._registers[reg] = -value

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
        left = self._int_register_value(reg)
        right = self._resolve_int(operand)
        if left < right:
            self._registers[reg] = -1
        elif left > right:
            self._registers[reg] = 1
        else:
            self._registers[reg] = 0

    def _op_halt(self, *operands: str) -> None:
        self._halted = True

    def _op_nop(self, *operands: str) -> None:
        return

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

    def _op_jlt(self, register: str, operand: str, target: str) -> None:
        self._jump_if_order(register, operand, target, lambda a, b: a < b)

    def _op_jgt(self, register: str, operand: str, target: str) -> None:
        self._jump_if_order(register, operand, target, lambda a, b: a > b)

    def _op_jle(self, register: str, operand: str, target: str) -> None:
        self._jump_if_order(register, operand, target, lambda a, b: a <= b)

    def _op_jge(self, register: str, operand: str, target: str) -> None:
        self._jump_if_order(register, operand, target, lambda a, b: a >= b)

    def _op_jeq(self, register: str, operand: str, target: str) -> None:
        self._jump_if_equal(register, operand, target)

    def _op_jne(self, register: str, operand: str, target: str) -> None:
        self._jump_if_equal(register, operand, target, negate=True)

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

    def _op_push(self, operand: str) -> None:
        self._stack.append(self._resolve_value(operand))

    def _op_pop(self, register: str) -> None:
        if not self._stack:
            raise RuntimeError("stack underflow")
        reg = self._require_register(register)
        self._registers[reg] = self._stack.pop()

    def _op_peek(self, register: str, offset: str | None = None) -> None:
        if not self._stack:
            raise RuntimeError("stack is empty")
        reg = self._require_register(register)
        depth = 0 if offset is None else self._resolve_int(offset)
        if depth < 0:
            raise RuntimeError("PEEK offset must be non-negative")
        if depth >= len(self._stack):
            raise RuntimeError("PEEK offset exceeds stack depth")
        self._registers[reg] = self._stack[-1 - depth]

    def _op_stacklen(self, register: str) -> None:
        reg = self._require_register(register)
        self._registers[reg] = len(self._stack)

    def _op_calldepth(self, register: str) -> None:
        reg = self._require_register(register)
        self._registers[reg] = len(self._call_stack)

    def _op_call(self, target: str) -> None:
        if self._pc < 0 or self._pc > len(self._program):
            raise RuntimeError(f"call return address out of range: {self._pc}")
        self._call_stack.append(self._pc)
        self._jump(target)

    def _op_ret(self, *operands: str) -> None:
        if not self._call_stack:
            raise RuntimeError("return stack empty")
        address = self._call_stack.pop()
        if address < 0 or address >= len(self._program):
            raise RuntimeError(f"return address out of range: {address}")
        self._pc = address


def run_program(
    source: str,
    *,
    inputs: Mapping[str, int | str] | None = None,
    trace: bool = False,
    max_steps: int | None = None,
) -> ExecutionResult:
    """Assemble and execute ``source`` in a freshly initialised computer."""

    computer = EchoComputer()
    computer.load(source)
    return computer.run(inputs=inputs, trace=trace, max_steps=max_steps)


def evolve_program(
    program: EchoProgram | str | Sequence[Instruction],
    *,
    input_series: Iterable[Mapping[str, int | str]],
    max_steps: int = 1024,
) -> List[EvolutionCycle]:
    """Run ``program`` across ``input_series`` and collect cycle results.

    The helper offers a higher-level orchestration primitive for experiments
    that need to repeatedly execute the same assembly program with varied
    inputs.  It mirrors the "evolution" terminology used throughout the Echo
    project by treating each execution as a cycle and returning a structured
    report describing how the virtual computer responded.

    Parameters
    ----------
    program:
        The program to execute.  This can be a raw assembly string,
        pre-assembled :class:`EchoProgram`, or a sequence of
        :class:`Instruction` instances.
    input_series:
        Iterable of input mappings for each cycle.  Each mapping is converted
        to a plain ``dict`` before execution to avoid leaking references back
        to the caller.
    max_steps:
        Optional override for the per-cycle execution limit.

    Returns
    -------
    List[EvolutionCycle]
        Ordered sequence of cycle reports, one per entry provided via
        ``input_series``.
    """

    computer = EchoComputer(max_steps=max_steps)
    computer.load(program)

    cycles: List[EvolutionCycle] = []
    for cycle_index, inputs in enumerate(input_series, start=1):
        prepared_inputs = {str(key): value for key, value in dict(inputs).items()}
        result = computer.run(inputs=prepared_inputs)
        cycles.append(
            EvolutionCycle(
                cycle=cycle_index,
                inputs=dict(prepared_inputs),
                result=result,
            )
        )

    return cycles


def advance_program(
    program: EchoProgram | str | Sequence[Instruction],
    *,
    input_series: Iterable[Mapping[str, int | str]],
    max_steps: int = 1024,
) -> List[AdvancementCycle]:
    """Execute ``program`` across ``input_series`` while preserving state.

    The helper mirrors :func:`evolve_program` but continues to reuse the same
    computer instance between cycles without clearing registers or memory.  It
    captures the state prior to each execution so that callers can trace how
    the program evolves over time.

    Returns
    -------
    List[AdvancementCycle]
        Ordered sequence of advancement reports pairing each input mapping
        with its pre-execution state snapshot and resulting execution report.
    """

    computer = EchoComputer(max_steps=max_steps)
    computer.load(program)

    cycles: List[AdvancementCycle] = []
    for cycle_index, inputs in enumerate(input_series, start=1):
        prepared_inputs = {str(key): value for key, value in dict(inputs).items()}
        before_registers = dict(computer.registers)
        before_memory = dict(computer.memory)
        result = computer.run(inputs=prepared_inputs, persist_state=True)
        cycles.append(
            AdvancementCycle(
                cycle=cycle_index,
                inputs=dict(prepared_inputs),
                before_registers=before_registers,
                before_memory=before_memory,
                result=result,
            )
        )

    return cycles


class EchoComputerAssistant:
    """Lightweight assistant that offers curated digital computer programs."""

    def __init__(
        self,
        computer_factory: Callable[[], EchoComputer] | None = None,
    ) -> None:
        self._computer_factory = computer_factory or EchoComputer
        self._templates: Tuple[
            Tuple[Tuple[str, ...], Callable[[str], AssistantSuggestion]],
            ...,
        ] = (
            (("factorial",), self._build_factorial),
            (("fibonacci",), self._build_fibonacci),
            (("sum",), self._build_sum_to_n),
            (("add", "numbers"), self._build_sum_inputs),
            (("max",), self._build_max_pair),
            (("echo",), self._build_echo),
            (("clamp",), self._build_clamp),
        )

    def suggest(self, prompt: str) -> AssistantSuggestion:
        """Return a program suggestion that matches ``prompt`` keywords.

        The assistant relies on a deterministic set of keyword heuristics so that
        behaviour remains predictable and auditable within tests.  Prompts are
        normalised to lower case before matching.  When no specialised template is
        selected the assistant falls back to a generic echo program.
        """

        normalised = prompt.lower()
        for keywords, builder in self._templates:
            if all(keyword in normalised for keyword in keywords):
                return builder(normalised)
        return self._build_echo(normalised)

    def execute(
        self,
        suggestion: AssistantSuggestion,
        *,
        inputs: Mapping[str, int | str] | None = None,
        trace: bool = False,
        max_steps: int | None = None,
    ) -> ExecutionResult:
        """Run ``suggestion`` using a freshly constructed computer instance."""

        provided_inputs = dict(inputs or {})
        missing = [key for key in suggestion.required_inputs if key not in provided_inputs]
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise KeyError(f"missing required inputs: {missing_str}")

        computer = self._computer_factory()
        computer.load(suggestion.program)
        return computer.run(inputs=provided_inputs, trace=trace, max_steps=max_steps)

    def available_templates(self) -> Tuple[str, ...]:
        """Return the registered template keywords for introspection."""

        return tuple(" ".join(keywords) for keywords, _ in self._templates)

    @staticmethod
    def _build_factorial(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A 1
            LOAD B ?n
            SET @result 1
            loop:
                JZ B done
                MUL A B
                STORE A @result
                DEC B
                JMP loop
            done:
                PRINT @result
                HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Computes the factorial of the input `n` and prints the product.",
            program=program,
            required_inputs=("n",),
            metadata={
                "template": "factorial",
                "category": "math",
                "keywords": ("factorial",),
                "estimated_steps": 9,
                "version": 1,
            },
        )

    @staticmethod
    def _build_fibonacci(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A 0
            LOAD B 1
            LOAD C ?terms
            loop:
                JZ C done
                PRINT A
                LOAD D A
                LOAD A B
                ADD D B
                LOAD B D
                DEC C
                JMP loop
            done:
                HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Streams Fibonacci numbers up to the provided number of `terms`.",
            program=program,
            required_inputs=("terms",),
            metadata={
                "template": "fibonacci",
                "category": "sequence",
                "keywords": ("fibonacci",),
                "estimated_steps": "O(n)",
                "version": 1,
            },
        )

    @staticmethod
    def _build_sum_to_n(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A 0
            LOAD B ?limit
            loop:
                JZ B done
                ADD A B
                DEC B
                JMP loop
            done:
                PRINT A
                HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Accumulates the sum of integers from 1 through the input `limit`.",
            program=program,
            required_inputs=("limit",),
            metadata={
                "template": "sum_to_n",
                "category": "math",
                "keywords": ("sum", "limit"),
                "estimated_steps": "O(n)",
                "version": 1,
            },
        )

    @staticmethod
    def _build_sum_inputs(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A ?left
            ADD A ?right
            PRINT A
            HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Adds the `left` and `right` inputs and prints the result.",
            program=program,
            required_inputs=("left", "right"),
            metadata={
                "template": "sum_inputs",
                "category": "math",
                "keywords": ("add", "numbers"),
                "estimated_steps": 6,
                "version": 1,
            },
        )

    @staticmethod
    def _build_max_pair(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A ?left
            LOAD B ?right
            JGE A B left_is_max
            PRINT B
            HALT
            left_is_max:
                PRINT A
                HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Prints the larger of the `left` and `right` inputs.",
            program=program,
            required_inputs=("left", "right"),
            metadata={
                "template": "max_pair",
                "category": "comparison",
                "keywords": ("max", "compare"),
                "estimated_steps": 8,
                "version": 1,
            },
        )

    @staticmethod
    def _build_echo(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A ?value
            PRINT A
            HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Echoes the provided `value` input back to the output channel.",
            program=program,
            required_inputs=("value",),
            metadata={
                "template": "echo",
                "category": "io",
                "keywords": ("echo",),
                "estimated_steps": 3,
                "version": 1,
            },
        )

    @staticmethod
    def _build_clamp(_: str) -> AssistantSuggestion:
        program = textwrap.dedent(
            """
            LOAD A ?value
            MAX A ?low
            MIN A ?high
            PRINT A
            HALT
            """
        ).strip()
        return AssistantSuggestion(
            description="Constrains `value` to the inclusive [low, high] range and prints it.",
            program=program,
            required_inputs=("value", "low", "high"),
            metadata={
                "template": "clamp",
                "category": "math",
                "keywords": ("clamp", "range"),
                "estimated_steps": 6,
                "version": 1,
            },
        )

