from decimal import Decimal
from datetime import datetime, timedelta, timezone

from token_system import (
    LockNotFoundError,
    TokenAllocation,
    TokenMetadata,
    TokenSystem,
    InsufficientBalanceError,
)


def build_system() -> TokenSystem:
    metadata = TokenMetadata(
        name="Echo Sovereign Token",
        symbol="EST",
        decimals=18,
        chain="Polygon",
        policy_notes="Utility + reputation hybrid with audited supply controls.",
    )
    allocations = [
        TokenAllocation(account="community", amount=Decimal("1000"), purpose="Community reserve"),
        TokenAllocation(account="treasury", amount=Decimal("500"), purpose="Treasury boot"),
    ]
    return TokenSystem(metadata=metadata, allocations=allocations)


def test_initial_allocations_are_minted() -> None:
    system = build_system()
    snapshot = system.snapshot()
    assert snapshot.total_minted == Decimal("1500")
    assert snapshot.circulating_supply == Decimal("1500")
    assert snapshot.balances["community"] == Decimal("1000")
    assert snapshot.balances["treasury"] == Decimal("500")


def test_transfer_and_burn_adjust_supply() -> None:
    system = build_system()
    system.transfer("community", "treasury", Decimal("200"), memo="Growth grant")
    system.burn("treasury", 100, memo="Retire excess")
    snapshot = system.snapshot()
    assert snapshot.total_burned == Decimal("100")
    assert snapshot.circulating_supply == Decimal("1400")
    assert snapshot.balances["community"] == Decimal("800")
    assert snapshot.balances["treasury"] == Decimal("600")


def test_locks_reduce_available_balance_until_released() -> None:
    system = build_system()
    lock = system.apply_lock("community", 300, reason="Vesting", release_at=datetime.now(timezone.utc) + timedelta(days=30))
    assert system.locked_balance("community") == Decimal("300")
    assert system.available_balance("community") == Decimal("700")
    released = system.release_lock(lock.lock_id)
    assert released.lock_id == lock.lock_id
    assert system.locked_balance("community") == Decimal("0")
    assert system.available_balance("community") == Decimal("1000")


def test_lock_release_raises_for_unknown_id() -> None:
    system = build_system()
    try:
        system.release_lock("LOCK-UNKNOWN")
    except LockNotFoundError:
        pass
    else:  # pragma: no cover - guard to ensure exception raised
        raise AssertionError("Expected LockNotFoundError")


def test_transfers_and_burns_respect_available_balance() -> None:
    system = build_system()
    system.apply_lock("community", 900, reason="Treasury safeguard")
    try:
        system.transfer("community", "treasury", 200)
    except InsufficientBalanceError:
        pass
    else:  # pragma: no cover
        raise AssertionError("Expected InsufficientBalanceError for transfer")
    try:
        system.burn("community", 200)
    except InsufficientBalanceError:
        pass
    else:  # pragma: no cover
        raise AssertionError("Expected InsufficientBalanceError for burn")
