"""Predictive Misconception Mapper (PMM).

The mapper inspects short-form statements and estimates which topics are
most likely to generate misunderstandings.  The implementation favours
repeatable heuristics over statistical models so it stays deterministic
inside constrained environments and unit tests.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

_NEGATION_TERMS = {"never", "no", "not", "nothing", "none"}
_ABSOLUTE_TERMS = {"always", "guaranteed", "impossible", "certain"}
_UNCERTAIN_TERMS = {"maybe", "perhaps", "unclear", "ambiguous", "assume"}


@dataclass(frozen=True)
class MisconceptionHypothesis:
    """Represents a possible misconception tied to a topic."""

    topic: str
    risk_score: float
    triggers: tuple[str, ...]
    mitigation: str


class PredictiveMisconceptionMapper:
    """Derive misconception hypotheses from narrative snippets."""

    def __init__(self, *, base_risk: float = 0.2, amplification: float = 1.4) -> None:
        self.base_risk = max(0.0, base_risk)
        self.amplification = max(1.0, amplification)

    def _tokens(self, text: str) -> set[str]:
        cleaned = text.replace("/", " ")
        return {token.strip(".,;:!?\"'()[]{}<>|\\`).").lower() for token in cleaned.split() if token}

    def _classify_triggers(self, text: str) -> list[str]:
        tokens = self._tokens(text)
        triggers: list[str] = []
        if tokens & _NEGATION_TERMS:
            triggers.append("negation")
        if tokens & _ABSOLUTE_TERMS:
            triggers.append("absolutist")
        if tokens & _UNCERTAIN_TERMS:
            triggers.append("ambiguous")
        if "?" in text:
            triggers.append("question")
        return triggers

    def _mitigation(self, topic: str, triggers: Iterable[str]) -> str:
        categories = sorted(set(triggers))
        if not categories:
            return f"Clarify how {topic} should be interpreted."
        joined = ", ".join(categories)
        return f"Offer concrete examples for {topic}; address {joined} language explicitly."

    def map_hypotheses(
        self, statements: Sequence[str], *, context: str | None = None
    ) -> list[MisconceptionHypothesis]:
        """Return ordered misconception hypotheses for the provided statements."""

        if not statements:
            return []

        context_tokens = self._tokens(context or "")
        topic_scores: Counter[str] = Counter()
        topic_triggers: defaultdict[str, list[str]] = defaultdict(list)

        for statement in statements:
            tokens = self._tokens(statement)
            if not tokens:
                continue

            triggers = self._classify_triggers(statement)
            base = self.base_risk + 0.05 * len(triggers)

            for topic in tokens:
                score = base
                if topic in context_tokens:
                    score += 0.08
                if "negation" in triggers and topic in context_tokens:
                    score += 0.12
                if "absolutist" in triggers:
                    score *= self.amplification

                topic_scores[topic] = max(topic_scores[topic], round(score, 3))
                topic_triggers[topic].extend(triggers)

        hypotheses: list[MisconceptionHypothesis] = []
        for topic, score in topic_scores.most_common():
            triggers = tuple(sorted(set(topic_triggers[topic])))
            hypotheses.append(
                MisconceptionHypothesis(
                    topic=topic,
                    risk_score=score,
                    triggers=triggers,
                    mitigation=self._mitigation(topic, triggers),
                )
            )

        return hypotheses

    def summarize(
        self, statements: Sequence[str], *, context: str | None = None
    ) -> Mapping[str, object]:
        """Return a compact summary and keep the heavier details optional."""

        hypotheses = self.map_hypotheses(statements, context=context)
        peak_risk = hypotheses[0].risk_score if hypotheses else 0.0
        topics = [hypothesis.topic for hypothesis in hypotheses]

        return {
            "topics": topics,
            "peak_risk": peak_risk,
            "count": len(hypotheses),
            "hypotheses": hypotheses,
        }
