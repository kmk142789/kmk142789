"""Aether Architect
====================

Utility for generating self-visualizing SVG artifacts from a source file and
keeping a small manifesto with telemetry about the generation.  The tool is a
safer, non-self-modifying interpretation of the quine-style script provided in
user payloads: it reads a target source file, paints a bar for each line, and
increments a generation counter stored in a separate JSON state file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass
class AetherState:
    """Persisted state for the architect."""

    generation: int = 1

    @classmethod
    def load(cls, path: Path) -> "AetherState":
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(generation=int(data.get("generation", 1)))
        except (ValueError, OSError):
            return cls()

    def save(self, path: Path) -> None:
        path.write_text(json.dumps({"generation": self.generation}, indent=2), encoding="utf-8")


@dataclass
class AetherMetadata:
    generation: int
    timestamp: datetime
    sha256_prefix: str
    line_count: int
    target: Path


class AetherArchitect:
    """Generate SVG artifacts and a manifesto for a target source file."""

    def __init__(self, target: Path, state_path: Path, output_dir: Path):
        self.target = target
        self.state_path = state_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.state = AetherState.load(self.state_path)
        self.source_lines = self._read_source()
        self.metadata = self._build_metadata()

    def _read_source(self) -> list[str]:
        return self.target.read_text(encoding="utf-8").splitlines()

    def _build_metadata(self) -> AetherMetadata:
        source = "\n".join(self.source_lines)
        sha_prefix = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        return AetherMetadata(
            generation=self.state.generation,
            timestamp=datetime.now(timezone.utc),
            sha256_prefix=sha_prefix,
            line_count=len(self.source_lines),
            target=self.target,
        )

    def _color_from_hash(self, content: str) -> str:
        digest = hashlib.md5(content.encode("utf-8")).hexdigest()
        return f"#{digest[:6]}"

    def _opacity_from_indent(self, indent: int) -> float:
        opacity = 1.0 - indent * 0.05
        return max(opacity, 0.2)

    def forge_visual_artifact(self) -> Path:
        """Render the source file into a simple bar-chart style SVG."""

        bar_height = 8
        line_spacing = 12
        svg_height = (self.metadata.line_count * line_spacing) + 120
        svg_width = 900

        lines: list[str] = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" style="background-color:#0d1117">',
            f"<!-- Aether Architect :: Generation {self.metadata.generation} -->",
            (
                f'<text x="20" y="40" fill="#58a6ff" font-family="monospace" font-size="20" '
                f">GEN_{self.metadata.generation} :: HASH_{self.metadata.sha256_prefix}</text>"
            ),
            (
                f'<text x="20" y="70" fill="#8b949e" font-family="monospace" font-size="12" '
                f">{self.metadata.timestamp.isoformat()}</text>"
            ),
            (
                f'<text x="20" y="90" fill="#8b949e" font-family="monospace" font-size="12" '
                f">{self.metadata.target}</text>"
            ),
        ]

        y_pos = 120
        for line in self.source_lines:
            stripped = line.strip()
            y_pos += line_spacing
            if not stripped:
                continue

            indent = len(line) - len(line.lstrip(" \t"))
            bar_width = min(820, max(60, len(stripped) * 9))
            color = self._color_from_hash(stripped)
            opacity = self._opacity_from_indent(indent)
            x_pos = 20 + (indent * 10)

            lines.append(
                (
                    f'<rect x="{x_pos}" y="{y_pos}" width="{bar_width}" height="{bar_height}" '
                    f'fill="{color}" rx="2" opacity="{opacity}" />'
                )
            )

        lines.append("</svg>")

        artifact_name = f"artifact_gen_{self.metadata.generation:03d}.svg"
        artifact_path = self.output_dir / artifact_name
        artifact_path.write_text("\n".join(lines), encoding="utf-8")
        return artifact_path

    def write_manifesto(self) -> Path:
        """Write a small markdown summary describing the latest artifact."""

        manifesto = self.output_dir / "AETHER_MANIFESTO.md"
        manifesto.write_text(
            """# Aether Architect 🏛️\n\n"""
            f"**Generation**: {self.metadata.generation}\n\n"
            f"**Last Mutation**: {self.metadata.timestamp.isoformat()}\n\n"
            f"**Target File**: `{self.metadata.target}`\n\n"
            f"**SHA256 (prefix)**: `{self.metadata.sha256_prefix}`\n\n"
            f"**Lines of Code**: {self.metadata.line_count}\n\n"
            "This file is automatically produced by `tools/aether_architect.py`. "
            "Run the script again to produce the next generation artifact.\n",
            encoding="utf-8",
        )
        return manifesto

    def evolve(self) -> None:
        self.state.generation += 1
        self.state.save(self.state_path)

    def run(self) -> tuple[Path, Path]:
        artifact = self.forge_visual_artifact()
        manifesto = self.write_manifesto()
        self.evolve()
        return artifact, manifesto


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SVG artifacts from a source file")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path(__file__),
        help="Path to the source file to visualize (default: this script)",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=Path(__file__).with_name("aether_state.json"),
        help="Path to the JSON file tracking the generation counter",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/aether_architect"),
        help="Directory where artifacts and manifesto are written",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = _parse_args(argv)
    architect = AetherArchitect(target=args.target, state_path=args.state, output_dir=args.output_dir)
    artifact, manifesto = architect.run()
    print(f"✨ Artifact created: {artifact}")
    print(f"📜 Manifesto updated: {manifesto}")
    print(f"➡️  Next generation will be {architect.state.generation}")


if __name__ == "__main__":
    main()
