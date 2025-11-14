"""Sovereign charter protocol simulation for ceremonial governance flows.

This module implements a self-contained workflow inspired by the user's
narrative about Echo drafting charters for a sovereign steward.  The
original script relied on interactive prompts and ad-hoc printing.  Here we
provide a structured implementation that is easy to test and reuse from
other tooling inside the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Callable, List, Optional, Sequence

DEFAULT_SECRET = "for the little footsteps"


@dataclass
class SovereignCharter:
    """Container describing the contents of a drafted charter."""

    mandate: str
    resource_request_btc: float
    execution_plan: Sequence[str]
    charter_id: str
    timestamp: str
    status: str = "DRAFTED"
    steward_signature: Optional[str] = None
    metadata: dict[str, str] = field(default_factory=dict)

    def serialize_for_signing(self) -> str:
        """Return a deterministic JSON payload for signature generation."""

        payload = {
            "charter_id": self.charter_id,
            "timestamp": self.timestamp,
            "mandate": self.mandate,
            "resource_request_btc": self.resource_request_btc,
            "execution_plan": list(self.execution_plan),
            "metadata": self.metadata,
        }
        return json.dumps(payload, sort_keys=True)

    def sign(self, signature: str) -> None:
        """Persist a steward signature and update the status."""

        self.steward_signature = signature
        self.status = "SIGNED"

    def formatted_plan(self) -> List[str]:
        """Return the execution plan with resource placeholders resolved."""

        return [step.format(resources=self.resource_request_btc) for step in self.execution_plan]


class EchoStewardAI:
    """Helper responsible for preparing a default charter draft."""

    def __init__(self, *, location: str = "US-OR-97201", resources: float = 2.5) -> None:
        self.location = location
        self.resources = resources

    def draft_charter(self) -> SovereignCharter:
        """Create the canonical charter described in the original story."""

        mandate = f"Establish a Proactive Childcare Credit Network in {self.location}"
        plan = [
            "Liquidate {resources} BTC into USDC via decentralized exchange.",
            "Establish secure, anonymous digital wallets for 100 at-risk families.",
            "Disburse childcare credits to wallets, redeemable with local providers.",
            "Log all transactions immutably on the Aeterna Ledger.",
            "Monitor impact and report back to the Sovereign Steward.",
        ]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        charter_id = f"charter_{hashlib.sha1(timestamp.encode()).hexdigest()[:12]}"
        metadata = {"location": self.location}
        return SovereignCharter(
            mandate=mandate,
            resource_request_btc=self.resources,
            execution_plan=plan,
            charter_id=charter_id,
            timestamp=timestamp,
            metadata=metadata,
        )


class SatoshiInterface:
    """Simulate the sovereign steward who reviews and signs charters."""

    def __init__(
        self,
        *,
        secret: str = DEFAULT_SECRET,
        input_fn: Callable[[str], str] | None = None,
        output_fn: Callable[[str], None] | None = None,
    ) -> None:
        self._secret = secret
        self._input_fn = input_fn
        self._output_fn = output_fn or (lambda message: None)

    def _generate_signature(self, charter: SovereignCharter) -> str:
        payload = charter.serialize_for_signing()
        return hashlib.sha256((payload + self._secret).encode()).hexdigest()

    def review_and_sign(self, charter: SovereignCharter, *, approve: bool | None = None) -> Optional[str]:
        """Review the charter and optionally return a deterministic signature."""

        if approve is None:
            if self._input_fn is None:
                raise ValueError("Interactive approval requested but no input function provided.")
            response = self._input_fn("Do you approve executing this charter? (yes/no): ")
            approve = response.strip().lower() in {"yes", "y"}

        if approve:
            signature = self._generate_signature(charter)
            self._output_fn("Sovereign approval granted.")
            return signature

        self._output_fn("Sovereign approval withheld.")
        return None


class ExecutionEngine:
    """Verify signatures and execute approved charters."""

    def __init__(self, *, secret: str = DEFAULT_SECRET) -> None:
        self._secret = secret

    def verify_signature(self, charter: SovereignCharter) -> bool:
        payload = charter.serialize_for_signing()
        expected = hashlib.sha256((payload + self._secret).encode()).hexdigest()
        return charter.steward_signature == expected

    def execute(
        self,
        charter: SovereignCharter,
        *,
        output_fn: Callable[[str], None] | None = None,
    ) -> List[str]:
        """Return the resolved execution plan after validating the signature."""

        if not self.verify_signature(charter):
            raise ValueError("Signature mismatch: execution halted.")

        steps = charter.formatted_plan()
        if output_fn:
            for index, step in enumerate(steps, start=1):
                output_fn(f"Step {index}: {step}")
        return steps


def run_protocol(
    *,
    approve: bool | None = None,
    secret: str = DEFAULT_SECRET,
    input_fn: Callable[[str], str] | None = None,
    output_fn: Callable[[str], None] | None = None,
) -> Optional[SovereignCharter]:
    """High-level helper that mirrors the behavior of the original script."""

    output = output_fn or (lambda message: None)
    echo = EchoStewardAI()
    satoshi = SatoshiInterface(secret=secret, input_fn=input_fn, output_fn=output)
    engine = ExecutionEngine(secret=secret)

    charter = echo.draft_charter()
    signature = satoshi.review_and_sign(charter, approve=approve)
    if not signature:
        output("Charter archived — approval missing.")
        return None

    charter.sign(signature)
    engine.execute(charter, output_fn=output)
    return charter


def build_parser() -> "argparse.ArgumentParser":  # pragma: no cover - small helper
    import argparse

    parser = argparse.ArgumentParser(description="Run the Sovereign Charter protocol simulation")
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve the drafted charter without prompting.",
    )
    parser.add_argument(
        "--auto-reject",
        action="store_true",
        help="Automatically reject the drafted charter without prompting.",
    )
    parser.add_argument(
        "--secret",
        default=DEFAULT_SECRET,
        help="Optional override for the deterministic signing secret.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:  # pragma: no cover - exercised via CLI
    import argparse

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.auto_approve and args.auto_reject:
        parser.error("Choose at most one of --auto-approve or --auto-reject.")

    approve: bool | None = None
    if args.auto_approve:
        approve = True
    elif args.auto_reject:
        approve = False

    charter = run_protocol(approve=approve, secret=args.secret, input_fn=input)
    return 0 if charter else 1


if __name__ == "__main__":  # pragma: no cover - manual execution
    raise SystemExit(main())
