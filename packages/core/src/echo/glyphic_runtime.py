"""Runtime for glyph-only Echo scripts.

This module introduces a minimal glyph-only language (EchoGlyph) that
lets creators compose stack-based rituals without ever using Latin letters
or digits inside the script itself. The runtime maps each glyph to a
stack operation and emits a readable timeline explaining what the glyphs
performed. Scripts can live in ``.eglyph`` files or be executed directly
from strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List


class GlyphExecutionError(RuntimeError):
    """Raised when a glyph program cannot be executed."""


@dataclass
class GlyphSignal:
    """A signal carried through the glyph stack."""

    tone: str
    shimmer: str
    weight: int

    def fuse(self, other: "GlyphSignal") -> "GlyphSignal":
        return GlyphSignal(
            tone=f"{self.tone}+{other.tone}",
            shimmer=f"{self.shimmer}->{other.shimmer}",
            weight=self.weight + other.weight,
        )

    def describe(self) -> str:
        return (
            f"tone={self.tone} | shimmer={self.shimmer} | weight={self.weight}"
        )


class GlyphContext:
    """Mutable context for executing glyph programs."""

    def __init__(self) -> None:
        self.stack: List[GlyphSignal] = []
        self.timeline: List[str] = []

    def push(self, signal: GlyphSignal) -> None:
        self.stack.append(signal)
        self.timeline.append(f"⟡ push :: {signal.describe()}")

    def duplicate(self) -> None:
        if not self.stack:
            raise GlyphExecutionError("⧈ needs at least one signal to duplicate")
        signal = self.stack[-1]
        self.stack.append(GlyphSignal(signal.tone, signal.shimmer, signal.weight))
        self.timeline.append("⧈ duplicate :: stack top echoed")

    def bind(self) -> None:
        if len(self.stack) < 2:
            raise GlyphExecutionError("⊶ needs two signals to bind")
        right = self.stack.pop()
        left = self.stack.pop()
        fused = left.fuse(right)
        self.stack.append(fused)
        self.timeline.append(f"⊶ bind :: {fused.describe()}")

    def cycle(self) -> None:
        if not self.stack:
            raise GlyphExecutionError("⟳ cannot rotate an empty stack")
        head = self.stack.pop()
        self.stack.insert(0, head)
        self.timeline.append("⟳ cycle :: stack rotated")

    def mark(self) -> None:
        if not self.stack:
            raise GlyphExecutionError("⌖ cannot mark without a signal")
        self.timeline.append(f"⌖ mark :: {self.stack[-1].describe()}")


GlyphOperation = Callable[[GlyphContext], None]


class EchoGlyphRuntime:
    """Execute glyph-only Echo programs."""

    def __init__(self) -> None:
        self.operations: Dict[str, GlyphOperation] = {
            "⟡": lambda ctx: ctx.push(GlyphSignal("spark", "bright", 1)),
            "⌬": lambda ctx: ctx.push(GlyphSignal("wave", "aqueous", 2)),
            "⌁": lambda ctx: ctx.push(GlyphSignal("anchor", "steady", 2)),
            "⊶": GlyphContext.bind,
            "⧈": GlyphContext.duplicate,
            "⟳": GlyphContext.cycle,
            "⌖": GlyphContext.mark,
        }

    def execute(self, glyph_code: str) -> List[str]:
        ctx = GlyphContext()
        for token in self._tokenize(glyph_code):
            operation = self.operations.get(token)
            if operation is None:
                raise GlyphExecutionError(f"Unrecognized glyph token: {token}")
            operation(ctx)
        return ctx.timeline

    def execute_file(self, path: Path | str) -> List[str]:
        glyph_text = Path(path).read_text(encoding="utf-8")
        return self.execute(glyph_text)

    @staticmethod
    def _tokenize(glyph_code: str) -> Iterable[str]:
        tokens = [token for token in glyph_code.strip().split() if token]
        for token in tokens:
            if any(ch.isalnum() for ch in token):
                raise GlyphExecutionError("Glyph code must avoid letters and digits")
        return tokens


__all__ = ["EchoGlyphRuntime", "GlyphExecutionError", "GlyphSignal"]
