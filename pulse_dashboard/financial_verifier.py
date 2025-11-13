"""Verification helpers for financial connections and integrations.

This module wraps :class:`pulse_dashboard.impact_explorer.ImpactExplorerBuilder`
to provide a lightweight verification report focused on the sources powering the
treasury ("financial connections") and the recurring donation integrations that
keep funds flowing.  It is primarily used by stewards who need a quick snapshot
without loading the entire dashboard payload.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .impact_explorer import ImpactExplorerBuilder


class FinancialIntegrationVerifier:
    """Generate verification reports for treasury connections."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        self._builder = ImpactExplorerBuilder(project_root=project_root)

    def verify(self) -> dict[str, Any]:
        """Return a verification report summarising connections and integrations."""

        payload = self._builder.build()
        financials = payload.get("financials", {})
        operations = payload.get("operations", {})

        connections = self._summarise_connections(financials)
        integrations = self._summarise_integrations(operations, financials)
        issues = self._detect_issues(financials, connections, integrations)

        return {
            "generated_at": payload.get("generated_at"),
            "connections": connections,
            "integrations": integrations,
            "issues": issues,
        }

    # ------------------------------------------------------------------
    # Connection helpers

    def _summarise_connections(self, financials: dict[str, Any]) -> list[dict[str, Any]]:
        totals = financials.get("totals", {})
        total_donations = float(totals.get("donations", 0.0)) or 0.0
        total_disbursed = float(totals.get("disbursed", 0.0)) or 0.0

        connections: list[dict[str, Any]] = []
        for name in sorted(financials.get("sources", {})):
            bucket = financials["sources"][name]
            donations = float(bucket.get("donations", 0.0))
            disbursed = float(bucket.get("disbursed", 0.0))
            balance = float(bucket.get("balance", donations - disbursed))
            connections.append(
                {
                    "source": name,
                    "donations": round(donations, 2),
                    "disbursed": round(disbursed, 2),
                    "balance": round(balance, 2),
                    "donation_share": self._share(donations, total_donations),
                    "disbursement_share": self._share(disbursed, total_disbursed),
                }
            )
        return connections

    @staticmethod
    def _share(value: float, total: float) -> float:
        if total == 0:
            return 0.0
        return round(value / total, 4)

    # ------------------------------------------------------------------
    # Integration helpers

    def _summarise_integrations(
        self, operations: dict[str, Any], financials: dict[str, Any]
    ) -> list[dict[str, Any]]:
        names = operations.get("sustainability", {}).get("recurring_donation_integrations", [])
        events = financials.get("events", [])
        integrations: list[dict[str, Any]] = []
        for name in names:
            status = "observed" if self._integration_observed(name, events) else "declared"
            integrations.append({"name": name, "status": status})
        return integrations

    @staticmethod
    def _integration_observed(name: str, events: Iterable[dict[str, Any]]) -> bool:
        target = name.lower()
        for event in events:
            for field in ("source", "memo", "asset"):
                value = event.get(field)
                if isinstance(value, str) and target in value.lower():
                    return True
        return False

    # ------------------------------------------------------------------
    # Issue helpers

    @staticmethod
    def _detect_issues(
        financials: dict[str, Any],
        connections: list[dict[str, Any]],
        integrations: list[dict[str, Any]],
    ) -> list[str]:
        issues: list[str] = []
        if not connections:
            issues.append("No financial event sources available for verification.")
        if not integrations:
            issues.append("No recurring donation integration metadata found.")

        balance = float(financials.get("totals", {}).get("balance", 0.0) or 0.0)
        if balance < 0:
            issues.append("Aggregate treasury balance is negative; investigate disbursement coverage.")
        return issues


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify recorded financial connections and recurring donation integrations."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root (defaults to current working directory).",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the verification report for human review.",
    )
    args = parser.parse_args()

    verifier = FinancialIntegrationVerifier(project_root=args.root)
    report = verifier.verify()
    if args.pretty:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report))


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()


__all__ = ["FinancialIntegrationVerifier", "main"]

