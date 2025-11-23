import math

import pytest

from src.parallax_storyweaver import (
    ParallaxStoryWeaver,
    ParallaxThread,
    ParallaxWindow,
    demo,
)


def test_compose_creates_sorted_beats_and_metrics():
    threads = (
        ParallaxThread(name="alpha", events=("aurora lace", "signal bloom")),
        ParallaxThread(name="beta", events=("tidal chord", "ember stair")),
    )
    window = ParallaxWindow(tempo=0.8, offset=1, jitter=0.0, phase=math.pi / 3)
    story = ParallaxStoryWeaver(threads, window=window, seed=3).compose()

    assert story.metrics["beats"] == 4
    assert story.metrics["resonance_mean"] > 0
    assert story.metrics["novelty_mean"] >= 0
    assert story.metrics["interference"] >= 0
    assert story.beats == tuple(sorted(story.beats, key=lambda beat: beat.timestamp))


def test_novelty_respects_unique_tokens_only():
    threads = (
        ParallaxThread(name="gamma", events=("shared motif",)),
        ParallaxThread(name="delta", events=("shared motif", "rare shard")),
    )
    weaver = ParallaxStoryWeaver(threads, seed=9)
    story = weaver.compose()

    novelties = {beat.line: beat.novelty for beat in story.beats}
    assert novelties["rare shard"] > novelties["shared motif"]


def test_demo_narrative_is_deterministic():
    narrative_first = demo()
    narrative_second = demo()
    assert narrative_first == narrative_second
    assert "world-first parallax synthesis" in narrative_first.lower()
