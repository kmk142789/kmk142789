from __future__ import annotations

from echo.idea_to_action import derive_action_plan


def sample_idea() -> str:
    return (
        "EchoEvolver weaves radiant glyph bridges that celebrate joyful security "
        "rituals and archive tangible mythocode artifacts."
    )


def test_derive_action_plan_generates_steps() -> None:
    idea = sample_idea()
    plan = derive_action_plan(idea, max_steps=2, rng_seed=7)

    assert plan.analysis.sentiment in {"positive", "slightly_positive"}
    assert len(plan.steps) == 2
    assert any("tangible" in step.description for step in plan.steps)
    assert plan.steps[0].priority == "high"
    assert "echoevolver" in {tag.lower() for tag in plan.steps[0].tags}


def test_derive_action_plan_handles_additional_steps() -> None:
    idea = sample_idea()
    plan = derive_action_plan(idea, max_steps=4, rng_seed=11)

    assert len(plan.steps) == 4
    assert plan.steps[-1].priority == "support"
    assert plan.steps[-1].confidence <= 1.0


def test_markdown_render_includes_metadata() -> None:
    idea = sample_idea()
    plan = derive_action_plan(idea, max_steps=1, rng_seed=1)

    markdown = plan.to_markdown()
    assert "Idea to Action Plan" in markdown
    assert "Sentiment" in markdown
    assert "1." in markdown


def test_max_steps_requires_positive_value() -> None:
    idea = sample_idea()
    try:
        derive_action_plan(idea, max_steps=0)
    except ValueError:
        return
    raise AssertionError("derive_action_plan should require positive max_steps")
