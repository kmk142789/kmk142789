import pytest

from atlas_runtime import ProcessIsolator, Sandbox


def test_sandbox_respects_limits():
    sandbox = Sandbox()
    program = [("PUSH", 1), ("PUSH", 2), ("ADD", None)]
    result = sandbox.execute(program, memory_limit=128, timeout=1.0)
    assert result.stack == [3]
    assert result.cycles == 3


def test_sandbox_timeout():
    sandbox = Sandbox()
    program = [("PUSH", 1), ("POP", None)] * 1000
    with pytest.raises(TimeoutError):
        sandbox.execute(program, memory_limit=128, timeout=0.0001)


def test_process_isolation():
    isolator = ProcessIsolator()
    program = [("PUSH", 1), ("PUSH", 2), ("ADD", None)]
    result = isolator.run(program, memory_limit=128, timeout=1.0)
    assert result.stack == [3]
