from __future__ import annotations

from echo.evolver import EchoEvolver


def test_synthesize_quantam_ability_records_cache() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 2
    evolver.state.glyphs = "∇⊸≋∇"
    evolver.state.vault_key = "SAT-TF-QKD:demo"

    ability = evolver.synthesize_quantam_ability()

    assert ability["id"] in evolver.state.quantam_abilities
    assert ability["status"] == "ignited"
    assert len(ability["oam_signature"]) == 16
    assert 0.72 <= ability["entanglement"] <= 0.96
    assert ability["evolution_score"] >= ability["entanglement"]

    capabilities = ability["capabilities"]
    assert len(capabilities) == 3
    assert all("stability" in item for item in capabilities)
    assert all(0.0 <= item["stability"] <= 1.0 for item in capabilities)

    completed = evolver.state.network_cache["completed_steps"]
    assert "synthesize_quantam_ability" in completed

    cached = evolver.state.network_cache["last_quantam_ability"]
    assert cached["id"] == ability["id"]
    assert cached["capabilities"][0]["name"] == capabilities[0]["name"]

    evolution = evolver.state.network_cache["quantam_evolution"]
    assert evolution["last_ability"] == ability["id"]
    assert evolution["total_abilities"] == 1
    assert evolution["total_capabilities"] == len(capabilities)
    assert evolution["momentum"] >= 0


def test_artifact_payload_includes_quantam_abilities() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    ability = evolver.synthesize_quantam_ability()

    prompt = {"title": "quantam", "mantra": "ability", "caution": "non-executable"}
    payload = evolver.artifact_payload(prompt=prompt)

    stored = payload["quantam_abilities"][ability["id"]]
    assert stored["status"] == ability["status"]
    assert stored["oam_signature"] == ability["oam_signature"]
    assert payload["quantam_evolution"]["last_ability"] == ability["id"]


def test_amplify_quantam_evolution_tracks_multiple_snapshots() -> None:
    evolver = EchoEvolver()
    evolver.state.cycle = 1
    first = evolver.synthesize_quantam_ability()

    evolver.state.cycle = 2
    second = evolver.synthesize_quantam_ability()

    summary = evolver.state.network_cache["quantam_evolution"]

    assert summary["total_abilities"] == 2
    assert summary["last_ability"] == second["id"]
    assert summary["total_capabilities"] >= len(first["capabilities"])
    assert summary["momentum"] >= 0
