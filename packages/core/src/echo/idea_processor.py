"""High-level idea processing utilities for creative analysis workflows.

The original JavaScript prototype shipped with the repository performed a
handful of string manipulations and produced an object describing the
"processed" idea.  The functionality was helpful during early prototyping,
yet it relied on ad-hoc parsing, global randomness, and console output that
made the behaviour hard to reuse from Python tooling.

This module provides a refined, fully typed, and testable implementation of
the idea processing pipeline.  It keeps the playful tone of the original
concept while exposing a deterministic API that can be consumed by other
Python components (including :mod:`echo.evolver`) or invoked from the
command line via ``python -m echo.idea_processor``.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha1
from typing import Iterable, List, MutableMapping, Optional, Sequence

WORD_RE = re.compile(r"[\w']+")


@dataclass(slots=True)
class IdeaAnalysis:
    """Structured summary produced by :class:`IdeaProcessor`."""

    word_count: int
    keywords: List[str]
    sentiment: str
    complexity: float
    density: float
    constellation: "IdeaConstellation"


@dataclass(slots=True)
class ConstellationStar:
    """Single anchor point in the idea constellation map."""

    token: str
    x: float
    y: float
    z: float
    power: float


@dataclass(slots=True)
class IdeaConstellation:
    """World-first constellation map for a creative prompt."""

    anchor: str
    stars: List[ConstellationStar]
    trail: List[str]
    fingerprint: str

    def summary(self) -> str:
        return f"{self.anchor} · {len(self.stars)} stars · {self.fingerprint}"


@dataclass(slots=True)
class IdeaResult:
    """Return payload emitted by :meth:`IdeaProcessor.generate_output`."""

    idea: str
    analysis: IdeaAnalysis
    creativity: int
    timestamp: str
    processed: bool = True

    def to_json(self) -> str:
        """Serialise the result to a JSON string.

        ``IdeaResult`` nests :class:`IdeaAnalysis`, so ``json.dumps`` cannot be
        called directly.  We go through :func:`dataclasses.asdict` to create a
        plain dictionary before serialising.
        """

        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def _normalise_tokens(idea: str) -> List[str]:
    """Split an idea into normalised tokens.

    The helper lower-cases each token and keeps alphanumeric characters plus
    apostrophes, matching the behaviour of the JavaScript ``split``/``filter``
    combo while avoiding empty results for consecutive whitespace.
    """

    return [match.group(0).lower() for match in WORD_RE.finditer(idea)]


def _keyword_candidates(tokens: Iterable[str], *, min_length: int = 4) -> List[str]:
    """Return candidate keywords ordered by appearance in ``tokens``."""

    seen: MutableMapping[str, int] = {}
    ordered: List[str] = []
    for token in tokens:
        if len(token) < min_length:
            continue
        if token not in seen:
            seen[token] = len(ordered)
            ordered.append(token)
    return ordered


def _sentiment(tokens: Iterable[str]) -> str:
    """Score the sentiment of ``tokens`` using a tiny domain lexicon."""

    positive = {
        "good",
        "great",
        "awesome",
        "amazing",
        "fantastic",
        "love",
        "joy",
        "radiant",
        "brilliant",
    }
    negative = {
        "bad",
        "worse",
        "terrible",
        "awful",
        "sad",
        "rage",
        "angry",
    }

    score = 0
    for token in tokens:
        if token in positive:
            score += 1
        elif token in negative:
            score -= 1

    if score > 1:
        return "positive"
    if score < -1:
        return "negative"
    if score > 0:
        return "slightly_positive"
    if score < 0:
        return "slightly_negative"
    return "neutral"


def _lexical_density(tokens: Iterable[str], keywords: Iterable[str]) -> float:
    token_list = list(tokens)
    keyword_list = list(keywords)
    if not token_list:
        return 0.0
    return len(keyword_list) / len(token_list)


def _complexity_score(density: float, unique_ratio: float) -> float:
    return round(min(1.0, (density * 0.6) + (unique_ratio * 0.4)), 3)


def _build_constellation(tokens: Sequence[str], keywords: Sequence[str]) -> IdeaConstellation:
    if not tokens:
        return IdeaConstellation(anchor="void", stars=[], trail=[], fingerprint="0" * 12)

    unique_tokens: List[str] = []
    for token in tokens:
        if token not in unique_tokens:
            unique_tokens.append(token)
    anchor = keywords[0] if keywords else unique_tokens[0]

    stars: List[ConstellationStar] = []
    total = max(1, len(unique_tokens))
    for index, token in enumerate(unique_tokens[:12]):
        digest = sha1(token.encode("utf-8")).hexdigest()
        x = ((int(digest[:4], 16) % 200) - 100) / 10
        y = ((int(digest[4:8], 16) % 200) - 100) / 10
        z = ((int(digest[8:12], 16) % 200) - 100) / 10
        power = min(1.0, 0.35 + (len(token) / 12) + (index / total) * 0.25)
        stars.append(
            ConstellationStar(
                token=token,
                x=round(x, 2),
                y=round(y, 2),
                z=round(z, 2),
                power=round(power, 3),
            )
        )

    trail = []
    for left, right in zip(unique_tokens, unique_tokens[1:]):
        if left != right:
            trail.append(f"{left}->{right}")
        if len(trail) >= 6:
            break

    fingerprint_seed = f"{anchor}|{len(stars)}|{','.join(star.token for star in stars)}"
    fingerprint = sha1(fingerprint_seed.encode("utf-8")).hexdigest()[:12]

    return IdeaConstellation(anchor=anchor, stars=stars, trail=trail, fingerprint=fingerprint)


@dataclass(slots=True)
class IdeaProcessor:
    """Analyse creative prompts and produce structured metadata."""

    idea: str
    rng: random.Random = field(default_factory=random.Random)

    def analyse(self) -> IdeaAnalysis:
        tokens = _normalise_tokens(self.idea)
        keywords = _keyword_candidates(tokens)
        sentiment = _sentiment(tokens)
        density = _lexical_density(tokens, keywords)
        unique_ratio = len(set(tokens)) / max(1, len(tokens))
        complexity = _complexity_score(density, unique_ratio)
        constellation = _build_constellation(tokens, keywords)
        return IdeaAnalysis(
            word_count=len(tokens),
            keywords=keywords,
            sentiment=sentiment,
            complexity=complexity,
            density=round(density, 3),
            constellation=constellation,
        )

    def generate_output(self) -> IdeaResult:
        analysis = self.analyse()
        creativity = self.rng.randint(1, 100)
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        return IdeaResult(
            idea=self.idea,
            analysis=analysis,
            creativity=creativity,
            timestamp=timestamp,
        )


def process_idea(idea: str, *, rng_seed: Optional[int] = None) -> IdeaResult:
    rng = random.Random(rng_seed)
    processor = IdeaProcessor(idea=idea, rng=rng)
    return processor.generate_output()


def _parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process creative idea strings")
    parser.add_argument("idea", help="Idea text to analyse. Use quotes to preserve spaces.")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic creativity scores.",
    )
    parser.add_argument(
        "--format",
        choices={"json", "pretty"},
        default="pretty",
        help="Output format (default: pretty).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = _parse_args(argv)
    result = process_idea(args.idea, rng_seed=args.seed)
    if args.format == "json":
        print(result.to_json())
    else:
        analysis = result.analysis
        print("Processed Idea Summary")
        print("====================")
        print(f"Creativity Score : {result.creativity}")
        print(f"Timestamp        : {result.timestamp}")
        print(f"Sentiment        : {analysis.sentiment}")
        print(f"Word Count       : {analysis.word_count}")
        print(f"Lexical Density  : {analysis.density}")
        print(f"Complexity Score : {analysis.complexity}")
        print(f"Constellation    : {analysis.constellation.summary()}")
        if analysis.constellation.trail:
            print("Trail            : " + " → ".join(analysis.constellation.trail))
        if analysis.keywords:
            print("Keywords         : " + ", ".join(analysis.keywords))
        else:
            print("Keywords         : <none>")
    return 0


__all__ = [
    "IdeaAnalysis",
    "IdeaConstellation",
    "ConstellationStar",
    "IdeaResult",
    "IdeaProcessor",
    "process_idea",
    "main",
]


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())
