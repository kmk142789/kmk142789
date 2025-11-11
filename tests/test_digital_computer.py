"""Tests for the Echo digital computer sandbox."""

from __future__ import annotations

import pytest

from echo.digital_computer import (
    AssemblyError,
    AdvancementCycle,
    AssistantSuggestion,
    EchoComputer,
    EchoComputerAssistant,
    EvolutionCycle,
    assemble_program,
    advance_program,
    evolve_program,
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


def test_min_max_and_sign_helpers() -> None:
    program = """
    LOAD A 10
    MIN A 7
    STORE A @min
    LOAD B -5
    ABS B
    STORE B @abs
    LOAD C 3
    NEG C
    STORE C @neg
    LOAD D 4
    MAX D @min
    STORE D @max
    HALT
    """

    result = run_program(program)

    assert result.memory["min"] == 7
    assert result.memory["abs"] == 5
    assert result.memory["neg"] == -3
    assert result.memory["max"] == 7


def test_comparison_jumps_enable_rich_branching() -> None:
    program = """
    LOAD A 3
    LOAD B 5
    JLT A B lt
    HALT
    lt:
        SET @lt 1
        JGT B A greater
        HALT
    greater:
        SET @gt 1
        JLE A B le
        HALT
    le:
        SET @le 1
        JGE B A ge
        HALT
    ge:
        SET @ge 1
        JNE A B noteq
        HALT
    noteq:
        SET @ne 1
        LOAD C "echo"
        JEQ C "echo" eq
        HALT
    eq:
        SET @eq 1
        HALT
    """

    result = run_program(program)

    assert result.memory["lt"] == 1
    assert result.memory["gt"] == 1
    assert result.memory["le"] == 1
    assert result.memory["ge"] == 1
    assert result.memory["ne"] == 1
    assert result.memory["eq"] == 1


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


def test_evolve_program_generates_cycle_reports() -> None:
    program = """
    LOAD A ?value
    STORE A @result
    PRINT @result
    HALT
    """

    cycles = evolve_program(
        program,
        input_series=[{"value": 2}, {"value": 7}],
    )

    assert [cycle.cycle for cycle in cycles] == [1, 2]
    assert all(isinstance(cycle, EvolutionCycle) for cycle in cycles)
    assert [cycle.result.memory["result"] for cycle in cycles] == [2, 7]
    assert cycles[1].result.output == ("7",)
    assert cycles[0].inputs["value"] == 2


def test_run_persist_state_preserves_registers() -> None:
    computer = EchoComputer()
    computer.load(
        """
        INC A
        HALT
        """
    )

    first = computer.run(persist_state=True)
    assert first.registers["A"] == 1

    second = computer.run(persist_state=True)
    assert second.registers["A"] == 2

    reset = computer.run()
    assert reset.registers["A"] == 1


def test_advance_program_preserves_state_between_cycles() -> None:
    program = """
    LOAD B ?delta
    ADD A B
    STORE A @total
    PRINT A
    HALT
    """

    cycles = advance_program(
        program,
        input_series=[{"delta": 1}, {"delta": 3}, {"delta": -2}],
    )

    assert all(isinstance(cycle, AdvancementCycle) for cycle in cycles)
    assert [cycle.before_registers["A"] for cycle in cycles] == [0, 1, 4]
    assert [cycle.result.registers["A"] for cycle in cycles] == [1, 4, 2]
    assert [cycle.result.memory["total"] for cycle in cycles] == [1, 4, 2]
    assert [cycle.before_memory.get("total", 0) for cycle in cycles] == [0, 1, 4]


def test_assistant_offers_clamp_template() -> None:
    assistant = EchoComputerAssistant()

    suggestion = assistant.suggest("please clamp the value")

    assert isinstance(suggestion, AssistantSuggestion)
    assert suggestion.metadata["template"] == "clamp"

    result = assistant.execute(
        suggestion,
        inputs={"value": 15, "low": 2, "high": 10},
    )

    assert result.output == ("10",)


def test_run_permits_per_call_max_steps_override() -> None:
    computer = EchoComputer(max_steps=3)
    computer.load(
        """
        LOAD A 0
        INC A
        INC A
        INC A
        INC A
        HALT
        """
    )

    with pytest.raises(RuntimeError):
        computer.run()

    result = computer.run(max_steps=8)

    assert result.halted is True
    assert result.registers["A"] == 4
    assert result.steps == 6


def test_run_program_accepts_max_steps_override() -> None:
    program = """
    LOAD A 0
    INC A
    INC A
    INC A
    INC A
    HALT
    """

    with pytest.raises(RuntimeError):
        run_program(program, max_steps=4)

    result = run_program(program, max_steps=8)

    assert result.steps == 6
    assert result.registers["A"] == 4


def test_assistant_generates_factorial_program() -> None:
    assistant = EchoComputerAssistant()
    suggestion = assistant.suggest("Please craft a factorial helper for me")

    assert isinstance(suggestion, AssistantSuggestion)
    assert "factorial" in suggestion.description.lower()
    assert "MUL A B" in suggestion.program

    result = assistant.execute(suggestion, inputs={"n": 5})

    assert result.output == ("120",)
    assert result.memory["result"] == 120


def test_assistant_fallback_echo_and_missing_inputs() -> None:
    assistant = EchoComputerAssistant()
    suggestion = assistant.suggest("say hello back")

    assert suggestion.required_inputs == ("value",)

    with pytest.raises(KeyError):
        assistant.execute(suggestion)

    result = assistant.execute(suggestion, inputs={"value": "hi"})

    assert result.output == ("hi",)


def test_assistant_max_pair_template() -> None:
    assistant = EchoComputerAssistant()
    suggestion = assistant.suggest("what is the max between two values?")

    assert suggestion.metadata["template"] == "max_pair"
    assert "JGE" in suggestion.program

    result = assistant.execute(suggestion, inputs={"left": 7, "right": 3})

    assert result.output == ("7",)


def test_stack_push_pop_round_trip() -> None:
    program = """
    LOAD A 1
    LOAD B 2
    PUSH A
    PUSH B
    LOAD A 0
    LOAD B 0
    POP B
    POP A
    HALT
    """

    result = run_program(program)

    assert result.registers["A"] == 1
    assert result.registers["B"] == 2


def test_pop_from_empty_stack_raises() -> None:
    computer = EchoComputer()
    computer.load(
        """
        POP A
        HALT
        """
    )

    with pytest.raises(RuntimeError):
        computer.run()


def test_call_and_ret_support_subroutines() -> None:
    program = """
    LOAD A 2
    LOAD B 3
    CALL add
    PRINT A
    HALT
    add:
        PUSH B
        ADD A B
        POP B
        RET
    """

    result = run_program(program)

    assert result.output == ("5",)
    assert result.registers["B"] == 3


def test_ret_without_call_stack_raises() -> None:
    computer = EchoComputer()
    computer.load(
        """
        RET
        HALT
        """
    )

    with pytest.raises(RuntimeError):
        computer.run()

