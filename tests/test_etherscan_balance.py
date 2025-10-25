from __future__ import annotations

import pytest

from echo.tools.etherscan_balance import (
    EtherscanAPIError,
    EtherscanBalanceClient,
    NativeBalance,
)


class StubResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> object:
        return self._payload


class StubSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []
        self.responses: list[StubResponse] = []

    def queue(self, payload: object, status_code: int = 200) -> None:
        self.responses.append(StubResponse(payload, status_code=status_code))

    def get(self, url: str, *, params: dict[str, str], timeout: float) -> StubResponse:
        self.calls.append((url, params))
        if not self.responses:
            raise AssertionError("No queued response available")
        return self.responses.pop(0)

    def close(self) -> None:  # pragma: no cover - included for interface parity
        pass


def test_single_address_balance_parses_result() -> None:
    session = StubSession()
    session.queue({"status": "1", "message": "OK", "result": "123"})
    client = EtherscanBalanceClient("test-key", session=session)

    balances = client.get_native_balances("0xabc")

    assert balances == [NativeBalance(address="0xabc", balance_wei=123)]
    assert session.calls[0][1]["address"] == "0xabc"


def test_multiple_address_balance_preserves_order() -> None:
    session = StubSession()
    session.queue(
        {
            "status": "1",
            "message": "OK",
            "result": [
                {"account": "0xSecond", "balance": "2"},
                {"account": "0xFirst", "balance": "1"},
            ],
        }
    )
    client = EtherscanBalanceClient("test-key", session=session)

    balances = client.get_native_balances(["0xFirst", "0xSecond"])

    assert balances == [
        NativeBalance(address="0xFirst", balance_wei=1),
        NativeBalance(address="0xSecond", balance_wei=2),
    ]


def test_rejects_empty_addresses() -> None:
    client = EtherscanBalanceClient("test-key", session=StubSession())
    with pytest.raises(ValueError):
        client.get_native_balances([])


def test_raises_for_api_error_status() -> None:
    session = StubSession()
    session.queue({"status": "0", "message": "NOTOK", "result": "0"})
    client = EtherscanBalanceClient("test-key", session=session)

    with pytest.raises(EtherscanAPIError) as excinfo:
        client.get_native_balances("0xabc")

    assert "NOTOK" in str(excinfo.value)


def test_missing_balance_entry_triggers_error() -> None:
    session = StubSession()
    session.queue(
        {"status": "1", "message": "OK", "result": [{"account": "0xabc"}]}
    )
    client = EtherscanBalanceClient("test-key", session=session)

    with pytest.raises(EtherscanAPIError):
        client.get_native_balances(["0xabc"])
