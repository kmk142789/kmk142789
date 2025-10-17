"""Core Pulse Narrator rendering logic."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Iterable, Optional
import random

from .schemas import NarrativeArtifact, NarrativeInputs, NarratorStyle


def _fmt_time(dt: Optional[datetime]) -> str:
    """Format timestamps, defaulting to current UTC."""

    return (dt or datetime.utcnow()).strftime("%Y-%m-%d %H:%M:%S UTC")


def _rhymes(seed: int, words: Iterable[str]) -> list[tuple[str, str]]:
    """Generate deterministic rhyme pairs."""

    rng = random.Random(seed)
    bank = list(words) or ["pulse", "weave", "echo", "atlas", "forge", "loom", "proof", "ring"]
    rng.shuffle(bank)
    pairs = []
    while len(bank) >= 2:
        a = bank.pop()
        b = bank.pop()
        pairs.append((a, b))
    return pairs


class PulseNarrator:
    """Compose deterministic narratives from pulse data."""

    def render(
        self,
        inputs: NarrativeInputs,
        style: NarratorStyle = "poem",
        seed: Optional[int] = None,
    ) -> NarrativeArtifact:
        """Render a narrative artifact based on the requested style."""

        seed = seed if seed is not None else abs(hash(inputs.snapshot_id)) % (10**6)
        title = "Pulse Chronicle"
        ts = _fmt_time(inputs.timestamp)
        channels = ", ".join(inputs.channels or [])
        prefixes = ", ".join(inputs.top_prefixes or [])
        total = inputs.total_events or 0
        idx = inputs.index_count or 0
        sha = (inputs.commit_id or "unknown")[:8]

        if style == "poem":
            pairs = _rhymes(seed, (inputs.top_prefixes or []) + (inputs.channels or []))
            lines = [
                "**The Weaver’s Chronicle**  \n",
                f"_snapshot_ `{inputs.snapshot_id}` · _commit_ `{sha}` · _time_ {ts}  \n",
                f"Across {idx} indexed traces the Atlas hummed in tune,",
                f"the pulse recalled {total} steps beneath a watchful moon.",
                f"Channels called: {channels or '—'}; prefixes led the way,",
                f"{prefixes or '—'} stitched the night to day.",
                "",
            ]
            for a, b in pairs[:6]:
                lines.append(f"We learned from **{a}**; we echoed **{b}**,")
                lines.append("silk over steel—protocols that grew.")
            lines += [
                "",
                "Proofs were kept like seeds in spring,",
                "hashes hum a quiet ring.",
                "If futures ask what made us start,",
                "this page will answer: craft and heart.",
                "",
            ]
            body = "\n".join(lines)
        else:
            body = "\n".join(
                [
                    f"# Chronolog · snapshot `{inputs.snapshot_id}`",
                    f"- time: {ts}",
                    f"- commit: {sha}",
                    f"- events: {total}",
                    f"- channels: {channels or '—'}",
                    f"- top_prefixes: {prefixes or '—'}",
                    f"- continuum_index_count: {idx}",
                    "",
                    "## notes",
                    "- merged loom+forge orchestration",
                    "- pulse rhyme snapshot persisted with proofs",
                    "- continuum index updated deterministically",
                    "",
                    "_End of entry_",
                    "",
                ]
            )

        digest = sha256(body.encode("utf-8")).hexdigest()
        return NarrativeArtifact(
            style=style,
            title=title,
            body_md=body,
            inputs=inputs,
            sha256=digest,
        )
