"""Build the transparency payload rendered on the Pulse dashboard."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

WEI_PER_ETHER = 10**18


@dataclass(frozen=True, slots=True)
class ImpactPaths:
    """Filesystem layout used by :class:`PublicImpactExplorer`."""

    root: Path

    def ledger(self) -> Path:
        return self.root / "ledger" / "nonprofit_bank_ledger.json"

    def treasury_policy(self) -> Path:
        return self.root / "state" / "nonprofit_treasury_policy.json"

    def childcare_metrics(self) -> Path:
        return self.root / "reports" / "data" / "childcare_impact_metrics.json"

    def parent_council(self) -> Path:
        return self.root / "state" / "parent_advisory_council.json"

    def provider_feedback(self) -> Path:
        return self.root / "state" / "provider_feedback_loop.json"


@dataclass(frozen=True)
class LedgerEntry:
    """Normalised ledger entry for deposits and payouts."""

    type: str
    amount_wei: int
    tx_hash: str
    actor: str
    timestamp: int

    @property
    def is_deposit(self) -> bool:
        return self.type == "deposit"

    @property
    def amount_eth(self) -> float:
        return round(self.amount_wei / WEI_PER_ETHER, 6)

    def signed_amount(self) -> int:
        return self.amount_wei if self.is_deposit else -self.amount_wei

    def timeline_row(self, running_balance: int) -> dict[str, Any]:
        return {
            "timestamp": _epoch_to_iso(self.timestamp),
            "type": self.type,
            "actor": self.actor,
            "amount_wei": self.amount_wei,
            "amount_eth": self.amount_eth,
            "balance_wei": running_balance,
            "balance_eth": round(running_balance / WEI_PER_ETHER, 6),
            "tx_hash": self.tx_hash,
        }


class PublicImpactExplorer:
    """Compose treasury, childcare impact, and stakeholder signals."""

    def __init__(self, root: Path | str | None = None) -> None:
        self._paths = ImpactPaths(root=Path(root or Path.cwd()).resolve())

    def build(self) -> dict[str, Any]:
        """Return a serialisable snapshot for the dashboard."""

        stakeholder_voice = self._stakeholder_voice()
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "treasury": self._treasury_snapshot(),
            "impact_metrics": self._childcare_metrics(),
            "stakeholder_voice": stakeholder_voice,
            "upcoming_engagements": self._engagements(stakeholder_voice),
        }

    # ------------------------------------------------------------------
    # Treasury snapshot
    # ------------------------------------------------------------------

    def _treasury_snapshot(self) -> dict[str, Any]:
        entries = self._ledger_entries()
        deposits = [entry for entry in entries if entry.is_deposit]
        payouts = [entry for entry in entries if not entry.is_deposit]

        total_deposits = sum(item.amount_wei for item in deposits)
        total_payouts = sum(item.amount_wei for item in payouts)
        balance_wei = total_deposits - total_payouts

        timeline: list[dict[str, Any]] = []
        running_balance = 0
        for entry in entries:
            running_balance += entry.signed_amount()
            timeline.append(entry.timeline_row(running_balance))

        ledger_snapshot = {
            "total_deposits_wei": total_deposits,
            "total_payouts_wei": total_payouts,
            "balance_wei": balance_wei,
            "balance_eth": round(balance_wei / WEI_PER_ETHER, 6),
            "total_deposits_eth": round(total_deposits / WEI_PER_ETHER, 6),
            "total_payouts_eth": round(total_payouts / WEI_PER_ETHER, 6),
            "deposit_count": len(deposits),
            "payout_count": len(payouts),
            "donor_addresses": sorted({entry.actor for entry in deposits}),
            "payout_addresses": sorted({entry.actor for entry in payouts}),
            "donor_count": len({entry.actor for entry in deposits}),
            "payout_recipient_count": len({entry.actor for entry in payouts}),
            "last_deposit_at": _epoch_to_iso(
                max((entry.timestamp for entry in deposits), default=None)
            ),
            "last_payout_at": _epoch_to_iso(
                max((entry.timestamp for entry in payouts), default=None)
            ),
            "timeline": timeline,
        }

        policy_snapshot = self._treasury_policy()
        return {"ledger": ledger_snapshot, "policy": policy_snapshot}

    def _ledger_entries(self) -> list[LedgerEntry]:
        payload = _load_json(self._paths.ledger())
        if not isinstance(payload, Iterable):
            return []

        entries: list[LedgerEntry] = []
        for raw in payload:
            if not isinstance(raw, Mapping):
                continue
            try:
                entry = LedgerEntry(
                    type=str(raw["type"]).lower(),
                    amount_wei=int(raw["amount_wei"]),
                    tx_hash=str(raw.get("tx_hash", "")),
                    actor=str(raw.get("actor", "")),
                    timestamp=int(raw.get("timestamp", 0)),
                )
            except (KeyError, TypeError, ValueError):
                continue
            entries.append(entry)
        entries.sort(key=lambda item: item.timestamp)
        return entries

    def _treasury_policy(self) -> dict[str, Any]:
        policy = _load_json(self._paths.treasury_policy())
        if not isinstance(policy, Mapping):
            return {
                "targets": [],
                "current_reserves": [],
                "diversity_score": None,
                "emergency_reserve": {},
                "yield_programs": [],
                "runway_weeks": None,
            }

        targets = _normalise_targets(policy.get("stablecoin_targets", []))
        reserves, total_reserves = _normalise_reserves(policy.get("current_reserves", {}))

        allocations = []
        deviation = 0.0
        for target in targets:
            reserve = next((item for item in reserves if item["symbol"] == target["symbol"]), None)
            amount = reserve["amount_usd"] if reserve else 0.0
            actual_pct = (amount / total_reserves) if total_reserves else 0.0
            delta = target["target_pct"] - actual_pct
            deviation += abs(delta)
            allocations.append(
                {
                    "symbol": target["symbol"],
                    "target_pct": round(target["target_pct"] * 100, 2),
                    "actual_pct": round(actual_pct * 100, 2),
                    "delta_pct": round(delta * 100, 2),
                    "action": "increase" if delta > 0.01 else "decrease" if delta < -0.01 else "hold",
                    "amount_usd": amount,
                }
            )

        emergency_raw = policy.get("emergency_reserve", {})
        emergency = _emergency_snapshot(emergency_raw, total_reserves)

        try:
            burn = float(policy.get("operating_burn_usd_weekly", 0))
        except (TypeError, ValueError):
            burn = 0.0
        runway = (total_reserves / burn) if burn else None

        return {
            "updated_at": policy.get("updated_at"),
            "targets": allocations,
            "current_reserves": reserves,
            "total_reserves_usd": total_reserves,
            "diversity_score": round(max(0.0, 100.0 - deviation * 100), 2),
            "emergency_reserve": emergency,
            "yield_programs": [
                item for item in policy.get("yield_programs", []) if isinstance(item, Mapping)
            ],
            "runway_weeks": round(runway, 2) if runway is not None else None,
            "auto_balance_rules": policy.get("auto_balance_rules", {}),
            "notes": policy.get("notes"),
        }

    # ------------------------------------------------------------------
    # Childcare impact metrics
    # ------------------------------------------------------------------

    def _childcare_metrics(self) -> dict[str, Any]:
        metrics = _load_json(self._paths.childcare_metrics())
        if not isinstance(metrics, Mapping):
            return {
                "totals": {},
                "current_cycle": {},
                "history": [],
                "trend": {},
                "equity_breakdown": {},
                "data_sources": [],
            }

        history = [item for item in metrics.get("history", []) if isinstance(item, Mapping)]
        history.sort(key=lambda item: str(item.get("period")))
        trend = _calculate_trend(history)

        return {
            "last_updated": metrics.get("last_updated"),
            "totals": metrics.get("totals", {}),
            "current_cycle": metrics.get("current_cycle", {}),
            "history": history[-8:],
            "trend": trend,
            "equity_breakdown": metrics.get("equity_breakdown", {}),
            "data_sources": metrics.get("data_sources", []),
        }

    # ------------------------------------------------------------------
    # Stakeholder engagement
    # ------------------------------------------------------------------

    def _stakeholder_voice(self) -> dict[str, Any]:
        parent = _load_json(self._paths.parent_council()) or {}
        provider = _load_json(self._paths.provider_feedback()) or {}
        return {
            "parent_advisory_council": parent,
            "provider_feedback_loop": provider,
        }

    def _engagements(self, voice: Mapping[str, Any]) -> list[dict[str, Any]]:
        engagements: list[dict[str, Any]] = []

        council = voice.get("parent_advisory_council", {}) if isinstance(voice, Mapping) else {}
        if isinstance(council, Mapping):
            cadence = council.get("meeting_cadence", {})
            next_session = cadence.get("next_session") if isinstance(cadence, Mapping) else None
            when = _parse_iso(next_session) if next_session else None
            if when:
                engagements.append(
                    {
                        "name": "Parent Advisory Council",
                        "scheduled_for": when.isoformat(),
                        "context": cadence.get("location") if isinstance(cadence, Mapping) else None,
                    }
                )

        provider = voice.get("provider_feedback_loop", {}) if isinstance(voice, Mapping) else {}
        if isinstance(provider, Mapping):
            office_hours = provider.get("office_hours", {})
            next_session = office_hours.get("next_session") if isinstance(office_hours, Mapping) else None
            when = _parse_iso(next_session) if next_session else None
            if when:
                engagements.append(
                    {
                        "name": "Provider Office Hours",
                        "scheduled_for": when.isoformat(),
                        "context": office_hours.get("host") if isinstance(office_hours, Mapping) else None,
                    }
                )

        engagements.sort(key=lambda item: item.get("scheduled_for", ""))
        return engagements


def _load_json(path: Path) -> Mapping[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _epoch_to_iso(value: int | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (OSError, OverflowError, ValueError):
        return None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        cleaned = value.replace("Z", "+00:00") if isinstance(value, str) else value
        return datetime.fromisoformat(cleaned)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _calculate_trend(history: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    sequence = list(history)
    if len(sequence) < 2:
        return {}
    latest = sequence[-1]
    previous = sequence[-2]

    metrics = [
        "families_served",
        "hours_of_childcare",
        "job_placements",
        "caregiver_wages_paid_usd",
    ]

    trend: dict[str, Any] = {}
    for field in metrics:
        latest_value = _safe_float(latest.get(field))
        previous_value = _safe_float(previous.get(field))
        if latest_value is None or previous_value is None:
            continue
        change = latest_value - previous_value
        pct_change = (change / previous_value * 100) if previous_value else None
        trend[field] = {
            "latest": latest_value,
            "previous": previous_value,
            "change": round(change, 2),
            "pct_change": round(pct_change, 2) if pct_change is not None else None,
        }
    return trend


def _normalise_targets(payload: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, Mapping):
            continue
        try:
            pct = float(raw.get("target_pct", 0))
        except (TypeError, ValueError):
            pct = 0.0
        if pct > 1:
            pct /= 100
        targets.append(
            {
                "symbol": str(raw.get("symbol", "")),
                "target_pct": pct,
                "network": raw.get("network"),
                "notes": raw.get("notes"),
            }
        )
    return targets


def _normalise_reserves(payload: Mapping[str, Any]) -> tuple[list[dict[str, Any]], float]:
    reserves: list[dict[str, Any]] = []
    total = 0.0
    for symbol, raw in payload.items():
        if not isinstance(raw, Mapping):
            continue
        try:
            amount = float(raw.get("amount_usd", 0))
        except (TypeError, ValueError):
            amount = 0.0
        total += amount
        reserves.append(
            {
                "symbol": symbol,
                "amount_usd": amount,
                "custodian": raw.get("custodian"),
                "addresses": raw.get("addresses", []),
            }
        )
    return reserves, total


def _emergency_snapshot(raw: Mapping[str, Any], total_reserves: float) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {}
    try:
        target_ratio = float(raw.get("target_ratio", 0))
    except (TypeError, ValueError):
        target_ratio = 0.0
    try:
        current_usd = float(raw.get("current_usd", 0))
    except (TypeError, ValueError):
        current_usd = 0.0
    current_ratio = (current_usd / total_reserves) if total_reserves else 0.0
    return {
        "target_ratio": round(target_ratio, 4),
        "current_ratio": round(current_ratio, 4),
        "current_usd": current_usd,
        "status": "meets_target" if current_ratio >= target_ratio else "below_target",
        "multisig_threshold": raw.get("multisig_threshold"),
        "vault": raw.get("vault"),
        "guardians": raw.get("guardians", []),
    }


__all__ = ["PublicImpactExplorer"]
