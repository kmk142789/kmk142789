"""Echo Kaleidoscope generator for playful ASCII symmetry.

This module introduces :class:`EchoKaleidoscope`, a lightweight engine that
spins harmonic patterns inspired by the wider Echo ecosystem.  It can be used
as a Python API or as a small command line toy to paint mirrored glyphs in the
terminal.  The implementation keeps dependencies minimal while still offering a
touch of theatricality through deterministic randomness and gentle animation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import argparse
import random
import sys
import time
from typing import Iterable, List, Optional, Sequence


DEFAULT_PALETTE: Sequence[str] = (".", "*", "+", "x", "o", "#")


@dataclass
class EchoKaleidoscope:
    """Generate mirrored ASCII patterns with a customizable palette.

    Parameters
    ----------
    width:
        Total number of glyphs per row.  Must be at least ``2``.
    height:
        Total number of rows to generate.  Must be at least ``1``.
    palette:
        Sequence of characters used to paint the mosaic.  When the palette is
        empty a single space is used so the output still has visible geometry.
    """

    width: int = 40
    height: int = 18
    palette: Sequence[str] = field(default_factory=lambda: DEFAULT_PALETTE)

    def __post_init__(self) -> None:
        if self.width < 2:
            raise ValueError("width must be at least 2 to form a mirror")
        if self.height < 1:
            raise ValueError("height must be at least 1")

    def generate_frame(self, seed: Optional[int] = None) -> List[str]:
        """Create a list of mirrored rows for a single kaleidoscope frame."""

        rng = random.Random(seed)
        palette = list(self.palette) or [" "]
        half_width = self.width // 2
        has_center = self.width % 2

        rows: List[str] = []
        for _ in range(self.height):
            left = [rng.choice(palette) for _ in range(half_width)]
            if has_center:
                center = rng.choice(palette)
                row = left + [center] + list(reversed(left))
            else:
                row = left + list(reversed(left))
            rows.append("".join(row))
        return rows

    def render(self, seed: Optional[int] = None) -> str:
        """Return a newline-joined string containing a kaleidoscope frame."""

        return "\n".join(self.generate_frame(seed=seed))

    def animate(
        self,
        frames: int = 12,
        delay: float = 0.18,
        seed: Optional[int] = None,
        stream: Optional[Iterable[str]] = None,
    ) -> None:
        """Stream multiple frames to ``stream`` for a simple terminal show.

        The default ``stream`` writes to ``sys.stdout``.  When ``seed`` is
        provided the animation becomes deterministic: each frame offsets the
        seed to produce a smooth-yet-repeatable drift.
        """

        if frames < 1:
            raise ValueError("frames must be at least 1")

        output = sys.stdout if stream is None else stream
        base_seed = seed

        for index in range(frames):
            frame_seed = None if base_seed is None else base_seed + index
            frame = self.render(seed=frame_seed)
            print("\x1b[2J\x1b[H", end="", file=output)  # Clear screen & move cursor
            print(frame, file=output)
            output.flush()
            time.sleep(max(0.0, delay))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Spin a mirrored ASCII kaleidoscope inspired by Echo",
    )
    parser.add_argument("--width", type=int, default=40, help="Total glyphs per row")
    parser.add_argument("--height", type=int, default=18, help="Number of rows")
    parser.add_argument(
        "--palette",
        type=str,
        default="".join(DEFAULT_PALETTE),
        help="Characters to use (e.g. '.:*#')",
    )
    parser.add_argument("--seed", type=int, help="Seed for deterministic patterns")
    parser.add_argument(
        "--frames",
        type=int,
        default=1,
        help="Render multiple frames for a short animation",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.18,
        help="Seconds to wait between frames when animating",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    kaleidoscope = EchoKaleidoscope(
        width=args.width,
        height=args.height,
        palette=tuple(args.palette) if args.palette else (" ",),
    )

    if args.frames == 1:
        print(kaleidoscope.render(seed=args.seed))
    else:
        try:
            kaleidoscope.animate(
                frames=args.frames,
                delay=args.delay,
                seed=args.seed,
            )
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
