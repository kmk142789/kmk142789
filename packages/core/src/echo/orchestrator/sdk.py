"""SDK wrapper around the proof orchestrator service."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Sequence

from .proof_service import (
    NetworkConfig,
    ProofOrchestratorService,
    SubmissionStatus,
    VerifiableCredential,
    WalletSigner,
)


class ProofOrchestratorClient:
    """Convenience client for programmatic access to the orchestrator service."""

    def __init__(
        self,
        *,
        state_dir: Path | str = Path("state/proof_orchestrator"),
        service: ProofOrchestratorService | None = None,
    ) -> None:
        self._service = service or ProofOrchestratorService(state_dir)

    def submit(
        self,
        credentials: Iterable[Mapping[str, object] | VerifiableCredential],
        *,
        scheme: str = "zk-snark",
        networks: Sequence[NetworkConfig] | None = None,
        signers: Mapping[str, WalletSigner] | None = None,
    ) -> SubmissionStatus:
        """Submit credentials for aggregation and dispatch."""

        return self._service.submit_proof(
            credentials,
            scheme=scheme,
            networks=networks,
            signers=signers,
        )

    def status(self, submission_id: str):
        """Return stored status for the given submission identifier."""

        return self._service.query_status(submission_id)

    def history(self, limit: int | None = None):
        """Return a list of recent submission records."""

        return self._service.list_statuses(limit)

    def pending(self):
        """Return pending fallback file paths for offline processing."""

        return self._service.pending_fallbacks()


__all__ = ["ProofOrchestratorClient"]
