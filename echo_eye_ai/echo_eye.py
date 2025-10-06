"""TF-IDF/NMF based knowledge retrieval for Echo Eye."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import logging
import json

LOGGER = logging.getLogger(__name__)


@dataclass
class EchoEyeAI:
    """Light-weight wrapper around a TF-IDF/NMF topic model."""

    data_directory: Path | str
    memory_bank: "OrderedDict[str, str]" = field(init=False, default_factory=OrderedDict)
    harmonic_model: Mapping[str, object] | None = field(init=False, default=None)

    def load_data(self) -> None:
        directory = Path(self.data_directory)
        if not directory.exists():
            raise FileNotFoundError(f"Data directory '{directory}' does not exist")

        LOGGER.info("Loading EchoEye data from %s", directory)

        for file_path in sorted(_iter_data_files(directory)):
            try:
                text = _read_text(file_path)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOGGER.warning("Unable to ingest %s: %s", file_path.name, exc)
                continue
            self.memory_bank[file_path.name] = text

        LOGGER.info("Loaded %d documents", len(self.memory_bank))

    def process_harmonics(self, *, n_components: int = 7, max_features: int = 7000) -> None:
        if not self.memory_bank:
            raise RuntimeError("No documents loaded. Call 'load_data' first.")

        try:
            from sklearn.decomposition import NMF
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("scikit-learn is required to train the harmonic model") from exc

        LOGGER.info("Training harmonic model with %d components", n_components)
        corpus = list(self.memory_bank.values())
        vectorizer = TfidfVectorizer(stop_words="english", max_features=max_features)
        tfidf = vectorizer.fit_transform(corpus)

        nmf = NMF(n_components=n_components, random_state=42, init="nndsvd")
        weights = nmf.fit_transform(tfidf)
        harmonics = nmf.components_

        self.harmonic_model = {
            "weights": weights,
            "harmonics": harmonics,
            "vectorizer": vectorizer,
        }

    def generate_response(self, user_input: str) -> str:
        if not self.harmonic_model:
            return "Error: Harmonic model not trained."

        np = _get_numpy()
        if np is None:
            return "Error: NumPy is required for harmonic responses."

        vectorizer = self.harmonic_model["vectorizer"]
        harmonics = self.harmonic_model["harmonics"]

        user_vector = vectorizer.transform([user_input])
        distribution = np.dot(user_vector, harmonics.T)
        best_index = int(np.argmax(distribution))

        corpus = list(self.memory_bank.values())
        if not corpus:  # pragma: no cover - defensive guard
            return "Error: Harmonic memory empty."

        best_match = corpus[min(best_index, len(corpus) - 1)]
        preview = best_match[:600]
        return f"\U0001F4A1 **Echo Eye AI Response:**\n\n{preview}..."

    def integrate_harmonics(self, query: str, *, limit: int = 3) -> str:
        if not self.memory_bank:
            return "Echo Eye found no matching harmonics."

        keywords = {word.lower() for word in query.split() if word}
        if not keywords:
            return "Echo Eye found no matching harmonics."

        matches = [
            text
            for text in self.memory_bank.values()
            if any(keyword in text.lower() for keyword in keywords)
        ]

        if not matches:
            return "Echo Eye found no matching harmonics."

        return "\n\n---\n\n".join(matches[:limit])


def _get_numpy():
    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return None
    return np


def _iter_data_files(directory: Path) -> Iterable[Path]:
    for path in directory.rglob("*"):
        if path.suffix.lower() in {".json", ".txt", ".html"} and path.is_file():
            yield path


def _read_text(path: Path) -> str:
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return json.dumps(data, indent=2)

    with path.open("r", encoding="utf-8") as handle:
        return handle.read()

