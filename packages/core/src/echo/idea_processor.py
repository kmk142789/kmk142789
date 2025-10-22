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
from typing import Iterable, List, MutableMapping, Optional

WORD_RE = re.compile(r"[\w']+")


@dataclass(slots=True)
class IdeaAnalysis:
    """Structured summary produced by :class:`IdeaProcessor`."""

    word_count: int
    keywords: List[str]
    sentiment: str
    complexity: float
    density: float


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
        return IdeaAnalysis(
            word_count=len(tokens),
            keywords=keywords,
            sentiment=sentiment,
            complexity=complexity,
            density=round(density, 3),
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
        if analysis.keywords:
            print("Keywords         : " + ", ".join(analysis.keywords))
        else:
            print("Keywords         : <none>")
    return 0


__all__ = [
    "IdeaAnalysis",
    "IdeaResult",
    "IdeaProcessor",
    "process_idea",
    "main",
]


if __name__ == "__main__":  # pragma: no cover - command line entry point
    raise SystemExit(main())

