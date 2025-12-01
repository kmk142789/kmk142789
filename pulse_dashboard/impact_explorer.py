"""Impact Explorer dataset builder.

This module assembles the transparency, community, and operational
signals that underpin the Impact Explorer dashboard.  It fuses on-chain
treasury events, childcare impact metrics, governance feedback, and the
supporting operating model into a single serialisable payload.  The
builder now also derives capital efficiency insights such as donor
concentration and treasury runway to help readers contextualise the
financial movements.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
from typing import Any, Iterable


Number = Decimal


def _decimal(value: Any) -> Number:
    """Return *value* coerced into a :class:`~decimal.Decimal`.

    The helper gracefully handles ``None`` values, strings, integers, and
    floats.  Any parsing failure returns ``Decimal("0")`` which keeps the
    aggregation logic resilient against partially populated records.
    """

    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):  # pragma: no cover -
        return Decimal("0")


@dataclass(slots=True)
class ImpactExplorerPaths:
    """Filesystem layout for the Impact Explorer inputs."""

    root: Path

    @property
    def data_dir(self) -> Path:
        return self.root / "data" / "impact"

    @property
    def financial_events(self) -> Path:
        return self.data_dir / "financial_events.json"

    @property
    def impact_metrics(self) -> Path:
        return self.data_dir / "impact_metrics.json"

    @property
    def community_voice(self) -> Path:
        return self.data_dir / "community_voice.json"

    @property
    def operations(self) -> Path:
        return self.data_dir / "operations.json"


class ImpactExplorerBuilder:
    """Construct the Impact Explorer payload from tracked datasets."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        root = Path(project_root or Path.cwd()).resolve()
        self._paths = ImpactExplorerPaths(root=root)

    # ------------------------------------------------------------------
    # Public entrypoints

    def build(self) -> dict[str, Any]:
        """Return a dictionary with transparency metrics and narratives."""

        now = datetime.now(timezone.utc)
        return {
            "generated_at": now.isoformat(),
            "financials": self._build_financials(now),
            "impact_metrics": self._load_json(self._paths.impact_metrics, {}),
            "community_voice": self._load_json(self._paths.community_voice, {}),
            "operations": self._load_json(self._paths.operations, {}),
        }

    def write(
        self, data: dict[str, Any] | None = None, *, path: Path | str | None = None
    ) -> Path:
        """Serialise the Impact Explorer payload to ``path``."""

        target = Path(path or self._paths.data_dir / "impact_dashboard.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = data or self.build()
        target.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    # Internal helpers

    def _build_financials(self, now: datetime) -> dict[str, Any]:
        window_start = now - timedelta(days=30)
        events = [
            self._normalise_financial_event(raw)
            for raw in self._load_json(self._paths.financial_events, [])
        ]
        events = [event for event in events if event is not None]
        events.sort(key=lambda item: item["timestamp"], reverse=True)

        totals = {"donations": Decimal("0"), "disbursed": Decimal("0"), "balance": Decimal("0")}
        window = {"donations": Decimal("0"), "disbursed": Decimal("0")}
        by_asset: dict[str, dict[str, Number]] = {}
        by_source: dict[str, dict[str, Number]] = {}
        monthly: dict[str, dict[str, Number]] = {}
        donation_amounts: list[Number] = []
        disbursement_amounts: list[Number] = []
        largest_donation: dict[str, Any] | None = None
        largest_disbursement: dict[str, Any] | None = None

        for event in events:
            amount = event["amount_usd"]
            asset = event.get("asset", "unknown")
            source = event.get("source", "unknown")
            bucket = by_asset.setdefault(
                asset,
                {"donations": Decimal("0"), "disbursed": Decimal("0"), "balance": Decimal("0")},
            )
            source_bucket = by_source.setdefault(
                source,
                {"donations": Decimal("0"), "disbursed": Decimal("0"), "balance": Decimal("0")},
            )

            month_key = event["timestamp"].strftime("%Y-%m")
            month_bucket = monthly.setdefault(
                month_key,
                {"donations": Decimal("0"), "disbursed": Decimal("0"), "balance": Decimal("0")},
            )

            if event["type"] == "donation":
                totals["donations"] += amount
                bucket["donations"] += amount
                source_bucket["donations"] += amount
                month_bucket["donations"] += amount
                donation_amounts.append(amount)
                if (largest_donation is None) or (amount > largest_donation["amount_usd"]):
                    largest_donation = event
                if event["timestamp"] >= window_start:
                    window["donations"] += amount
            else:
                totals["disbursed"] += amount
                bucket["disbursed"] += amount
                source_bucket["disbursed"] += amount
                month_bucket["disbursed"] += amount
                disbursement_amounts.append(amount)
                if (largest_disbursement is None) or (amount > largest_disbursement["amount_usd"]):
                    largest_disbursement = event
                if event["timestamp"] >= window_start:
                    window["disbursed"] += amount

        totals["balance"] = totals["donations"] - totals["disbursed"]
        for bucket in (*by_asset.values(), *by_source.values()):
            bucket["balance"] = bucket["donations"] - bucket["disbursed"]
        for bucket in monthly.values():
            bucket["balance"] = bucket["donations"] - bucket["disbursed"]

        donor_concentration = self._donation_concentration(by_source, totals["donations"])
        runway = self._estimate_runway(totals["balance"], monthly)

        insights = self._build_insights(
            largest_donation,
            largest_disbursement,
            donation_amounts,
            disbursement_amounts,
            donor_concentration,
            runway,
        )

        return {
            "events": [self._serialise_event(event) for event in events],
            "totals": self._serialise_amounts(totals),
            "rolling_30_days": self._serialise_amounts(window),
            "assets": {key: self._serialise_amounts(value) for key, value in by_asset.items()},
            "sources": {key: self._serialise_amounts(value) for key, value in by_source.items()},
            "monthly_trends": self._serialise_monthly(monthly),
            "activity": self._activity_summary(events, window, now),
            "insights": insights,
        }

    # -- financial helpers -------------------------------------------------

    @staticmethod
    def _serialise_amounts(data: dict[str, Number]) -> dict[str, float]:
        return {key: float(value.quantize(Decimal("0.01"))) for key, value in data.items()}

    @staticmethod
    def _serialise_event(event: dict[str, Any]) -> dict[str, Any]:
        payload = dict(event)
        payload["timestamp"] = event["timestamp"].isoformat()
        payload["amount_usd"] = float(event["amount_usd"].quantize(Decimal("0.01")))
        return payload

    def _serialise_monthly(self, data: dict[str, dict[str, Number]]) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for month, bucket in sorted(data.items()):
            serialised = self._serialise_amounts(bucket)
            serialised["month"] = month
            entries.append(serialised)
        return entries

    def _build_insights(
        self,
        largest_donation: dict[str, Any] | None,
        largest_disbursement: dict[str, Any] | None,
        donation_amounts: list[Number],
        disbursement_amounts: list[Number],
        donor_concentration: dict[str, Any] | None,
        runway: dict[str, Any] | None,
    ) -> dict[str, Any]:
        insights = {
            "largest_donation": self._summarise_event(largest_donation),
            "largest_disbursement": self._summarise_event(largest_disbursement),
            "median_donation": self._serialise_decimal(self._median(donation_amounts)),
            "median_disbursement": self._serialise_decimal(self._median(disbursement_amounts)),
        }
        if donor_concentration is not None:
            insights["donor_concentration"] = donor_concentration
        if runway is not None:
            insights["runway"] = runway
        return insights

    def _donation_concentration(
        self, by_source: dict[str, dict[str, Number]], total_donations: Number
    ) -> dict[str, Any] | None:
        """Return the share contributed by the most significant donor."""
        if not by_source or total_donations <= Decimal("0"):
            return None

        source, bucket = max(by_source.items(), key=lambda item: item[1]["donations"])
        if bucket["donations"] <= Decimal("0"):
            return None

        share = bucket["donations"] / total_donations
        return {
            "source": source,
            "share": float(share.quantize(Decimal("0.0001"))),
            "amount_usd": float(bucket["donations"].quantize(Decimal("0.01"))),
        }

    def _estimate_runway(
        self, balance: Number, monthly: dict[str, dict[str, Number]]
    ) -> dict[str, Any] | None:
        """Estimate cash runway in months from historical disbursements."""
        if not monthly:
            return None

        disbursements = [bucket["disbursed"] for bucket in monthly.values() if bucket["disbursed"] > 0]
        if not disbursements:
            return None

        average = sum(disbursements) / Decimal(len(disbursements))
        if average <= Decimal("0"):
            return None

        months = balance / average if balance > Decimal("0") else Decimal("0")
        return {
            "average_monthly_disbursement": float(average.quantize(Decimal("0.01"))),
            "months": float(months.quantize(Decimal("0.01"))),
        }

    @staticmethod
    def _summarise_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
        if event is None:
            return None
        return {
            "id": event["id"],
            "asset": event.get("asset"),
            "source": event.get("source"),
            "amount_usd": float(event["amount_usd"].quantize(Decimal("0.01"))),
            "timestamp": event["timestamp"].isoformat(),
            "beneficiary": event.get("beneficiary"),
        }

    @staticmethod
    def _serialise_decimal(value: Number | None) -> float | None:
        if value is None:
            return None
        return float(value.quantize(Decimal("0.01")))

    @staticmethod
    def _median(values: list[Number]) -> Number | None:
        if not values:
            return None
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2

    def _activity_summary(
        self,
        events: list[dict[str, Any]],
        window: dict[str, Number],
        now: datetime,
    ) -> dict[str, Any]:
        latest_event = events[0] if events else None
        latest_donation = next((event for event in events if event["type"] == "donation"), None)
        latest_disbursement = next(
            (event for event in events if event["type"] == "disbursement"), None
        )

        days_since_event: float | None = None
        if latest_event is not None:
            delta = now - latest_event["timestamp"]
            days_since_event = round(delta.total_seconds() / 86_400, 2)

        return {
            "latest_event": self._summarise_event(latest_event),
            "latest_donation": self._summarise_event(latest_donation),
            "latest_disbursement": self._summarise_event(latest_disbursement),
            "days_since_last_event": days_since_event,
            "net_flow_30_days": self._serialise_decimal(
                window["donations"] - window["disbursed"]
            ),
        }

    def _normalise_financial_event(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        try:
            timestamp = self._parse_timestamp(raw.get("timestamp"))
        except ValueError:
            return None

        event_type = str(raw.get("type", "")).strip().lower()
        if event_type not in {"donation", "disbursement"}:
            return None

        amount = _decimal(raw.get("amount_usd"))
        return {
            "id": str(raw.get("id") or raw.get("tx_hash") or timestamp.isoformat()),
            "type": event_type,
            "timestamp": timestamp,
            "amount_usd": amount,
            "asset": str(raw.get("asset") or "unknown"),
            "source": str(raw.get("source") or "unknown"),
            "memo": raw.get("memo"),
            "beneficiary": raw.get("beneficiary"),
            "tx_hash": raw.get("tx_hash"),
        }

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str):
            try:
                # ISO 8601 parsing; ``fromisoformat`` handles most forms.
                return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
            except ValueError as exc:  # pragma: no cover - defensive branch
                raise ValueError("Invalid timestamp") from exc
        raise ValueError("Unsupported timestamp value")

    # -- generic helpers ---------------------------------------------------

    @staticmethod
    def _load_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default


def iter_events(builder: ImpactExplorerBuilder) -> Iterable[dict[str, Any]]:
    """Convenience generator yielding financial events for *builder*.

    The helper is primarily used by tests and notebook explorations where a
    quick iterator over the denormalised financial event feed is handy.
    """

    data = builder.build()
    yield from data.get("financials", {}).get("events", [])


__all__ = ["ImpactExplorerBuilder", "iter_events"]

