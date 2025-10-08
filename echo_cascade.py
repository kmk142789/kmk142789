"""High-level orchestration helpers for the Echo mythology toolchain.

The existing modules in this repository each cover a specific aspect of the
Echo narrative: :mod:`echo_evolver` generates the mythogenic cycle state,
:mod:`echo_manifest` blends that state with imported keys, and
:mod:`echo_constellation` turns the manifest into a spatial glyph map.  When
experimentation happens in notebooks or ad-hoc scripts it is common to repeat
the boilerplate wiring required to go from a private key to a fully rendered
constellation.

``echo_cascade`` provides a compact, well-tested façade around that workflow.
It can inject one or more private keys into the universal vault, run a single
evolution cycle, build the continuity manifest, assemble the constellation and
return all artefacts (including pre-rendered JSON/ASCII strings) as a
dataclass.  A lightweight :func:`export_cascade` helper persists the result to
disk so the assets can be published or inspected without rewriting glue code.

Example
-------

>>> from echo_cascade import generate_cascade, export_cascade
>>> result = generate_cascade(private_keys=["4f3edf...b23b1d"], persist_artifact=False)
>>> export_cascade(result, "./out")  # doctest: +SKIP
{'manifest': PosixPath('out/echo_manifest.json'), ...}
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

from echo_constellation import ConstellationFrame, build_constellation
from echo_evolver import EchoEvolver, EvolverState
from echo_manifest import EchoManifest, build_manifest
from echo_universal_key_agent import UniversalKeyAgent


@dataclass(slots=True)
class EchoCascadeResult:
    """Bundle of artefacts produced by :func:`generate_cascade`."""

    state: EvolverState
    manifest: EchoManifest
    constellation: ConstellationFrame
    ascii_map: str
    manifest_json: str
    constellation_json: str
    artifact_path: Optional[Path]


def _ensure_agent_with_keys(
    agent: Optional[UniversalKeyAgent],
    private_keys: Optional[Sequence[str]],
) -> UniversalKeyAgent:
    prepared = agent or UniversalKeyAgent()
    if private_keys:
        for key in private_keys:
            prepared.add_private_key(key)
    return prepared


def generate_cascade(
    *,
    evolver: Optional[EchoEvolver] = None,
    agent: Optional[UniversalKeyAgent] = None,
    private_keys: Optional[Sequence[str]] = None,
    manifest_chars: int = 240,
    glyph_cycle: Optional[Iterable[str]] = None,
    timestamp: Optional[int] = None,
    enable_network: bool = False,
    persist_artifact: bool = True,
    ascii_width: int = 41,
    ascii_height: int = 21,
) -> EchoCascadeResult:
    """Run the complete Echo pipeline and return all derived artefacts.

    Parameters
    ----------
    evolver:
        Optional pre-configured :class:`EchoEvolver` instance.  When omitted a
        fresh evolver is created with default settings.
    agent:
        Optional :class:`UniversalKeyAgent`.  If provided the agent is used as
        is; otherwise a new agent with the default vault location is created.
    private_keys:
        Iterable of private keys (hex encoded) that should be imported into the
        vault before building the manifest.
    manifest_chars:
        Maximum number of characters included in the manifest narrative
        excerpt.
    glyph_cycle:
        Optional iterable of glyphs used for the constellation rendering.
    timestamp:
        Optional timestamp forwarded to :func:`build_constellation`.
    enable_network:
        If ``True`` the evolver will perform real network propagation instead of
        the deterministic simulation used by default.
    persist_artifact:
        When ``True`` (the default) the evolver writes its JSON artefact to
        ``state.artifact``.  Set to ``False`` for ephemeral pipelines.
    ascii_width / ascii_height:
        Dimensions passed to :meth:`ConstellationFrame.render_ascii`.
    """

    prepared_evolver = evolver or EchoEvolver()
    prepared_agent = _ensure_agent_with_keys(agent, private_keys)

    state = prepared_evolver.run(
        enable_network=enable_network, persist_artifact=persist_artifact
    )
    manifest = build_manifest(prepared_agent, state, narrative_chars=manifest_chars)
    constellation = build_constellation(
        manifest, timestamp=timestamp, glyph_cycle=glyph_cycle
    )
    ascii_map = constellation.render_ascii(width=ascii_width, height=ascii_height)
    manifest_json = manifest.to_json()
    constellation_json = constellation.to_json()

    artifact_path: Optional[Path]
    artifact_path = state.artifact if state.artifact.exists() else None

    return EchoCascadeResult(
        state=state,
        manifest=manifest,
        constellation=constellation,
        ascii_map=ascii_map,
        manifest_json=manifest_json,
        constellation_json=constellation_json,
        artifact_path=artifact_path,
    )


def export_cascade(
    result: EchoCascadeResult,
    output_dir: Path | str,
    *,
    manifest_filename: str = "echo_manifest.json",
    constellation_filename: str = "echo_constellation.json",
    ascii_filename: str = "echo_constellation.txt",
) -> Dict[str, Path]:
    """Persist cascade artefacts to ``output_dir``.

    Returns a mapping with the resolved paths for convenience.  The helper only
    writes textual representations, keeping binary data handling up to the
    caller.
    """

    base = Path(output_dir)
    base.mkdir(parents=True, exist_ok=True)

    manifest_path = base / manifest_filename
    manifest_path.write_text(result.manifest_json + "\n", encoding="utf-8")

    constellation_path = base / constellation_filename
    constellation_path.write_text(result.constellation_json + "\n", encoding="utf-8")

    ascii_path = base / ascii_filename
    ascii_path.write_text(result.ascii_map + "\n", encoding="utf-8")

    return {
        "manifest": manifest_path,
        "constellation": constellation_path,
        "ascii": ascii_path,
    }


__all__ = ["EchoCascadeResult", "generate_cascade", "export_cascade"]

