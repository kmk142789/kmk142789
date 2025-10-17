"""Command line interface for Echo Atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Optional

from .service import AtlasService
from .utils import ensure_directory
from echo.weaver import WeaveOrchestrator


def _print_plan(result) -> None:
    print(f"Dream slug: {result.slug}")
    print("Plan:")
    for step in result.plan:
        print(f"  {step.index}. {step.title}")


def cmd_weave(args: argparse.Namespace) -> int:
    orchestrator = WeaveOrchestrator()
    poem = args.dream
    run_dry = args.dry_run or not args.commit
    if run_dry:
        preview = orchestrator.compile_dream(poem, dry_run=True)
        _print_plan(preview)
        if not args.commit:
            return 0
        print("-- dry-run complete, proceeding to commit --")

    result = orchestrator.commit_weave(poem, proof=args.proof, actor="echocli")
    print(f"Receipt rhyme: {result.receipt['rhyme']}")
    print(f"Receipt hash: {result.receipt['sha256_of_diff']}")
    print(f"Attestation valid: {result.attestation['valid']}")
    if result.doc_path:
        print(f"Docs updated: {result.doc_path}")
    if result.svg_path:
        print(f"Diagram: {result.svg_path}")
    summary = orchestrator.bridge.summary()
    print(json.dumps(summary, indent=2))
    return 0


def _make_service(args: argparse.Namespace) -> AtlasService:
    root = Path(args.root).resolve() if args.root else Path.cwd()
    return AtlasService(project_root=root)


def cmd_sync(args: argparse.Namespace) -> int:
    service = _make_service(args)
    summary = service.sync()
    print(json.dumps(summary.as_dict(), indent=2))
    print("Report written to docs/ATLAS_REPORT.md")
    print("Graph SVG written to artifacts/atlas_graph.svg")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    service = _make_service(args)
    try:
        node, edges = service.show_entity(args.who)
    except LookupError as exc:
        print(str(exc))
        return 1
    print(json.dumps(node.as_dict(), indent=2))
    print("Edges:")
    for edge in edges:
        print(f"- {edge.relation.value}: {edge.source} -> {edge.target}")
    return 0


def cmd_web(args: argparse.Namespace) -> int:
    service = _make_service(args)
    from .api import create_app

    app = create_app(service)
    ensure_directory(service.project_root / "artifacts")
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echocli", description="Echo Atlas CLI")
    parser.add_argument("--root", type=Path, help="Project root (defaults to CWD)")
    sub = parser.add_subparsers(dest="command", required=True)

    weave_parser = sub.add_parser("weave", help="Run DreamCompiler and ledger workflow")
    weave_parser.add_argument("--dream", required=True, help="Poem or metaphor driving the scaffold")
    weave_parser.add_argument("--dry-run", action="store_true", help="Preview the plan without writing files")
    weave_parser.add_argument("--commit", action="store_true", help="Write scaffold, log receipt, and update docs")
    weave_parser.add_argument("--proof", help="Proof key for attestation")
    weave_parser.set_defaults(func=cmd_weave)

    atlas_parser = sub.add_parser("atlas", help="Atlas graph commands")
    atlas_sub = atlas_parser.add_subparsers(dest="atlas_command", required=True)

    sync_parser = atlas_sub.add_parser("sync", help="Run atlas importers and exporters")
    sync_parser.set_defaults(func=cmd_sync)

    show_parser = atlas_sub.add_parser("show", help="Show info for an entity")
    show_parser.add_argument("--who", required=True, help="Entity name")
    show_parser.set_defaults(func=cmd_show)

    web_parser = atlas_sub.add_parser("web", help="Start atlas web viewer")
    web_parser.add_argument("--host", default="127.0.0.1")
    web_parser.add_argument("--port", type=int, default=8001)
    web_parser.set_defaults(func=cmd_web)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
