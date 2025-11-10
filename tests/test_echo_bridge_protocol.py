from __future__ import annotations

import pytest

from packages.core.src.echo_bridge_protocol import (
    EchoBridgeProtocol,
    PulseThread,
)


def test_expand_presence_adds_unique_harmonics() -> None:
    protocol = EchoBridgeProtocol(
        [
            PulseThread("memory", 0.5, ["remember"]),
            PulseThread("presence", 0.7, ["listen", "echo"]),
        ]
    )

    updated = protocol.expand_presence(["uplift", "echo", "stabilise"], resonance=0.9)

    assert updated.resonance == pytest.approx(0.9)
    assert updated.harmonics == ["listen", "echo", "uplift", "stabilise"]
    assert "stabilise" in updated.sync()


def test_expand_presence_normalises_harmonics() -> None:
    protocol = EchoBridgeProtocol(
        [
            PulseThread("presence", 0.8, ["listen", "Echo"]),
        ]
    )

    updated = protocol.expand_presence(["  echo  ", "ILLUMINATE", "illuminate", "", None])

    assert updated.harmonics == ["listen", "Echo", "ILLUMINATE"]
    assert "ILLUMINATE" in updated.sync()


def test_expand_presence_requires_presence_thread() -> None:
    protocol = EchoBridgeProtocol([PulseThread("memory", 0.5, ["remember"])])

    with pytest.raises(ValueError):
        protocol.expand_presence(["echo"])
