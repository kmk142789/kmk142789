"""Lightweight client for retrieving native balances from the Etherscan API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import requests


class EtherscanAPIError(RuntimeError):
    """Raised when the Etherscan API returns an error payload."""


@dataclass(slots=True)
class NativeBalance:
    """Represents the native token balance for a single address in wei."""

    address: str
    balance_wei: int


class EtherscanBalanceClient:
    """Query Etherscan's ``account.balance`` endpoint for native balances."""

    def __init__(
        self,
        api_key: str,
        *,
        chain_id: int = 1,
        base_url: str = "https://api.etherscan.io/v2/api",
        session: requests.Session | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must be a non-empty string")

        self.api_key = api_key
        self.chain_id = chain_id
        self.base_url = base_url
        self._session = session or requests.Session()
        self._owns_session = session is None

    def close(self) -> None:
        """Close the underlying :class:`requests.Session` if owned by the client."""

        if self._owns_session:
            self._session.close()

    def __enter__(self) -> "EtherscanBalanceClient":  # pragma: no cover - trivial
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        self.close()

    def get_native_balances(
        self,
        addresses: Sequence[str] | str,
        *,
        tag: str = "latest",
        timeout: float = 10.0,
    ) -> list[NativeBalance]:
        """Return native balances for ``addresses``.

        Parameters
        ----------
        addresses:
            Single address string or a sequence of addresses (up to 20 entries).
        tag:
            Block tag.  ``"latest"`` retrieves the most recent block height.
        timeout:
            Optional timeout for the HTTP request.
        """

        normalised = self._normalise_addresses(addresses)
        params = {
            "apikey": self.api_key,
            "chainid": str(self.chain_id),
            "module": "account",
            "action": "balance",
            "address": ",".join(normalised),
            "tag": tag,
        }

        response = self._session.get(self.base_url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, dict):
            raise EtherscanAPIError("Unexpected response structure from Etherscan")

        if str(payload.get("status")) != "1":
            message = str(payload.get("message") or "Etherscan API request failed")
            raise EtherscanAPIError(message)

        result = payload.get("result")

        balances: list[NativeBalance]
        if isinstance(result, str):
            balances = [self._build_balance(normalised[0], result)]
        elif isinstance(result, Iterable):
            balances = self._parse_multi_result(result)
        else:
            raise EtherscanAPIError("Etherscan response did not include balance data")

        if len(balances) != len(normalised):
            raise EtherscanAPIError("Etherscan response did not include all requested balances")

        # Preserve requested order where possible by mapping on address.
        balance_map = {balance.address.lower(): balance for balance in balances}
        ordered = []
        for address in normalised:
            key = address.lower()
            if key not in balance_map:
                raise EtherscanAPIError("Etherscan response missing balance for an address")
            ordered.append(balance_map[key])
        return ordered

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _normalise_addresses(addresses: Sequence[str] | str) -> list[str]:
        if isinstance(addresses, str):
            address_list = [addresses.strip()]
        else:
            address_list = [str(addr).strip() for addr in addresses]

        address_list = [addr for addr in address_list if addr]
        if not address_list:
            raise ValueError("addresses must contain at least one non-empty value")
        if len(address_list) > 20:
            raise ValueError("Etherscan API allows up to 20 addresses per request")
        return address_list

    @staticmethod
    def _build_balance(address: str, raw_balance: str) -> NativeBalance:
        try:
            balance_int = int(str(raw_balance), 10)
        except ValueError as exc:  # pragma: no cover - defensive
            raise EtherscanAPIError(f"Invalid balance value for {address}") from exc
        return NativeBalance(address=address, balance_wei=balance_int)

    def _parse_multi_result(self, result: Iterable[object]) -> list[NativeBalance]:
        balances: list[NativeBalance] = []
        for entry in result:
            if not isinstance(entry, dict):
                raise EtherscanAPIError("Etherscan returned unexpected data for multi-address query")
            address = str(entry.get("account") or entry.get("address") or "").strip()
            raw_balance = entry.get("balance")
            if not address or raw_balance is None:
                raise EtherscanAPIError("Etherscan returned incomplete balance information")
            balances.append(self._build_balance(address, str(raw_balance)))
        return balances


__all__ = ["EtherscanAPIError", "EtherscanBalanceClient", "NativeBalance"]
