"""Spectral canvas generator for mythogenic colour exploration.

This module introduces a compact utility for crafting deterministic colour
palettes and layered gradient matrices from arbitrary narrative seeds.  The
``SpectralCanvas`` class turns strings – typically titles, glyph collections or
story fragments – into a reproducible three-channel NumPy array.  The array can
then be exported as a Pandas ``DataFrame`` for downstream analysis or rendered
via Rich tables for quick terminal previews.

The implementation intentionally keeps its dependencies lightweight by relying
on the scientific stack already present in the project.  No file IO occurs in
order to keep the helper friendly for automated tests and sandbox execution
environments.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence

import numpy as np
from rich.table import Table

try:  # pragma: no cover - optional dependency path
    import pandas as pd
except ModuleNotFoundError:  # pragma: no cover - optional dependency path
    pd = None  # type: ignore[assignment]

__all__ = ["PaletteColor", "SpectralCanvas", "generate_palette"]


@dataclass(frozen=True)
class PaletteColor:
    """Simple RGB palette entry.

    The floating-point values are normalised in the inclusive range ``[0.0, 1.0]``.
    """

    name: str
    red: float
    green: float
    blue: float

    def as_tuple(self) -> tuple[float, float, float]:
        """Return an RGB tuple for convenience."""

        return (self.red, self.green, self.blue)

    def to_hex(self) -> str:
        """Return a hexadecimal colour representation."""

        r, g, b = (max(0, min(255, int(channel * 255))) for channel in self.as_tuple())
        return f"#{r:02x}{g:02x}{b:02x}"


def _chunked_digest(seed: str, length: int) -> List[int]:
    """Expand ``seed`` into deterministic integer values."""

    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    required = math.ceil(length / len(digest))
    buffer = (digest * required)[:length]
    return list(buffer)


def generate_palette(seed: str, size: int = 5) -> List[PaletteColor]:
    """Generate ``size`` palette colours derived from ``seed``.

    The helper derives each RGB triple from independent sections of the hashed
    seed, ensuring that identical seeds always lead to identical palettes.
    """

    if size <= 0:
        raise ValueError("Palette size must be positive")

    channels = _chunked_digest(seed, size * 4)
    palette: List[PaletteColor] = []
    for index in range(size):
        r, g, b, label = channels[index * 4 : index * 4 + 4]
        name = f"tone-{index}-{label:02x}"
        palette.append(
            PaletteColor(
                name=name,
                red=r / 255.0,
                green=g / 255.0,
                blue=b / 255.0,
            )
        )
    return palette


@dataclass
class SpectralCanvas:
    """Layered gradient generator derived from narrative seeds."""

    width: int
    height: int
    seed: str
    layers: Sequence[str] = ()

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Canvas dimensions must be positive")

    def _layer_values(self) -> Iterable[tuple[np.ndarray, float]]:
        base_hash = hashlib.sha256(self.seed.encode("utf-8")).hexdigest()
        for offset, layer in enumerate((self.seed, *self.layers)):
            layer_hash = hashlib.sha256(f"{base_hash}:{layer}:{offset}".encode("utf-8")).digest()
            freq_x = 1 + layer_hash[0] % 7
            freq_y = 1 + layer_hash[1] % 7
            phase = (layer_hash[2] / 255.0) * math.pi
            amplitude = 0.25 + (layer_hash[3] / 255.0) * 0.5
            x = np.linspace(0.0, 1.0, self.width, dtype=np.float64)
            y = np.linspace(0.0, 1.0, self.height, dtype=np.float64)
            grid_x, grid_y = np.meshgrid(x, y)
            wave = np.sin(2 * math.pi * (freq_x * grid_x + freq_y * grid_y) + phase)
            yield wave, amplitude

    def render_matrix(self) -> np.ndarray:
        """Return a ``height x width x 3`` matrix normalised to ``[0.0, 1.0]``."""

        canvas = np.zeros((self.height, self.width, 3), dtype=np.float64)
        palette = generate_palette(self.seed + "::" + "::".join(self.layers), size=3)
        for channel_index, color in enumerate(palette):
            channel = np.zeros((self.height, self.width), dtype=np.float64)
            for wave, amplitude in self._layer_values():
                channel += amplitude * wave
            channel = (channel - channel.min()) / max(channel.max() - channel.min(), 1e-12)
            scale = color.as_tuple()[channel_index]
            canvas[:, :, channel_index] = np.clip(channel * scale, 0.0, 1.0)
        return canvas

    def as_dataframe(self) -> "pd.DataFrame":
        """Return a flattened Pandas representation of the canvas."""

        if pd is None:  # pragma: no cover - depends on optional dependency
            raise ModuleNotFoundError("pandas is required to export DataFrames")

        matrix = self.render_matrix()
        y_coords, x_coords = np.indices((self.height, self.width))
        rows = {
            "x": x_coords.ravel(),
            "y": y_coords.ravel(),
            "red": matrix[:, :, 0].ravel(),
            "green": matrix[:, :, 1].ravel(),
            "blue": matrix[:, :, 2].ravel(),
        }
        return pd.DataFrame(rows)

    def describe(self) -> Table:
        """Build a Rich table summarising palette entries and canvas statistics."""

        matrix = self.render_matrix()
        palette = generate_palette(self.seed + "::" + "::".join(self.layers), size=3)
        table = Table(title=f"Spectral Canvas – {self.seed}")
        table.add_column("Channel", justify="left")
        table.add_column("Tone", justify="left")
        table.add_column("Range", justify="left")
        stats = zip(("Red", "Green", "Blue"), palette, matrix.transpose(2, 0, 1))
        for channel_name, tone, channel_matrix in stats:
            min_value = float(channel_matrix.min())
            max_value = float(channel_matrix.max())
            table.add_row(
                channel_name,
                tone.to_hex(),
                f"{min_value:.3f} – {max_value:.3f}",
            )
        return table

