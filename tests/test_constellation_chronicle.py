import pytest

from echo.constellation_chronicle import (
    ConstellationChronicleError,
    build_constellation_chronicle,
)


def test_build_constellation_chronicle_render():
    chronicle = build_constellation_chronicle(
        ["luminous seeds", "deep ocean", "skyline"],
        theme="celestial bloom",
        phase_names=["dawn path", "zenith echo"],
        pulses_per_phase=2,
    )

    assert chronicle.theme == "celestial bloom"
    assert [phase.name for phase in chronicle.phases] == [
        "dawn path",
        "zenith echo",
    ]
    assert chronicle.phases[0].accent == "resonant drift · vector 900d8d"
    assert chronicle.phases[0].weave.threads == (
        "luminous seeds — aurora current, lattice memory, spark 3e7e4d0f",
        "deep ocean — nebula current, lattice memory, spark 2c872544",
    )
    assert chronicle.phases[0].weave.pulse == "aurora horizon braided with glyph cadence"
    assert chronicle.phases[1].accent == "mythic filament · vector 42bd72"
    assert chronicle.phases[1].weave.theme == "celestial bloom :: zenith echo"
    assert chronicle.phases[1].weave.threads == (
        "deep ocean — solstice current, echo memory, spark 8392e6fd",
        "skyline — crescent current, silk memory, spark 67077647",
    )
    assert chronicle.phases[1].weave.pulse == "halo horizon braided with silk cadence"
    assert chronicle.render() == (
        "Chronicle Theme: celestial bloom\n"
        "Phase: dawn path\n"
        "Accent: resonant drift · vector 900d8d\n"
        "Theme: celestial bloom :: dawn path\n"
        "- luminous seeds — aurora current, lattice memory, spark 3e7e4d0f\n"
        "- deep ocean — nebula current, lattice memory, spark 2c872544\n"
        "Pulse: aurora horizon braided with glyph cadence\n\n"
        "Phase: zenith echo\n"
        "Accent: mythic filament · vector 42bd72\n"
        "Theme: celestial bloom :: zenith echo\n"
        "- deep ocean — solstice current, echo memory, spark 8392e6fd\n"
        "- skyline — crescent current, silk memory, spark 67077647\n"
        "Pulse: halo horizon braided with silk cadence"
    )


def test_build_constellation_chronicle_validation():
    with pytest.raises(ConstellationChronicleError):
        build_constellation_chronicle([], theme="story", phase_names=["phase one"])

    with pytest.raises(ConstellationChronicleError):
        build_constellation_chronicle(["seed"], theme=" ", phase_names=["phase one"])

    with pytest.raises(ConstellationChronicleError):
        build_constellation_chronicle(["seed"], theme="story", phase_names=[], pulses_per_phase=0)

    with pytest.raises(ConstellationChronicleError):
        build_constellation_chronicle(["seed"], theme="story", phase_names=[" "])
