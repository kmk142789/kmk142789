"""Minimal but well-typed scaffolding for a programmable token system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Iterable, Literal, Mapping, MutableMapping, Sequence
from uuid import uuid4

TokenEventKind = Literal["mint", "burn", "transfer"]


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    """Normalise numeric inputs to :class:`~decimal.Decimal`."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True)
class TokenMetadata:
    """Static properties describing the token."""

    name: str
    symbol: str
    decimals: int
    chain: str
    policy_notes: str

    def summary(self) -> str:
        return (
            f"{self.name} ({self.symbol}) · chain={self.chain} · "
            f"decimals={self.decimals}: {self.policy_notes}"
        )


@dataclass(frozen=True)
class TokenAllocation:
    """Declarative initial allocation entry."""

    account: str
    amount: Decimal
    purpose: str
    vesting_terms: str | None = None


@dataclass(frozen=True)
class TokenEvent:
    """Ledger entry representing a mutation of balances."""

    seq: int
    timestamp: datetime
    kind: TokenEventKind
    amount: Decimal
    source: str | None
    destination: str | None
    memo: str
    reference: Mapping[str, str]


@dataclass(frozen=True)
class TokenLock:
    """Represents temporarily restricted tokens for an account."""

    lock_id: str
    account: str
    amount: Decimal
    reason: str
    created_at: datetime
    release_at: datetime | None = None


@dataclass(frozen=True)
class TokenSupplySnapshot:
    """High-level summary of the token system at a point in time."""

    total_minted: Decimal
    total_burned: Decimal
    circulating_supply: Decimal
    balances: Mapping[str, Decimal]
    locked_balances: Mapping[str, Decimal]


class TokenLedger:
    """Append-only ledger for token events."""

    def __init__(self) -> None:
        self._events: list[TokenEvent] = []

    def record(
        self,
        *,
        kind: TokenEventKind,
        amount: Decimal,
        source: str | None,
        destination: str | None,
        memo: str,
        reference: Mapping[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> TokenEvent:
        if amount <= Decimal("0"):
            raise ValueError("Token events must have a positive amount")
        seq = len(self._events) + 1
        event = TokenEvent(
            seq=seq,
            timestamp=timestamp or datetime.now(tz=UTC),
            kind=kind,
            amount=amount,
            source=source,
            destination=destination,
            memo=memo,
            reference=dict(reference or {}),
        )
        self._events.append(event)
        return event

    def events(self) -> Sequence[TokenEvent]:
        return tuple(self._events)

    def balance(self, account: str) -> Decimal:
        total = Decimal("0")
        for event in self._events:
            if event.destination == account:
                total += event.amount
            if event.source == account:
                total -= event.amount
        return total

    def accounts(self) -> Sequence[str]:
        seen: set[str] = set()
        for event in self._events:
            if event.source:
                seen.add(event.source)
            if event.destination:
                seen.add(event.destination)
        return tuple(sorted(seen))

    @property
    def total_minted(self) -> Decimal:
        return sum((event.amount for event in self._events if event.kind == "mint"), Decimal("0"))

    @property
    def total_burned(self) -> Decimal:
        return sum((event.amount for event in self._events if event.kind == "burn"), Decimal("0"))


class InsufficientBalanceError(RuntimeError):
    """Raised when a transfer attempts to move more than the unlocked balance."""


class LockNotFoundError(RuntimeError):
    """Raised when a lock identifier does not exist."""


class TokenSystem:
    """High-level orchestrator for a programmable token model."""

    def __init__(
        self,
        metadata: TokenMetadata,
        allocations: Iterable[TokenAllocation] | None = None,
    ) -> None:
        self.metadata = metadata
        self._ledger = TokenLedger()
        self._locks: MutableMapping[str, TokenLock] = {}
        if allocations:
            for allocation in allocations:
                self.mint(
                    allocation.account,
                    allocation.amount,
                    memo=allocation.purpose,
                    reference={"vesting": allocation.vesting_terms or "immediate"},
                )

    # ------------------------------------------------------------------
    # Balance helpers
    # ------------------------------------------------------------------
    def balance(self, account: str) -> Decimal:
        return self._ledger.balance(account)

    def locked_balance(self, account: str) -> Decimal:
        return sum(
            (lock.amount for lock in self._locks.values() if lock.account == account),
            Decimal("0"),
        )

    def available_balance(self, account: str) -> Decimal:
        return self.balance(account) - self.locked_balance(account)

    def circulating_supply(self) -> Decimal:
        return self._ledger.total_minted - self._ledger.total_burned

    # ------------------------------------------------------------------
    # Core actions
    # ------------------------------------------------------------------
    def mint(
        self,
        account: str,
        amount: Decimal | int | float | str,
        *,
        memo: str = "Mint",
        reference: Mapping[str, str] | None = None,
    ) -> TokenEvent:
        amount_decimal = _to_decimal(amount)
        return self._ledger.record(
            kind="mint",
            amount=amount_decimal,
            source=None,
            destination=account,
            memo=memo,
            reference=reference,
        )

    def burn(
        self,
        account: str,
        amount: Decimal | int | float | str,
        *,
        memo: str = "Burn",
        reference: Mapping[str, str] | None = None,
    ) -> TokenEvent:
        amount_decimal = _to_decimal(amount)
        if self.available_balance(account) < amount_decimal:
            raise InsufficientBalanceError(f"Account {account} does not have enough unlocked tokens to burn")
        return self._ledger.record(
            kind="burn",
            amount=amount_decimal,
            source=account,
            destination=None,
            memo=memo,
            reference=reference,
        )

    def transfer(
        self,
        source: str,
        destination: str,
        amount: Decimal | int | float | str,
        *,
        memo: str = "Transfer",
        reference: Mapping[str, str] | None = None,
    ) -> TokenEvent:
        if source == destination:
            raise ValueError("Transfers require distinct source and destination accounts")
        amount_decimal = _to_decimal(amount)
        if self.available_balance(source) < amount_decimal:
            raise InsufficientBalanceError(
                f"Account {source} does not have enough unlocked tokens to transfer"
            )
        return self._ledger.record(
            kind="transfer",
            amount=amount_decimal,
            source=source,
            destination=destination,
            memo=memo,
            reference=reference,
        )

    # ------------------------------------------------------------------
    # Locks
    # ------------------------------------------------------------------
    def apply_lock(
        self,
        account: str,
        amount: Decimal | int | float | str,
        *,
        reason: str,
        release_at: datetime | None = None,
    ) -> TokenLock:
        amount_decimal = _to_decimal(amount)
        if self.available_balance(account) < amount_decimal:
            raise InsufficientBalanceError(
                f"Account {account} does not have enough unlocked tokens to lock"
            )
        lock_id = f"LOCK-{uuid4().hex[:10].upper()}"
        lock = TokenLock(
            lock_id=lock_id,
            account=account,
            amount=amount_decimal,
            reason=reason,
            created_at=datetime.now(tz=UTC),
            release_at=release_at,
        )
        self._locks[lock_id] = lock
        return lock

    def release_lock(self, lock_id: str) -> TokenLock:
        lock = self._locks.pop(lock_id, None)
        if lock is None:
            raise LockNotFoundError(f"Lock {lock_id} does not exist")
        return lock

    def active_locks(self) -> Sequence[TokenLock]:
        return tuple(self._locks.values())

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def snapshot(self) -> TokenSupplySnapshot:
        balances: MutableMapping[str, Decimal] = {
            account: self.balance(account) for account in self._ledger.accounts()
        }
        locked: MutableMapping[str, Decimal] = {
            account: self.locked_balance(account) for account in balances
        }
        return TokenSupplySnapshot(
            total_minted=self._ledger.total_minted,
            total_burned=self._ledger.total_burned,
            circulating_supply=self.circulating_supply(),
            balances=balances,
            locked_balances=locked,
        )
