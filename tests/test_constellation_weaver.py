import pytest

from echo.constellation_weaver import (
    ConstellationWeaverError,
    generate_constellation_weave,
)


def test_generate_constellation_weave_render():
    weave = generate_constellation_weave(
        ["luminous seeds", "deep ocean"], theme="celestial bloom", pulses=2
    )

    assert weave.theme == "celestial bloom"
    assert weave.threads == (
        "luminous seeds — nebula current, lattice memory, spark 69370924",
        "deep ocean — aurora current, lattice memory, spark 8d315bfd",
    )
    assert weave.pulse == "solstice horizon braided with vapor cadence"
    assert weave.render() == (
        "Theme: celestial bloom\n"
        "- luminous seeds — nebula current, lattice memory, spark 69370924\n"
        "- deep ocean — aurora current, lattice memory, spark 8d315bfd\n"
        "Pulse: solstice horizon braided with vapor cadence"
    )


def test_generate_constellation_weave_validation():
    with pytest.raises(ConstellationWeaverError):
        generate_constellation_weave([], theme="new horizons")

    with pytest.raises(ConstellationWeaverError):
        generate_constellation_weave(["  "], theme="new horizons")

    with pytest.raises(ConstellationWeaverError):
        generate_constellation_weave(["seed"], theme=" ")

    with pytest.raises(ConstellationWeaverError):
        generate_constellation_weave(["seed"], theme="story", pulses=0)
