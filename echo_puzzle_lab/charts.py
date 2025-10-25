"""Chart builders shared by the Puzzle Lab CLI and dashboard."""
from __future__ import annotations

from pathlib import Path
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

matplotlib.use("Agg")

CHART_FILENAMES = {
    "family": "puzzle_lab_family",
    "timeline": "puzzle_lab_timeline",
    "ud_pie": "puzzle_lab_ud_coverage",
}


def _prepare_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    data = frame.copy()
    if "Updated" in data.columns:
        data["Updated"] = pd.to_datetime(data["Updated"], utc=True, errors="coerce")
    return data


def build_family_chart(frame: pd.DataFrame) -> plt.Figure:
    data = _prepare_dataframe(frame)
    fig, ax = plt.subplots(figsize=(7, 4))
    if data.empty:
        ax.set_title("Puzzle count by script family")
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        return fig

    counts = data.groupby("Family").size().sort_values(ascending=False)
    counts.plot(kind="bar", color="#4c72b0", ax=ax)
    ax.set_ylabel("Puzzles")
    ax.set_xlabel("Script family")
    ax.set_title("Puzzle count by script family")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    return fig


def build_timeline_chart(frame: pd.DataFrame) -> plt.Figure:
    data = _prepare_dataframe(frame)
    fig, ax = plt.subplots(figsize=(8, 4))
    if data.empty:
        ax.set_title("Puzzle timeline by PR and date")
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        return fig

    timeline = data.dropna(subset=["Updated"]).copy()
    if timeline.empty:
        ax.set_title("Puzzle timeline by PR and date")
        ax.text(0.5, 0.5, "No dated entries", ha="center", va="center")
        return fig

    timeline["Date"] = timeline["Updated"].dt.date
    pivot = (
        timeline.groupby(["Date", "Lineage_PR"])
        .size()
        .unstack(fill_value=0)
        .sort_index()
    )
    pivot.plot.area(ax=ax, alpha=0.7)
    ax.set_ylabel("Puzzles per day")
    ax.set_xlabel("Date")
    ax.set_title("Puzzle timeline by PR and date")
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1))
    fig.tight_layout()
    return fig


def build_ud_pie_chart(frame: pd.DataFrame) -> plt.Figure:
    data = _prepare_dataframe(frame)
    fig, ax = plt.subplots(figsize=(5, 5))
    if data.empty:
        ax.set_title("UD binding coverage")
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        return fig

    bound = int(data["UD_Bound"].sum())
    total = len(data)
    values = [bound, total - bound]
    labels = ["Bound", "Unbound"]
    colors = ["#55a868", "#c44e52"]
    ax.pie(values, labels=labels, colors=colors, autopct="%1.1f%%")
    ax.set_title("UD binding coverage")
    fig.tight_layout()
    return fig


def save_charts(frame: pd.DataFrame, directory: Path) -> dict[str, list[Path]]:
    """Build and persist PNG/SVG chart artefacts for the provided frame."""

    directory.mkdir(parents=True, exist_ok=True)
    charts = {
        "family": build_family_chart(frame),
        "timeline": build_timeline_chart(frame),
        "ud_pie": build_ud_pie_chart(frame),
    }

    outputs: dict[str, list[Path]] = {}
    for key, figure in charts.items():
        outputs[key] = []
        base = directory / CHART_FILENAMES[key]
        for suffix in (".png", ".svg"):
            target = base.with_suffix(suffix)
            figure.savefig(target, bbox_inches="tight")
            outputs[key].append(target)
        plt.close(figure)
    return outputs


__all__ = [
    "CHART_FILENAMES",
    "build_family_chart",
    "build_timeline_chart",
    "build_ud_pie_chart",
    "save_charts",
]
