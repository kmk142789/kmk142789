from datetime import datetime, timedelta, timezone

from pulse_weaver.glyphs import GlyphDefinition, GlyphRotationScheduler


def test_scheduler_rotates_through_catalog() -> None:
    catalog = (
        GlyphDefinition("∇", "Source", "Ground"),
        GlyphDefinition("⊸", "Bridge", "Connect"),
    )
    scheduler = GlyphRotationScheduler(catalog=catalog, cadence_hours=24)
    day_one = datetime(2025, 1, 1, 12, tzinfo=timezone.utc)
    day_two = day_one + timedelta(days=1)

    rotation_one = scheduler.current(now=day_one)
    rotation_two = scheduler.current(now=day_two)

    assert {rotation_one.glyph, rotation_two.glyph} == {"∇", "⊸"}
    assert rotation_one.window_start == datetime(2025, 1, 1, tzinfo=timezone.utc)
    assert rotation_one.window_end == datetime(2025, 1, 2, tzinfo=timezone.utc)
    assert rotation_one.energy != rotation_two.energy


def test_scheduler_preview_returns_sequential_windows() -> None:
    scheduler = GlyphRotationScheduler(cadence_hours=12)
    start = datetime(2025, 2, 1, 5, tzinfo=timezone.utc)
    preview = scheduler.preview(count=3, start=start)

    assert len(preview) == 3
    for idx in range(1, len(preview)):
        assert preview[idx].window_start == preview[idx - 1].window_start + timedelta(hours=12)
        assert preview[idx].cycle != preview[idx - 1].cycle
    serialized = preview[0].to_dict()
    assert serialized["glyph"]
    assert "start" in serialized["window"]
    assert "end" in serialized["window"]
