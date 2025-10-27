"""Tools for distilling "enlightenment" style insights from text.

The Echo codebase contains many creative generators that output glyphs,
chronicles, and mythogenic prose.  For day-to-day work it is also helpful to
have a lightweight, testable component that can surface the most uplifting or
illuminating fragments from a larger body of text.  The utilities in this module
focus on simple heuristics so that they remain dependency-free and easy to use
inside scripts, notebooks, or CLI commands.

The core of the module is :class:`EnlightenmentEngine`, which accepts one or
more passages and produces a ranked list of :class:`EnlightenmentInsight`
instances.  Each insight records the original sentence, the normalized
"enlightenment score", and the list of keywords that contributed to that score.
The scoring logic blends keyword coverage, sentence clarity, and novelty so that
the results feel balanced instead of simply highlighting every sentence that
contains a positive word.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable, List, Sequence

_DEFAULT_KEYWORDS = {
    "enlightenment",
    "clarity",
    "illumination",
    "insight",
    "wisdom",
    "wonder",
    "grace",
    "kindness",
    "gratitude",
    "empathy",
    "harmony",
    "balance",
    "joy",
    "peace",
}

_WORD_RE = re.compile(r"[\w']+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(slots=True)
class EnlightenmentInsight:
    """Represents a distilled insight extracted from source text."""

    sentence: str
    score: float
    keywords: List[str]
    clarity: float

    def as_dict(self) -> dict:
        """Return a JSON-serialisable representation of the insight."""

        return {
            "sentence": self.sentence,
            "score": self.score,
            "keywords": list(self.keywords),
            "clarity": self.clarity,
        }


class EnlightenmentEngine:
    """Rank enlightening sentences from one or more passages.

    Parameters
    ----------
    keywords:
        Optional sequence of keywords that should boost sentences.  When not
        provided a curated default set emphasising positive, reflective concepts
        is used.
    minimum_length:
        Sentences shorter than this value (measured in characters) are treated as
        low-confidence hints.  They can still surface if they have exceptional
        keyword coverage but their score is gently reduced.
    """

    def __init__(
        self,
        *,
        keywords: Sequence[str] | None = None,
        minimum_length: int = 20,
    ) -> None:
        if minimum_length < 0:
            raise ValueError("minimum_length must be non-negative")

        self.minimum_length = minimum_length
        base_keywords = _DEFAULT_KEYWORDS if keywords is None else keywords
        # Normalise keywords for case-insensitive matching while preserving order
        # for reproducibility when the caller supplies a sequence.
        self.keywords = [kw.strip().lower() for kw in base_keywords if kw.strip()]
        self.keyword_set = set(self.keywords)

    def analyze(
        self,
        passages: Iterable[str],
        *,
        top_k: int = 3,
    ) -> List[EnlightenmentInsight]:
        """Return the ``top_k`` enlightening sentences from ``passages``.

        The passages can be strings, paragraphs, or already separated sentences.
        Empty inputs yield an empty list.  The ``top_k`` argument must be a
        positive integer; requesting zero or fewer results raises a
        ``ValueError`` because it likely indicates a configuration issue.
        """

        if top_k <= 0:
            raise ValueError("top_k must be greater than zero")

        sentences = self._collect_sentences(passages)
        if not sentences:
            return []

        scored = [self._score_sentence(sentence) for sentence in sentences]
        scored.sort(key=lambda item: (-item.score, -item.clarity, item.sentence))
        return scored[: min(top_k, len(scored))]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_sentences(self, passages: Iterable[str]) -> List[str]:
        sentences: List[str] = []
        for passage in passages:
            if not passage:
                continue
            chunks = _SENTENCE_RE.split(passage.strip())
            for chunk in chunks:
                sentence = chunk.strip()
                if sentence:
                    sentences.append(sentence)
        return sentences

    def _score_sentence(self, sentence: str) -> EnlightenmentInsight:
        tokens = _WORD_RE.findall(sentence.lower())
        if not tokens:
            return EnlightenmentInsight(sentence=sentence, score=0.0, keywords=[], clarity=0.0)

        unique_tokens = set(tokens)
        matched_keywords = sorted(self.keyword_set.intersection(unique_tokens))

        keyword_score = len(matched_keywords) / max(1, len(self.keyword_set))
        clarity = self._clarity_score(tokens)

        # Encourage sentences that introduce new concepts in addition to keyword
        # hits by considering the ratio of unique tokens to total tokens.
        novelty = len(unique_tokens) / len(tokens)

        raw_score = keyword_score * 0.6 + clarity * 0.25 + novelty * 0.15

        if len(sentence) < self.minimum_length:
            raw_score *= 0.75

        return EnlightenmentInsight(
            sentence=sentence,
            score=round(raw_score, 4),
            keywords=matched_keywords,
            clarity=round(clarity, 4),
        )

    def _clarity_score(self, tokens: Sequence[str]) -> float:
        # Clarity loosely measures how evenly the words distribute.  Highly
        # repetitive sentences are down-weighted, while those with a balanced
        # vocabulary trend upward.
        token_count = len(tokens)
        if token_count == 0:
            return 0.0

        unique_count = len(set(tokens))
        repetition_ratio = 1 - (unique_count / token_count)
        # Map repetition into a score between 0 and 1, where lower repetition is
        # better.  ``math.exp`` keeps the curve smooth without needing numpy.
        clarity = math.exp(-3 * repetition_ratio)
        return min(1.0, max(0.0, clarity))


__all__ = ["EnlightenmentEngine", "EnlightenmentInsight"]

