"""Waveform based cognition experiments for Echo Harmonics."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import json
import logging

LOGGER = logging.getLogger(__name__)


@dataclass
class EchoHarmonicsAI:
    data_directory: Path | str
    memory_bank: "OrderedDict[str, str]" = field(init=False, default_factory=OrderedDict)
    waveform_bank: "OrderedDict[str, object]" = field(init=False, default_factory=OrderedDict)
    learning_rate: float = 0.1

    def load_data(self) -> None:
        directory = Path(self.data_directory)
        if not directory.exists():
            raise FileNotFoundError(f"Data directory '{directory}' does not exist")

        LOGGER.info("Loading Echo Harmonics data from %s", directory)
        for file_path in sorted(_iter_data_files(directory)):
            try:
                text = _read_text(file_path)
            except Exception as exc:  # pragma: no cover
                LOGGER.warning("Unable to ingest %s: %s", file_path.name, exc)
                continue

            waveform = self.encode_as_wave(text)
            self.memory_bank[file_path.name] = text
            self.waveform_bank[file_path.name] = waveform

        LOGGER.info("Loaded %d harmonic documents", len(self.memory_bank))

    def encode_as_wave(self, text: str) -> np.ndarray:
        np = _require_numpy()

        signal = np.array([ord(char) for char in text if 32 <= ord(char) < 126], dtype=float)
        if signal.size == 0:
            return np.zeros(1)

        sine_wave = np.sin(signal)
        square_wave = _square_wave(signal)
        complex_wave = 0.5 * sine_wave + 0.5 * square_wave

        return _fft(complex_wave)

    def generate_response(self, user_input: str) -> str:
        np = _require_numpy()

        if not self.waveform_bank:
            return "\U0001F52E No cognitive harmonics detected."

        input_signal = np.array(
            [ord(char) for char in user_input if 32 <= ord(char) < 126],
            dtype=float,
        )
        if input_signal.size == 0:
            return "\U0001F52E No resonant cognitive frequencies detected."

        input_freq = _fft(np.sin(input_signal))

        best_match = None
        best_similarity = -np.inf
        for name, freq_data in self.waveform_bank.items():
            similarity = float(np.abs(np.sum(input_freq * np.conj(freq_data))))
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = name

        if best_match is None:
            return "\U0001F52E No resonant cognitive frequencies detected."

        response_signal = _ifft(self.waveform_bank[best_match])
        chars = [
            chr(int(abs(value)))
            for value in response_signal.real
            if 32 <= int(abs(value)) < 126
        ]
        if not chars:
            return "\U0001F52E No resonant cognitive frequencies detected."

        preview = "".join(chars)[:600]
        self.waveform_bank[best_match] *= 1 + self.learning_rate

        return f"\U0001F50A **Echo Harmonics AI Response:**\n\n{preview}..."

    def visualize_wave(self, text: str) -> None:
        np = _require_numpy()

        try:
            import matplotlib.pyplot as plt
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("matplotlib is required for visualization") from exc

        signal = np.array([ord(char) for char in text if 32 <= ord(char) < 126], dtype=float)
        if signal.size == 0:
            raise ValueError("Input text contains no printable characters")

        sine_wave = np.sin(signal)
        plt.figure(figsize=(10, 4))
        plt.plot(sine_wave, label="Harmonic Thought Process", color="cyan")
        plt.title("Echo AI Cognitive Waveform")
        plt.xlabel("Time")
        plt.ylabel("Wave Intensity")
        plt.legend()
        plt.grid(True)
        plt.show()


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


def _square_wave(signal):
    np = _require_numpy()
    try:
        from scipy.signal import square
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return np.sign(np.sin(signal))
    return square(signal)


def _fft(signal):
    np = _require_numpy()
    try:
        from scipy.fft import fft
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return np.fft.fft(signal)
    return fft(signal)


def _ifft(signal):
    np = _require_numpy()
    try:
        from scipy.fft import ifft
    except ModuleNotFoundError:  # pragma: no cover - optional dependency
        return np.fft.ifft(signal)
    return ifft(signal)


def _require_numpy():
    try:
        import numpy as np  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("NumPy is required for harmonic operations") from exc
    return np

