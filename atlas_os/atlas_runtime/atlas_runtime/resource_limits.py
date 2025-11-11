"""Resource limit enforcement for the runtime sandbox."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ResourceLimits:
    cpu_time_ms: int
    memory_bytes: int
    instruction_count: int

    def check(self, *, cpu_time_ms: int, memory_bytes: int, instruction_count: int) -> None:
        if cpu_time_ms > self.cpu_time_ms:
            raise RuntimeError("CPU time exceeded")
        if memory_bytes > self.memory_bytes:
            raise MemoryError("Memory limit exceeded")
        if instruction_count > self.instruction_count:
            raise RuntimeError("Instruction budget exhausted")


__all__ = ["ResourceLimits"]
