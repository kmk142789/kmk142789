import json

import pytest

from scripts import resonant_story as rs


def test_build_story_json_format_round_trip():
    output = rs.build_story("orbital solidarity", 2, seed=7, format="json")
    payload = json.loads(output)
    assert payload["theme"] == "orbital solidarity"
    assert len(payload["beats"]) == 2
    assert all({"focus", "tone", "action"} <= beat.keys() for beat in payload["beats"])


def test_build_story_rejects_unknown_format():
    with pytest.raises(ValueError):
        rs.build_story("tidal recursion", 1, format="xml")


def test_build_story_rejects_unknown_vibe():
    with pytest.raises(ValueError):
        rs.build_story("tidal recursion", 1, vibe="metallic")


def test_build_story_payload_respects_width():
    payload = rs.build_story_payload("tidal recursion", 1, seed=11, width=40)
    for paragraph in payload["paragraphs"]:
        assert all(len(line) <= 40 for line in paragraph.splitlines())


def test_outline_format_presents_beats_and_sections():
    output = rs.build_story(
        "orbital solidarity", 2, seed=4, format="outline", vibe="bright"
    )

    assert "Theme: orbital solidarity" in output
    assert output.count("-") >= 2
    assert "Closing:" in output


def test_vibe_palette_changes_vocabulary():
    payload_default = rs.build_story_payload(
        "orbital solidarity", 1, seed=7, vibe="default"
    )
    payload_shadow = rs.build_story_payload(
        "orbital solidarity", 1, seed=7, vibe="shadow"
    )

    default_focus = payload_default["beats"][0]["focus"]
    shadow_focus = payload_shadow["beats"][0]["focus"]

    assert default_focus != shadow_focus
    assert payload_shadow["vibe"] == "shadow"


def test_markdown_format_includes_title_and_beats():
    output = rs.build_story(
        "orbital solidarity",
        3,
        seed=5,
        title="Orbit Log",
        format="markdown",
    )

    assert output.startswith("# Orbit Log")
    assert "_Theme: orbital solidarity_" in output
    assert output.count("- ") == 3


def test_build_story_payload_sets_default_title():
    payload = rs.build_story_payload("tidal recursion", 2, seed=3)
    assert payload["title"] == "Resonant story about tidal recursion"
