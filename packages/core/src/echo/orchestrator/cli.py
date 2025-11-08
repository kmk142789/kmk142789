"""Command-line interface for the proof orchestrator service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import typer

from .proof_service import (
    NetworkConfig,
    ProofOrchestratorService,
    Secp256k1Wallet,
    Ed25519Wallet,
)


app = typer.Typer(add_completion=False, help="Coordinate verifiable credential proof submissions")


def _load_credentials(paths: Iterable[Path]) -> list[dict]:
    credentials: list[dict] = []
    for path in paths:
        with Path(path).expanduser().open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            credentials.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            credentials.append(payload)
        else:
            raise typer.BadParameter(f"Credential file {path} must contain an object or list of objects")
    if not credentials:
        raise typer.BadParameter("No credentials were loaded from the provided sources")
    return credentials


def _parse_network(option: str) -> NetworkConfig:
    parts = option.split(":")
    if len(parts) not in {2, 3}:
        raise typer.BadParameter("Network must be formatted as name:chain_id[:protocol]")
    name, chain_id, *rest = parts
    protocol = rest[0] if rest else "generic"
    return NetworkConfig(name=name, chain_id=chain_id, protocol=protocol)


def _parse_key(option: str, wallet_cls):
    if "=" not in option:
        raise typer.BadParameter("Key arguments must be formatted as network=hexkey")
    network, hex_value = option.split("=", 1)
    try:
        wallet = wallet_cls.from_private_key_hex(hex_value)
    except ValueError as exc:  # pragma: no cover - propagated for user clarity
        raise typer.BadParameter(str(exc)) from exc
    return network, wallet


@app.command()
def submit(
    credentials: list[Path] = typer.Option(..., "--credential", exists=True, readable=True, help="Path to a VC JSON file"),
    scheme: str = typer.Option("zk-snark", help="Proof aggregation scheme (zk-snark or bbs+)"),
    network: list[str] = typer.Option([], "--network", help="Target network in the form name:chain_id[:protocol]"),
    secp_key: list[str] = typer.Option([], "--secp-key", help="Network signer in the form network=hexkey"),
    ed25519_key: list[str] = typer.Option([], "--ed25519-key", help="Network signer in the form network=hexkey"),
    state_dir: Path = typer.Option(Path("state/proof_orchestrator"), help="Directory used for orchestrator state"),
) -> None:
    """Submit credentials for aggregated proof generation and dispatch."""

    service = ProofOrchestratorService(state_dir)
    credential_payloads = _load_credentials(credentials)

    networks = [_parse_network(item) for item in network]

    signers = {}
    for item in secp_key:
        net, wallet = _parse_key(item, Secp256k1Wallet)
        signers[net] = wallet
    for item in ed25519_key:
        net, wallet = _parse_key(item, Ed25519Wallet)
        signers[net] = wallet

    submission = service.submit_proof(
        credential_payloads,
        scheme=scheme,
        networks=networks,
        signers=signers,
    )

    typer.echo(json.dumps(submission.to_dict(), indent=2))


@app.command()
def status(
    submission_id: str = typer.Argument(..., help="Submission identifier returned by the submit command"),
    state_dir: Path = typer.Option(Path("state/proof_orchestrator"), help="Directory used for orchestrator state"),
) -> None:
    """Display the status of a previously submitted aggregated proof."""

    service = ProofOrchestratorService(state_dir)
    record = service.query_status(submission_id)
    if not record:
        raise typer.Exit(code=1)
    typer.echo(json.dumps(record, indent=2))


@app.command("list")
def list_status(
    limit: int = typer.Option(10, help="Number of historical submissions to display"),
    state_dir: Path = typer.Option(Path("state/proof_orchestrator"), help="Directory used for orchestrator state"),
) -> None:
    """List recent submissions stored by the orchestrator."""

    service = ProofOrchestratorService(state_dir)
    records = service.list_statuses(limit)
    typer.echo(json.dumps(records, indent=2))


def main() -> None:
    """Entrypoint for console script registration."""

    app()


__all__ = ["app", "main"]
