"""Tests for the deterministic mutation module export helper."""

from echo.evolver import EchoEvolver


def test_mutation_module_reports_empty_state_when_no_snippets():
    evolver = EchoEvolver()

    module = evolver.mutation_module()

    assert "# Auto-generated EchoEvolver mutation module" in module
    assert "# No mutations recorded yet" in module
    assert module.endswith("\n")


def test_mutation_module_contains_sorted_mutations():
    evolver = EchoEvolver()
    evolver.advance_cycle()
    first_snippet = evolver.mutate_code()

    evolver.advance_cycle()
    second_snippet = evolver.mutate_code()

    module = evolver.mutation_module()

    assert "def echo_cycle_1" in module
    assert "def echo_cycle_2" in module
    assert first_snippet.strip() in module
    assert second_snippet.strip() in module

    function_lines = [line for line in module.splitlines() if line.startswith("def echo_cycle")]
    assert function_lines == sorted(function_lines)
    assert module.endswith("\n")
