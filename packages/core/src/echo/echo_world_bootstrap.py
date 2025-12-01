"""Bootstrap layer that wires InnovationSuite with the OuterLink runtime."""

from __future__ import annotations

import argparse
import json
import logging
from typing import Dict, Mapping

from echo.innovation_suite import InnovationOrchestrator
from outerlink.runtime import OuterLinkRuntime

LOGGER = logging.getLogger(__name__)


class EchoWorldBootstrap:
    """Orchestrate the innovation suite and the OuterLink runtime together."""

    def __init__(self) -> None:
        self.innovation_suite = InnovationOrchestrator()
        self.outerlink_runtime = OuterLinkRuntime()

    def activate(self, dry_run: bool = False) -> Dict[str, object]:
        """Activate EchoWorld, keeping side effects minimal when ``dry_run`` is set."""

        LOGGER.info("[ECHOWORLD] Bootstrapping EchoWorld runtime…")

        innovation_status = "initialized"
        outerlink_status = "initialized"

        if dry_run:
            try:
                # Lightweight orchestration to verify wiring without heavy work.
                self.innovation_suite.execute()
                innovation_status = "sanity_checked"
            except Exception as exc:  # pragma: no cover - defensive guard
                LOGGER.warning("Innovation suite sanity check skipped: %s", exc)

            try:
                self.outerlink_runtime.emit_state()
                outerlink_status = "sanity_checked"
            except Exception as exc:  # pragma: no cover - defensive guard
                LOGGER.warning("OuterLink runtime sanity check skipped: %s", exc)

            return {
                "innovation_suite": innovation_status,
                "outerlink_runtime": outerlink_status,
                "mode": "dry_run",
            }

        report = self.innovation_suite.execute()
        state = self.outerlink_runtime.emit_state()
        # Flush in a safe, offline-first manner; no blocking operations expected.
        self.outerlink_runtime.flush_events()

        return {
            "innovation_suite": innovation_status,
            "outerlink_runtime": outerlink_status,
            "mode": "live",
            "details": {
                "innovation": {
                    "ghost_stubs": len(report.ghost_stubs),
                    "superposition_tasks": len(report.superposition_tasks),
                },
                "outerlink": {
                    "online": state.get("online"),
                    "last_sync": state.get("last_sync"),
                },
            },
        }


def run_echoworld(dry_run: bool = False) -> Dict[str, object]:
    """Convenience helper for triggering the bootstrap and printing status."""

    bootstrap = EchoWorldBootstrap()
    status = bootstrap.activate(dry_run=dry_run)

    human_readable = json.dumps(status, indent=2, sort_keys=True)
    LOGGER.info("[ECHOWORLD] Status:\n%s", human_readable)
    print(human_readable)
    return status


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EchoWorld bootstrap orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Run without side effects")
    parser.add_argument("--json", action="store_true", help="Print status as JSON")
    return parser


def _format_status(status: Mapping[str, object], as_json: bool) -> str:
    if as_json:
        return json.dumps(status)
    return "\n".join(f"{key}: {value}" for key, value in status.items())


def main() -> int:  # pragma: no cover - CLI entrypoint
    logging.basicConfig(level=logging.INFO)
    parser = _build_parser()
    args = parser.parse_args()

    status = run_echoworld(dry_run=args.dry_run)
    output = _format_status(status, args.json)
    print(output)
    return 0


if __name__ == "__main__":  # pragma: no cover - module CLI
    raise SystemExit(main())
