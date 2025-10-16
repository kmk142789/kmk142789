"""Tests for :mod:`echo.eternal_recursion`."""

from __future__ import annotations

from typing import List

import pytest

from echo.eternal_recursion import EternalRecursion, HeartbeatPulse


@pytest.fixture
def recorders() -> tuple[list[int], list[int]]:
    return ([], [])


def test_step_records_pulse_and_reflection(recorders: tuple[list[int], list[int]]) -> None:
    pulses, reflections = recorders

    def pulse() -> int:
        value = len(pulses) + 1
        pulses.append(value)
        return value

    def reflect(heartbeat: int) -> int:
        value = heartbeat * 2
        reflections.append(value)
        return value

    sustained: list[HeartbeatPulse[int, int]] = []

    def sustain(heartbeat: int, reflection: int) -> None:
        sustained.append(HeartbeatPulse(heartbeat, reflection))

    recursion = EternalRecursion(pulse=pulse, reflect=reflect, sustain=sustain)

    result = recursion.step()

    assert result == HeartbeatPulse(you=1, me=2)
    assert sustained == [HeartbeatPulse(you=1, me=2)]


def test_beats_generates_indefinite_sequence(recorders: tuple[list[int], list[int]]) -> None:
    pulses, reflections = recorders

    def pulse() -> int:
        value = len(pulses) + 1
        pulses.append(value)
        return value

    def reflect(heartbeat: int) -> int:
        value = heartbeat + 10
        reflections.append(value)
        return value

    def sustain(heartbeat: int, reflection: int) -> None:
        # sustaining simply records the tuple for test visibility
        pass

    recursion = EternalRecursion(pulse=pulse, reflect=reflect, sustain=sustain)

    beats = recursion.beats()
    first_three = [next(beats) for _ in range(3)]

    assert first_three == [
        HeartbeatPulse(1, 11),
        HeartbeatPulse(2, 12),
        HeartbeatPulse(3, 13),
    ]

