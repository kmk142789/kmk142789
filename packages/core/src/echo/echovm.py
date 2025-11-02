"""Compact stack-based virtual machine with assembler and extensible syscalls.

The :mod:`echo.echovm` module provides a tiny stack-oriented computer that can
assemble a deliberately small assembly language, execute the resulting
bytecode, and grow over time through a syscall interface.  The design is
minimal by default but includes a virtual file system extension and a plug-in
mechanism so external modules can register new "devices" without modifying the
core interpreter.

The VM understands the following opcodes:

``PUSH`` (value)       -- push an integer onto the stack
``POP``                -- discard the top of the stack
``DUP``                -- duplicate the top stack value
``ADD``/``SUB``/``MUL``/``DIV`` -- integer arithmetic
``PRINT``              -- pop and print a value
``JMP`` (addr)         -- jump to an absolute bytecode address
``JZ`` (addr)          -- pop and jump when the value equals zero
``SYS`` (num)          -- invoke a registered syscall
``HALT``               -- terminate the program

Assembly syntax mirrors the structure used in the original EchoVM sketch:

* One instruction per line with optional integer argument.
* Labels end with ``:`` and comments start with ``;``.
* ``JMP`` and ``JZ`` accept either a label name or a literal address.

The helper :func:`create_vm` instantiates an :class:`EchoVM`, registers the
standard syscalls (including the virtual filesystem), and optionally installs
plug-in devices declared via :func:`device`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, MutableMapping, MutableSequence, Sequence

__all__ = [
    "OP_CODES",
    "OP_NAMES",
    "AssemblyError",
    "assemble",
    "EchoVM",
    "VirtualFileSystem",
    "register_default_syscalls",
    "device",
    "register_devices",
    "create_vm",
    "EXAMPLE_PROGRAM",
]

# ---------------------------------------------------------------------------
# Instruction set
# ---------------------------------------------------------------------------

OP_CODES: Dict[str, int] = {
    "NOP": 0x00,
    "PUSH": 0x01,
    "POP": 0x02,
    "DUP": 0x03,
    "ADD": 0x04,
    "SUB": 0x05,
    "MUL": 0x06,
    "DIV": 0x07,
    "PRINT": 0x08,
    "JMP": 0x09,
    "JZ": 0x0A,
    "HALT": 0x0B,
    "SYS": 0x0C,
}

OP_NAMES: Dict[int, str] = {code: name for name, code in OP_CODES.items()}


class AssemblyError(ValueError):
    """Raised when assembly input cannot be parsed."""


# ---------------------------------------------------------------------------
# Assembler
# ---------------------------------------------------------------------------

def assemble(source: str) -> List[int]:
    """Assemble ``source`` and return the resulting bytecode list."""

    lines = []
    for raw_line in source.splitlines():
        line, *_ = raw_line.split(";", 1)
        stripped = line.strip()
        if not stripped:
            continue
        lines.append(stripped)

    labels: Dict[str, int] = {}
    program_counter = 0
    filtered: List[str] = []

    for entry in lines:
        if entry.endswith(":"):
            label = entry[:-1]
            if not label:
                raise AssemblyError("empty label declaration")
            if label in labels:
                raise AssemblyError(f"label {label!r} already defined")
            labels[label] = program_counter
            continue

        filtered.append(entry)
        mnemonic, *args = entry.split()
        if mnemonic not in OP_CODES:
            raise AssemblyError(f"unknown opcode {mnemonic!r}")
        program_counter += 1
        if mnemonic in {"PUSH", "JMP", "JZ", "SYS"}:
            if not args:
                raise AssemblyError(f"opcode {mnemonic!r} requires an argument")
            program_counter += 1
        elif args:
            raise AssemblyError(f"opcode {mnemonic!r} takes no arguments")

    bytecode: List[int] = []
    for entry in filtered:
        mnemonic, *args = entry.split()
        bytecode.append(OP_CODES[mnemonic])
        if mnemonic in {"PUSH", "SYS"}:
            bytecode.append(int(args[0]))
        elif mnemonic in {"JMP", "JZ"}:
            target = args[0]
            try:
                address = labels[target]
            except KeyError:
                address = int(target)
            bytecode.append(address)

    return bytecode


# ---------------------------------------------------------------------------
# Virtual machine
# ---------------------------------------------------------------------------

Stack = MutableSequence[int]
Syscall = Callable[["EchoVM", Stack], None]


@dataclass
class EchoVM:
    """Tiny stack-based virtual machine executing assembled bytecode."""

    code: List[int] = field(default_factory=list)
    pc: int = 0
    stack: List[int] = field(default_factory=list)
    running: bool = False
    syscalls: MutableMapping[int, Syscall] = field(default_factory=dict)
    debug: bool = False

    def load(self, code: Sequence[int]) -> None:
        """Replace the currently loaded code with ``code``."""

        self.code = list(code)
        self.pc = 0
        self.stack.clear()
        self.running = False

    def reg_syscall(self, number: int, handler: Syscall) -> None:
        """Register ``handler`` as syscall ``number``."""

        existing = self.syscalls.get(number)
        if existing is not None and existing is not handler:
            raise ValueError(f"syscall {number} already registered")
        self.syscalls[number] = handler

    def fetch(self) -> int:
        if self.pc >= len(self.code):
            raise RuntimeError("program counter out of bounds")
        op = self.code[self.pc]
        self.pc += 1
        return op

    def fetch_arg(self) -> int:
        return self.fetch()

    def pop(self) -> int:
        if not self.stack:
            raise RuntimeError("stack underflow")
        return self.stack.pop()

    def push(self, value: int) -> None:
        self.stack.append(value)

    def run(self) -> None:
        """Run the loaded program until :opcode:`HALT` or program end."""

        self.running = True
        while self.running and self.pc < len(self.code):
            op = self.fetch()
            if self.debug:
                opname = OP_NAMES.get(op, "???")
                print(f"[pc={self.pc - 1:03}] {opname:<5} stack={self.stack}")

            if op == OP_CODES["NOP"]:
                continue
            if op == OP_CODES["PUSH"]:
                self.push(self.fetch_arg())
                continue
            if op == OP_CODES["POP"]:
                self.pop()
                continue
            if op == OP_CODES["DUP"]:
                value = self.pop()
                self.push(value)
                self.push(value)
                continue
            if op == OP_CODES["ADD"]:
                b = self.pop()
                a = self.pop()
                self.push(a + b)
                continue
            if op == OP_CODES["SUB"]:
                b = self.pop()
                a = self.pop()
                self.push(a - b)
                continue
            if op == OP_CODES["MUL"]:
                b = self.pop()
                a = self.pop()
                self.push(a * b)
                continue
            if op == OP_CODES["DIV"]:
                b = self.pop()
                a = self.pop()
                if b == 0:
                    raise ZeroDivisionError("division by zero")
                self.push(int(a / b))
                continue
            if op == OP_CODES["PRINT"]:
                print(self.pop())
                continue
            if op == OP_CODES["JMP"]:
                self.pc = self.fetch_arg()
                continue
            if op == OP_CODES["JZ"]:
                address = self.fetch_arg()
                if self.pop() == 0:
                    self.pc = address
                continue
            if op == OP_CODES["SYS"]:
                number = self.fetch_arg()
                handler = self.syscalls.get(number)
                if handler is None:
                    raise RuntimeError(f"unknown syscall {number}")
                handler(self, self.stack)
                continue
            if op == OP_CODES["HALT"]:
                self.running = False
                break
            raise RuntimeError(f"illegal opcode {op}")


# ---------------------------------------------------------------------------
# Built-in syscalls
# ---------------------------------------------------------------------------


def sys_print_str(vm: EchoVM, stack: Stack) -> None:
    """Pop length and character codes to print a string."""

    length = vm.pop()
    chars = [chr(vm.pop()) for _ in range(length)][::-1]
    print("".join(chars))


def sys_time(vm: EchoVM, stack: Stack) -> None:
    """Push a coarse integer timestamp onto the stack."""

    import time

    vm.push(int(time.time()))


class VirtualFileSystem:
    """In-memory key/value store that acts as a virtual disk."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}

    def write(self, key: str, value: str) -> None:
        self._store[key] = value

    def read(self, key: str) -> str:
        return self._store.get(key, "")

    def ls(self) -> List[str]:
        return list(self._store.keys())


DEFAULT_VFS = VirtualFileSystem()


def _make_fs_write(vfs: VirtualFileSystem) -> Syscall:
    def handler(vm: EchoVM, stack: Stack) -> None:
        value_length = vm.pop()
        value_chars = [chr(vm.pop()) for _ in range(value_length)][::-1]
        key_length = vm.pop()
        key_chars = [chr(vm.pop()) for _ in range(key_length)][::-1]
        vfs.write("".join(key_chars), "".join(value_chars))

    return handler


def _make_fs_read(vfs: VirtualFileSystem) -> Syscall:
    def handler(vm: EchoVM, stack: Stack) -> None:
        key_length = vm.pop()
        key_chars = [chr(vm.pop()) for _ in range(key_length)][::-1]
        value = vfs.read("".join(key_chars))
        for ch in value:
            vm.push(ord(ch))
        vm.push(len(value))

    return handler


def _make_fs_ls(vfs: VirtualFileSystem) -> Syscall:
    def handler(vm: EchoVM, stack: Stack) -> None:
        names = ",".join(vfs.ls())
        for ch in reversed(names):
            vm.push(ord(ch))
        vm.push(len(names))

    return handler


def register_default_syscalls(vm: EchoVM, *, vfs: VirtualFileSystem | None = None) -> None:
    """Install the standard syscall set on ``vm``."""

    fs = vfs or DEFAULT_VFS
    vm.reg_syscall(1, sys_print_str)
    vm.reg_syscall(2, sys_time)
    vm.reg_syscall(10, _make_fs_write(fs))
    vm.reg_syscall(11, _make_fs_read(fs))
    vm.reg_syscall(12, _make_fs_ls(fs))


# ---------------------------------------------------------------------------
# Device plug-ins
# ---------------------------------------------------------------------------

DEVICE_REGISTRY: Dict[str, tuple[int, Syscall]] = {}
_NEXT_DEVICE = 32


def _allocate_syscall_number() -> int:
    global _NEXT_DEVICE
    number = _NEXT_DEVICE
    _NEXT_DEVICE += 1
    return number


def device(name: str, *, number: int | None = None) -> Callable[[Syscall], Syscall]:
    """Decorator that registers ``name`` as a plug-in device syscall."""

    def decorator(func: Syscall) -> Syscall:
        if name in DEVICE_REGISTRY:
            raise ValueError(f"device {name!r} already registered")
        assigned = number if number is not None else _allocate_syscall_number()
        DEVICE_REGISTRY[name] = (assigned, func)
        return func

    return decorator


def register_devices(vm: EchoVM, *, names: Iterable[str] | None = None) -> Dict[str, int]:
    """Register plug-in devices on ``vm`` and return the assigned numbers."""

    if names is None:
        items = DEVICE_REGISTRY.items()
    else:
        items = ((name, DEVICE_REGISTRY[name]) for name in names)

    mapping: Dict[str, int] = {}
    for name, (number, handler) in items:
        existing = vm.syscalls.get(number)
        if existing is not None and existing is not handler:
            raise ValueError(f"syscall {number} already bound to another handler")
        vm.reg_syscall(number, handler)
        mapping[name] = number
    return mapping


@device("rng32")
def _device_rng(vm: EchoVM, stack: Stack) -> None:
    import random

    vm.push(random.getrandbits(32))


# ---------------------------------------------------------------------------
# Helper factory + example
# ---------------------------------------------------------------------------


def create_vm(
    source: Sequence[int] | str | None = None,
    *,
    debug: bool = False,
    install_default_syscalls: bool = True,
    install_devices: bool = True,
    vfs: VirtualFileSystem | None = None,
) -> EchoVM:
    """Return a configured :class:`EchoVM` instance."""

    if source is None:
        code: List[int] = []
    elif isinstance(source, str):
        code = assemble(source)
    else:
        code = list(source)

    vm = EchoVM(code=code, debug=debug)
    if install_default_syscalls:
        register_default_syscalls(vm, vfs=vfs)
    if install_devices:
        register_devices(vm)
    return vm


EXAMPLE_PROGRAM = """
; print "ECHO"
PUSH 69
PUSH 67
PUSH 72
PUSH 79
PUSH 4
SYS 1

; sum 1..5 -> PRINT
PUSH 0
PUSH 1
loop:
DUP
PUSH 6
SUB
JZ end
DUP
PUSH 1
SUB
POP
ADD
PUSH 1
ADD
JMP loop
end:
PRINT
HALT
"""


def _run_example() -> None:
    vm = create_vm(EXAMPLE_PROGRAM)
    vm.run()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    _run_example()
