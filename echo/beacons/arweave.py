"""Arweave beacon implementation."""

from __future__ import annotations

from pathlib import Path

from echo.beacons.base import BeaconResult


class ArweaveBeacon:
    """Store payloads on the Arweave permaweb."""

    name = "arweave"

    def __init__(self, wallet_path: str | Path) -> None:
        self._wallet_path = Path(wallet_path)
        if not self._wallet_path.exists():
            raise FileNotFoundError(f"Arweave wallet not found at {self._wallet_path}")

    def publish(self, payload: bytes, tag: str) -> BeaconResult:
        try:
            import arweave  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("The 'arweave-python-client' package is required") from exc

        wallet = arweave.Wallet(str(self._wallet_path))
        transaction = arweave.Transaction(wallet, data=payload)
        transaction.add_tag("App-Name", "EchoEye")
        transaction.add_tag("Echo-Tag", tag)
        transaction.add_tag("Content-Type", "application/octet-stream")
        transaction.sign()
        transaction.send()

        return BeaconResult(id=transaction.id, url=f"https://arweave.net/{transaction.id}")

    def fetch(self, tx_id: str) -> bytes:
        import requests

        response = requests.get(f"https://arweave.net/{tx_id}", timeout=30)
        response.raise_for_status()
        return response.content
