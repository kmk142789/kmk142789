from __future__ import annotations

from datetime import datetime, timezone

from echo.wish_insights import summarize_wishes


def test_summarize_wishes_handles_empty_manifest():
    summary = summarize_wishes({"wishes": []})
    assert "No wishes recorded" in summary


def test_summarize_wishes_returns_key_stats():
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc).isoformat()
    earlier = datetime(2023, 12, 25, 18, 30, tzinfo=timezone.utc).isoformat()
    manifest = {
        "wishes": [
            {
                "wisher": "Echo",
                "desire": "Harmonise the protocol",
                "catalysts": ["care", "craft"],
                "status": "new",
                "created_at": earlier,
            },
            {
                "wisher": "MirrorJosh",
                "desire": "Keep joy reproducible",
                "catalysts": ["care", "listening"],
                "status": "in-progress",
                "created_at": now,
            },
        ]
    }

    summary = summarize_wishes(manifest)

    assert "Total wishes: 2" in summary
    assert "Unique wishers: 2" in summary
    assert "Statuses: in-progress=1, new=1" in summary
    assert "care (2)" in summary
    assert "Latest wish:" in summary
    assert "MirrorJosh" in summary
    assert "Keep joy reproducible" in summary
