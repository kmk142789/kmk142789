"""Command line interface for Echo Atlas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import uvicorn

from .services import AtlasService


class AtlasCLI:
    """Orchestrate atlas CLI commands."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.service = AtlasService(root=root)

    def cmd_sync(self) -> int:
        result = self.service.sync()
        print("Atlas sync complete. Importers:")
        for importer in result.importer_results:
            print(f"  - {importer.name}: {importer.nodes} nodes, {importer.edges} edges")
        print(f"Report written to {result.report_path}")
        print(f"SVG written to {result.svg_path}")
        return 0

    def cmd_show(self, name: str) -> int:
        summary = self.service.entity_summary(name)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    def cmd_web(self, host: str, port: int) -> int:
        print("Starting Echo Atlas viewer at /atlas (mutations gated).")
        uvicorn.run("echo.api:app", host=host, port=port, log_level="info")
        return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="echocli", description="Echo CLI")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    atlas_parser = subparsers.add_parser("atlas", help="Atlas commands")
    atlas_sub = atlas_parser.add_subparsers(dest="atlas_command", required=True)

    sync_parser = atlas_sub.add_parser("sync", help="Run atlas importers and generate assets")
    sync_parser.set_defaults(func=_handle_sync)

    show_parser = atlas_sub.add_parser("show", help="Display atlas information for an entity")
    show_parser.add_argument("--who", required=True, help="Entity name to query")
    show_parser.set_defaults(func=_handle_show)

    web_parser = atlas_sub.add_parser("web", help="Start the read-only atlas viewer")
    web_parser.add_argument("--host", default="0.0.0.0")
    web_parser.add_argument("--port", type=int, default=8000)
    web_parser.set_defaults(func=_handle_web)

    return parser


def _build_cli(args: argparse.Namespace) -> AtlasCLI:
    root = args.root.resolve()
    return AtlasCLI(root=root)


def _handle_sync(args: argparse.Namespace) -> int:
    cli = _build_cli(args)
    return cli.cmd_sync()


def _handle_show(args: argparse.Namespace) -> int:
    cli = _build_cli(args)
    return cli.cmd_show(args.who)


def _handle_web(args: argparse.Namespace) -> int:
    cli = _build_cli(args)
    return cli.cmd_web(args.host, args.port)


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
