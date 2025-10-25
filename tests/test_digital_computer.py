"""Tests for the Echo digital computer sandbox."""

from __future__ import annotations

import pytest

from echo.digital_computer import (
    AssemblyError,
    EchoComputer,
    assemble_program,
    run_program,
)


def test_assemble_program_builds_labels() -> None:
    source = """
    # toy program
    start:
        LOAD A 5
        HALT
    """

    program = assemble_program(source)

    assert program.labels["start"] == 0
    assert [instr.opcode for instr in program.instructions] == ["LOAD", "HALT"]
    assert program.instructions[0].operands == ("A", "5")


def test_run_program_factorial() -> None:
    program = """
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

    result = run_program(program, inputs={"n": 5})

    assert result.halted is True
    assert result.output == ("120",)
    assert result.registers["A"] == 120
    assert result.memory["result"] == 120


def test_trace_and_assertion_failure() -> None:
    computer = EchoComputer(max_steps=16)
    computer.load(
        """
        LOAD A 2
        HALT
        """
    )

    trace_result = computer.run(trace=True)
    assert trace_result.diagnostics[0].startswith("0000: LOAD")
    assert trace_result.diagnostics[-1].startswith("0001: HALT")

    computer.load(
        """
        ASSERT 1 2
        HALT
        """
    )

    with pytest.raises(RuntimeError):
        computer.run()


def test_duplicate_label_raises() -> None:
    source = """
    again:
        NOP
    again:
        HALT
    """

    with pytest.raises(AssemblyError):
        assemble_program(source)


def test_bitwise_operations_and_shifts() -> None:
    program = """
    LOAD A 12
    AND A 5
    STORE A @and
    SHL A 2
    STORE A @shl
    LOAD B 12
    OR B 5
    STORE B @or
    LOAD C 12
    XOR C 5
    STORE C @xor
    LOAD D 5
    NOT D
    STORE D @not
    LOAD E 128
    SHR E 3
    STORE E @shr
    HALT
    """

    result = run_program(program)

    assert result.memory["and"] == 12 & 5
    assert result.memory["shl"] == (12 & 5) << 2
    assert result.memory["or"] == 12 | 5
    assert result.memory["xor"] == 12 ^ 5
    assert result.memory["not"] == ~5
    assert result.memory["shr"] == 128 >> 3


def test_shift_negative_amount_raises() -> None:
    computer = EchoComputer()
    computer.load(
        """
        LOAD A 1
        SHL A -1
        HALT
        """
    )

    with pytest.raises(RuntimeError):
        computer.run()

