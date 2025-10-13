"""Shared state for the Echo API surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Protocol


class ReceiptsProtocol(Protocol):
    def tip(self) -> str: ...

    def height(self, tip: str) -> int: ...

    def commit(self, action: str, payload: dict[str, Any]) -> None: ...


class DagProtocol(Protocol):
    def merkle_root(self, heads: Iterable[str]) -> str: ...


@dataclass
class _NullReceipts:
    def tip(self) -> str:
        return "0x0"

    def height(self, tip: str) -> int:  # pragma: no cover - trivial
        return 0

    def commit(self, action: str, payload: dict[str, Any]) -> None:  # pragma: no cover
        pass


@dataclass
class _NullDag:
    def merkle_root(self, heads: Iterable[str]) -> str:  # pragma: no cover - trivial
        return "cid_0"


def _default_session_heads() -> list[str]:  # pragma: no cover - trivial
    return []


receipts: ReceiptsProtocol = _NullReceipts()
dag: DagProtocol = _NullDag()
_session_heads: Callable[[], Iterable[str]] = _default_session_heads


def set_receipts(instance: ReceiptsProtocol) -> None:
    global receipts
    receipts = instance


def set_dag(instance: DagProtocol) -> None:
    global dag
    dag = instance


def set_session_heads(factory: Callable[[], Iterable[str]]) -> None:
    global _session_heads
    _session_heads = factory


def session_heads() -> Iterable[str]:
    return list(_session_heads())


__all__ = [
    "receipts",
    "dag",
    "session_heads",
    "set_receipts",
    "set_dag",
    "set_session_heads",
]
