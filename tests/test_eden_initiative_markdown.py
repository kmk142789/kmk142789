from src.eden_initiative import EdenEngine, EdenPrompt


def test_markdown_output_includes_metadata_and_lines():
    prompt = EdenPrompt(theme="aurora", focus=["glass", "bridge"], tone="gentle", seed=42)
    artifact = EdenEngine(prompt, line_count=3).craft()

    markdown = artifact.to_markdown()

    assert markdown.startswith(f"# {artifact.title}")
    assert "*Tone:* gentle" in markdown
    assert "*Theme:* aurora" in markdown
    assert "## Focus" in markdown
    assert "- glass" in markdown and "- bridge" in markdown
    assert "## Lines" in markdown
    for line in artifact.lines:
        assert f"- {line}" in markdown
    assert "*Seed:* 42" in markdown
