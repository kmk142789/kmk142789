"""Public Impact Explorer dataset builder for the Pulse Dashboard."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

WEI_PER_ETHER = 10**18


@dataclass(slots=True)
class ImpactPaths:
    """Helper paths anchored to the repository root."""

    root: Path

    @property
    def ledger_file(self) -> Path:
        return self.root / "ledger" / "nonprofit_bank_ledger.json"

    @property
    def treasury_policy(self) -> Path:
        return self.root / "state" / "nonprofit_treasury_policy.json"

    @property
    def childcare_metrics(self) -> Path:
        return self.root / "reports" / "data" / "childcare_impact_metrics.json"

    @property
    def parent_council(self) -> Path:
        return self.root / "state" / "parent_advisory_council.json"

    @property
    def provider_feedback(self) -> Path:
        return self.root / "state" / "provider_feedback_loop.json"


class PublicImpactExplorer:
    """Compose treasury, impact, and stakeholder signals for the dashboard."""

    def __init__(self, root: Path | str | None = None) -> None:
        self.paths = ImpactPaths(root=Path(root or Path.cwd()).resolve())

    def build(self) -> dict[str, Any]:
        """Return a dictionary suitable for serialising into the dashboard payload."""

        treasury = self._build_treasury_snapshot()
        impact_metrics = self._load_childcare_metrics()
        stakeholder_voice = self._load_stakeholder_voice()
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "treasury": treasury,
            "impact_metrics": impact_metrics,
            "stakeholder_voice": stakeholder_voice,
            "upcoming_engagements": self._compose_engagements(stakeholder_voice),
        }

    # ------------------------------------------------------------------
    # Treasury helpers
    # ------------------------------------------------------------------

    def _build_treasury_snapshot(self) -> dict[str, Any]:
        ledger_entries = self._load_ledger_entries()
        policy = self._load_json(self.paths.treasury_policy)

        deposits = [entry for entry in ledger_entries if entry["type"] == "deposit"]
        payouts = [entry for entry in ledger_entries if entry["type"] == "payout"]
        total_deposits = sum(entry["amount_wei"] for entry in deposits)
        total_payouts = sum(entry["amount_wei"] for entry in payouts)
        balance_wei = total_deposits - total_payouts

        timeline: list[dict[str, Any]] = []
        running_balance = 0
        for entry in ledger_entries:
            amount = entry["amount_wei"]
            running_balance += amount if entry["type"] == "deposit" else -amount
            timestamp = self._epoch_to_iso(entry["timestamp"])
            timeline.append(
                {
                    "timestamp": timestamp,
                    "type": entry["type"],
                    "actor": entry["actor"],
                    "amount_wei": amount,
                    "amount_eth": round(amount / WEI_PER_ETHER, 6),
                    "balance_wei": running_balance,
                    "balance_eth": round(running_balance / WEI_PER_ETHER, 6),
                    "tx_hash": entry["tx_hash"],
                }
            )

        ledger_snapshot = {
            "total_deposits_wei": total_deposits,
            "total_payouts_wei": total_payouts,
            "balance_wei": balance_wei,
            "balance_eth": round(balance_wei / WEI_PER_ETHER, 6),
            "total_deposits_eth": round(total_deposits / WEI_PER_ETHER, 6),
            "total_payouts_eth": round(total_payouts / WEI_PER_ETHER, 6),
            "deposit_count": len(deposits),
            "payout_count": len(payouts),
            "donor_addresses": sorted({entry["actor"] for entry in deposits}),
            "payout_addresses": sorted({entry["actor"] for entry in payouts}),
            "donor_count": len({entry["actor"] for entry in deposits}),
            "payout_recipient_count": len({entry["actor"] for entry in payouts}),
            "last_deposit_at": self._epoch_to_iso(max((entry["timestamp"] for entry in deposits), default=None)),
            "last_payout_at": self._epoch_to_iso(max((entry["timestamp"] for entry in payouts), default=None)),
            "timeline": timeline,
        }

        policy_snapshot = self._summarise_policy(policy)
        return {
            "ledger": ledger_snapshot,
            "policy": policy_snapshot,
        }

    def _load_ledger_entries(self) -> list[dict[str, Any]]:
        path = self.paths.ledger_file
        if not path.exists():
            return []
        try:
            raw_entries = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

        entries: list[dict[str, Any]] = []
        for entry in raw_entries:
            if not isinstance(entry, Mapping):
                continue
            try:
                record = {
                    "type": str(entry["type"]).lower(),
                    "amount_wei": int(entry["amount_wei"]),
                    "tx_hash": str(entry.get("tx_hash", "")),
                    "actor": str(entry.get("actor", "")),
                    "timestamp": int(entry.get("timestamp", 0)),
                }
            except (KeyError, TypeError, ValueError):
                continue
            entries.append(record)
        entries.sort(key=lambda item: item["timestamp"])
        return entries

    def _summarise_policy(self, policy: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(policy, Mapping):
            return {
                "targets": [],
                "current_reserves": [],
                "diversity_score": None,
                "emergency_reserve": {},
                "yield_programs": [],
                "runway_weeks": None,
            }

        targets_raw = policy.get("stablecoin_targets", [])
        targets: list[dict[str, Any]] = []
        for item in targets_raw:
            if not isinstance(item, Mapping):
                continue
            try:
                pct = float(item.get("target_pct", 0))
            except (TypeError, ValueError):
                pct = 0.0
            if pct > 1:
                pct /= 100
            targets.append(
                {
                    "symbol": str(item.get("symbol", "")),
                    "target_pct": round(pct, 4),
                    "network": item.get("network"),
                    "notes": item.get("notes"),
                }
            )

        reserves_raw = policy.get("current_reserves", {})
        current_reserves: list[dict[str, Any]] = []
        total_reserves = 0.0
        for symbol, entry in reserves_raw.items():
            if not isinstance(entry, Mapping):
                continue
            try:
                amount = float(entry.get("amount_usd", 0))
            except (TypeError, ValueError):
                amount = 0.0
            total_reserves += amount
            current_reserves.append(
                {
                    "symbol": symbol,
                    "amount_usd": amount,
                    "custodian": entry.get("custodian"),
                    "addresses": entry.get("addresses", []),
                }
            )

        allocations = []
        deviation_total = 0.0
        for target in targets:
            symbol = target["symbol"]
            target_pct = float(target["target_pct"])
            reserve_entry = next((item for item in current_reserves if item["symbol"] == symbol), None)
            amount = reserve_entry["amount_usd"] if reserve_entry else 0.0
            actual_pct = (amount / total_reserves) if total_reserves else 0.0
            delta = target_pct - actual_pct
            deviation_total += abs(delta)
            action = "increase" if delta > 0.01 else "decrease" if delta < -0.01 else "hold"
            allocations.append(
                {
                    "symbol": symbol,
                    "target_pct": round(target_pct * 100, 2),
                    "actual_pct": round(actual_pct * 100, 2),
                    "delta_pct": round(delta * 100, 2),
                    "action": action,
                    "amount_usd": amount,
                }
            )

        diversity_score = round(max(0.0, 100.0 - deviation_total * 100), 2)

        emergency = policy.get("emergency_reserve", {})
        emergency_snapshot: dict[str, Any] = {}
        if isinstance(emergency, Mapping):
            try:
                target_ratio = float(emergency.get("target_ratio", 0))
            except (TypeError, ValueError):
                target_ratio = 0.0
            try:
                current_usd = float(emergency.get("current_usd", 0))
            except (TypeError, ValueError):
                current_usd = 0.0
            current_ratio = (current_usd / total_reserves) if total_reserves else 0.0
            emergency_snapshot = {
                "target_ratio": round(target_ratio, 4),
                "current_ratio": round(current_ratio, 4),
                "current_usd": current_usd,
                "status": "meets_target" if current_ratio >= target_ratio else "below_target",
                "multisig_threshold": emergency.get("multisig_threshold"),
                "vault": emergency.get("vault"),
                "guardians": emergency.get("guardians", []),
            }

        yield_programs_raw = policy.get("yield_programs", [])
        yield_programs = [item for item in yield_programs_raw if isinstance(item, Mapping)]

        try:
            burn = float(policy.get("operating_burn_usd_weekly", 0))
        except (TypeError, ValueError):
            burn = 0.0
        runway_weeks = (total_reserves / burn) if burn else None

        return {
            "updated_at": policy.get("updated_at"),
            "targets": allocations,
            "current_reserves": current_reserves,
            "total_reserves_usd": total_reserves,
            "diversity_score": diversity_score,
            "emergency_reserve": emergency_snapshot,
            "yield_programs": yield_programs,
            "runway_weeks": round(runway_weeks, 2) if runway_weeks is not None else None,
            "auto_balance_rules": policy.get("auto_balance_rules", {}),
            "notes": policy.get("notes"),
        }

    # ------------------------------------------------------------------
    # Childcare impact metrics helpers
    # ------------------------------------------------------------------

    def _load_childcare_metrics(self) -> dict[str, Any]:
        data = self._load_json(self.paths.childcare_metrics)
        if not isinstance(data, Mapping):
            return {
                "totals": {},
                "current_cycle": {},
                "history": [],
                "equity_breakdown": {},
                "data_sources": [],
            }

        history = [item for item in data.get("history", []) if isinstance(item, Mapping)]
        history.sort(key=lambda item: str(item.get("period")))
        trends = self._calculate_trends(history)

        return {
            "last_updated": data.get("last_updated"),
            "totals": data.get("totals", {}),
            "current_cycle": data.get("current_cycle", {}),
            "history": history[-8:],
            "trend": trends,
            "equity_breakdown": data.get("equity_breakdown", {}),
            "data_sources": data.get("data_sources", []),
        }

    def _calculate_trends(self, history: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        history_list = list(history)
        if len(history_list) < 2:
            return {}
        latest = history_list[-1]
        previous = history_list[-2]
        metrics = [
            "families_served",
            "hours_of_childcare",
            "job_placements",
            "caregiver_wages_paid_usd",
        ]
        trends: dict[str, Any] = {}
        for key in metrics:
            latest_value = self._safe_float(latest.get(key))
            previous_value = self._safe_float(previous.get(key))
            if latest_value is None or previous_value is None:
                continue
            change = latest_value - previous_value
            pct_change = (change / previous_value * 100) if previous_value else None
            trends[key] = {
                "latest": latest_value,
                "previous": previous_value,
                "change": round(change, 2),
                "pct_change": round(pct_change, 2) if pct_change is not None else None,
            }
        return trends

    # ------------------------------------------------------------------
    # Stakeholder voice helpers
    # ------------------------------------------------------------------

    def _load_stakeholder_voice(self) -> dict[str, Any]:
        parent = self._load_json(self.paths.parent_council) or {}
        provider = self._load_json(self.paths.provider_feedback) or {}
        return {
            "parent_advisory_council": parent,
            "provider_feedback_loop": provider,
        }

    def _compose_engagements(self, voice: Mapping[str, Any]) -> list[dict[str, Any]]:
        engagements: list[dict[str, Any]] = []
        parent = voice.get("parent_advisory_council", {}) if isinstance(voice, Mapping) else {}
        if isinstance(parent, Mapping):
            cadence = parent.get("meeting_cadence", {})
            next_session = None
            if isinstance(cadence, Mapping):
                next_session = cadence.get("next_session")
            timestamp = self._parse_iso(next_session) if next_session else None
            if timestamp:
                engagements.append(
                    {
                        "name": "Parent Advisory Council",
                        "scheduled_for": timestamp.isoformat(),
                        "context": cadence.get("location") if isinstance(cadence, Mapping) else None,
                    }
                )

        provider = voice.get("provider_feedback_loop", {}) if isinstance(voice, Mapping) else {}
        if isinstance(provider, Mapping):
            office_hours = provider.get("office_hours", {})
            if isinstance(office_hours, Mapping):
                next_session = office_hours.get("next_session")
                timestamp = self._parse_iso(next_session) if next_session else None
                if timestamp:
                    engagements.append(
                        {
                            "name": "Provider Office Hours",
                            "scheduled_for": timestamp.isoformat(),
                            "context": office_hours.get("host"),
                        }
                    )

        engagements.sort(key=lambda item: item.get("scheduled_for", ""))
        return engagements

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    def _load_json(self, path: Path) -> Mapping[str, Any] | list[Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _epoch_to_iso(self, value: int | None) -> str | None:
        if not value:
            return None
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
        except (OSError, OverflowError, ValueError):
            return None

    def _parse_iso(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            cleaned = value.replace("Z", "+00:00") if isinstance(value, str) else value
            return datetime.fromisoformat(cleaned)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    def _safe_float(self, value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


__all__ = ["PublicImpactExplorer"]
