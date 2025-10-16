import random

from echo.evolver import EchoEvolver, HearthWeave


def test_perfect_the_hearth_uses_finder_and_updates_state():
    evolver = EchoEvolver(rng=random.Random(0))

    palette = {
        "sunlight": "Sunlight threaded through stained glass",
        "coffee_scent": "Cardamom espresso with orange zest",
        "quiet": "Snow-muted city street",
        "warmth": "Quilted radiant floor glow",
        "love": "Signal of forever",
    }

    calls = []

    def finder(key: str) -> str:
        calls.append(key)
        return palette[key]

    hearth = evolver.perfect_the_hearth(finder)

    assert isinstance(hearth, HearthWeave)
    assert calls == ["sunlight", "coffee_scent", "quiet", "warmth", "love"]
    assert hearth.light == palette["sunlight"]
    assert hearth.scent == palette["coffee_scent"]
    assert hearth.sound == palette["quiet"]
    assert hearth.feeling == palette["warmth"]
    assert hearth.love == palette["love"]
    assert evolver.state.hearth_signature == hearth
    assert evolver.state.network_cache["hearth_signature"]["light"] == palette["sunlight"]

    digest = evolver.cycle_digest()
    assert "perfect_the_hearth" in digest["completed_steps"]
    assert any("Hearth refined" in entry for entry in evolver.state.event_log)


def test_perfect_the_hearth_allows_palette_updates_and_fallback():
    evolver = EchoEvolver(rng=random.Random(0))

    updates = {
        "sunlight": "Amber hearthlight",
        "quiet": "Forest hush under gentle snow",
    }

    def finder(key: str):
        if key == "quiet":
            return None
        return f"custom-{key}"

    hearth = evolver.perfect_the_hearth(finder, palette_updates=updates)

    assert hearth.light == "custom-sunlight"
    assert hearth.scent == "custom-coffee_scent"
    assert hearth.sound == updates["quiet"]
    assert hearth.feeling == "custom-warmth"
    assert hearth.love == "custom-love"

    palette_cache = evolver.state.network_cache["hearth_palette"]
    assert palette_cache["sunlight"] == updates["sunlight"]
    assert palette_cache["quiet"] == updates["quiet"]
    assert evolver.state.hearth_signature == hearth
