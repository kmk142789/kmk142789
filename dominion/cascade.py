"""Cascade helpers for Dominion.

This module bridges the :mod:`echo_cascade` orchestration pipeline with the
Dominion plan system.  ``echo_cascade.generate_cascade`` is capable of
producing all of the artefacts required for a publication cycle, but Dominion
expects those artefacts to be expressed as action intents so they can be
applied, audited, and archived.  ``build_cascade_plan`` wraps the cascade and
translates the resulting payloads into :class:`~dominion.plans.ActionIntent`
entries so they can be executed through :class:`~dominion.executor.PlanExecutor`.

The module also exposes a small CLI (``python -m dominion.cascade``) that can
be used to compile a cascade plan from the command line.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional, Sequence, TYPE_CHECKING

from echo_cascade import generate_cascade

from .plans import ActionIntent, DominionPlan


if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from echo_evolver import EchoEvolver
    from echo_universal_key_agent import UniversalKeyAgent


DEFAULT_MANIFEST_FILENAME = "echo_manifest.json"
DEFAULT_CONSTELLATION_FILENAME = "echo_constellation.json"
DEFAULT_ASCII_FILENAME = "echo_constellation.txt"


def build_cascade_plan(
    output_dir: Path | str,
    *,
    private_keys: Optional[Sequence[str]] = None,
    manifest_chars: int = 240,
    glyph_cycle: Optional[Iterable[str]] = None,
    timestamp: Optional[int] = None,
    ascii_width: int = 41,
    ascii_height: int = 21,
    enable_network: bool = False,
    persist_artifact: bool = False,
    evolver: "EchoEvolver" | None = None,
    agent: "UniversalKeyAgent" | None = None,
    source: str = "dominion.cascade",
    manifest_filename: str = DEFAULT_MANIFEST_FILENAME,
    constellation_filename: str = DEFAULT_CONSTELLATION_FILENAME,
    ascii_filename: str = DEFAULT_ASCII_FILENAME,
) -> DominionPlan:
    """Generate a Dominion plan that exports Echo cascade artefacts.

    Parameters
    ----------
    output_dir:
        Directory (relative to the Dominion workspace) where cascade artefacts
        should be written once the plan is applied.
    private_keys:
        Optional sequence of private keys injected into the cascade prior to
        manifest generation.
    manifest_chars / ascii_width / ascii_height / glyph_cycle / timestamp:
        Parameters forwarded to :func:`echo_cascade.generate_cascade`.
    enable_network:
        When ``True`` the cascade is allowed to perform real network
        propagation.  The default keeps the deterministic offline simulation.
    persist_artifact:
        Whether the evolver should persist its state artefact.  Dominion plans
        typically operate on textual payloads, so this is disabled by default.
    evolver / agent:
        Optional preconfigured instances reused by the cascade.
    source:
        Value recorded in the resulting :class:`DominionPlan` ``source`` field.
    *_filename:
        Override the output filenames for the generated artefacts.
    """

    base_dir = Path(output_dir)

    cascade_result = generate_cascade(
        evolver=evolver,
        agent=agent,
        private_keys=private_keys,
        manifest_chars=manifest_chars,
        glyph_cycle=glyph_cycle,
        timestamp=timestamp,
        enable_network=enable_network,
        persist_artifact=persist_artifact,
        ascii_width=ascii_width,
        ascii_height=ascii_height,
    )

    payloads = {
        "manifest": (manifest_filename, cascade_result.manifest_json + "\n"),
        "constellation": (
            constellation_filename,
            cascade_result.constellation_json + "\n",
        ),
        "ascii": (ascii_filename, cascade_result.ascii_map + "\n"),
    }

    intents: list[ActionIntent] = []
    for name, (filename, content) in payloads.items():
        target_path = base_dir / filename
        intent = ActionIntent(
            intent_id=f"cascade-{name}",
            action_type="file.write",
            target=str(target_path),
            payload={"content": content},
            metadata={
                "artifact": name,
                "filename": filename,
                "output_dir": str(base_dir),
            },
        )
        intents.append(intent)

    plan = DominionPlan.from_intents(intents, source=source)

    cycle = getattr(cascade_result.state, "cycle", None)
    glyphs = getattr(cascade_result.state, "glyphs", None)
    artifact_path = getattr(cascade_result.state, "artifact", None)

    plan.metadata.update(
        {
            "cascade": {
                "cycle": cycle,
                "glyphs": glyphs,
                "output_dir": str(base_dir),
                "ascii_dimensions": [ascii_width, ascii_height],
                "manifest_chars": manifest_chars,
                "private_key_count": len(private_keys or []),
                "glyph_cycle": list(glyph_cycle) if glyph_cycle is not None else None,
                "timestamp": timestamp,
                "artifact_path": str(artifact_path) if artifact_path is not None else None,
                "outputs": {
                    name: str(base_dir / filename)
                    for name, (filename, _content) in payloads.items()
                },
            }
        }
    )

    return plan


def _load_keys(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, str):
        return [parsed]
    if isinstance(parsed, Sequence):
        return [str(item) for item in parsed if str(item)]

    return [line for line in (line.strip() for line in raw.splitlines()) if line]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compile an Echo cascade into a Dominion plan."
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        default="build/cascade",
        help="Directory (relative to repo root) for cascade artefacts.",
    )
    parser.add_argument(
        "--plan-dir",
        dest="plan_dir",
        default="build/dominion/plans",
        help="Directory where the Dominion plan will be written.",
    )
    parser.add_argument(
        "--plan-name",
        dest="plan_name",
        help="Optional explicit filename for the plan JSON output.",
    )
    parser.add_argument(
        "--private-key",
        dest="private_keys",
        action="append",
        default=[],
        help="Hex-encoded private key to inject (may be specified multiple times).",
    )
    parser.add_argument(
        "--keys-file",
        type=Path,
        help="Path to a JSON or newline-delimited file containing private keys.",
    )
    parser.add_argument(
        "--manifest-chars",
        type=int,
        default=240,
        help="Number of characters captured in the manifest narrative excerpt.",
    )
    parser.add_argument(
        "--glyph-cycle",
        help="Optional glyph cycle string forwarded to the cascade renderer.",
    )
    parser.add_argument(
        "--timestamp",
        type=int,
        help="Optional timestamp used when rendering the constellation.",
    )
    parser.add_argument(
        "--ascii-width",
        type=int,
        default=41,
        help="Width of the ASCII constellation map.",
    )
    parser.add_argument(
        "--ascii-height",
        type=int,
        default=21,
        help="Height of the ASCII constellation map.",
    )
    parser.add_argument(
        "--enable-network",
        action="store_true",
        help="Allow the cascade to perform real network propagation.",
    )
    parser.add_argument(
        "--persist-artifact",
        action="store_true",
        help="Persist the evolver JSON artefact to disk during the cascade run.",
    )
    parser.add_argument(
        "--source",
        default="dominion.cascade",
        help="Value recorded in the Dominion plan's source field.",
    )
    parser.add_argument(
        "--manifest-filename",
        default=DEFAULT_MANIFEST_FILENAME,
        help="Filename used for the manifest output.",
    )
    parser.add_argument(
        "--constellation-filename",
        default=DEFAULT_CONSTELLATION_FILENAME,
        help="Filename used for the constellation JSON output.",
    )
    parser.add_argument(
        "--ascii-filename",
        default=DEFAULT_ASCII_FILENAME,
        help="Filename used for the ASCII constellation output.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    private_keys = list(args.private_keys or [])
    if args.keys_file:
        private_keys.extend(_load_keys(args.keys_file))
    private_keys = [key for key in private_keys if key]

    glyph_cycle: Optional[Iterable[str]]
    glyph_cycle = list(args.glyph_cycle) if args.glyph_cycle else None

    plan = build_cascade_plan(
        args.output_dir,
        private_keys=private_keys or None,
        manifest_chars=args.manifest_chars,
        glyph_cycle=glyph_cycle,
        timestamp=args.timestamp,
        ascii_width=args.ascii_width,
        ascii_height=args.ascii_height,
        enable_network=args.enable_network,
        persist_artifact=args.persist_artifact,
        source=args.source,
        manifest_filename=args.manifest_filename,
        constellation_filename=args.constellation_filename,
        ascii_filename=args.ascii_filename,
    )

    plan_dir = Path(args.plan_dir)
    plan_dir.mkdir(parents=True, exist_ok=True)
    plan_name = args.plan_name or f"plan_{plan.plan_id}.json"
    plan_path = plan_dir / plan_name
    plan.write(plan_path)

    print(f"Plan {plan.plan_id} written to {plan_path}")
    print(
        "Intents: {} -> {}".format(
            len(plan.intents), [intent.target for intent in plan.intents]
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()

