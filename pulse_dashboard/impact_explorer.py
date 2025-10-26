"""Impact Explorer dataset builder.

This module assembles the transparency, community, and operational
signals that underpin the Impact Explorer dashboard.  It fuses on-chain
treasury events, childcare impact metrics, governance feedback, and the
supporting operating model into a single serialisable payload.
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

            if event["type"] == "donation":
                totals["donations"] += amount
                bucket["donations"] += amount
                source_bucket["donations"] += amount
                if event["timestamp"] >= window_start:
                    window["donations"] += amount
            else:
                totals["disbursed"] += amount
                bucket["disbursed"] += amount
                source_bucket["disbursed"] += amount
                if event["timestamp"] >= window_start:
                    window["disbursed"] += amount

        totals["balance"] = totals["donations"] - totals["disbursed"]
        for bucket in (*by_asset.values(), *by_source.values()):
            bucket["balance"] = bucket["donations"] - bucket["disbursed"]

        return {
            "events": [self._serialise_event(event) for event in events],
            "totals": self._serialise_amounts(totals),
            "rolling_30_days": self._serialise_amounts(window),
            "assets": {key: self._serialise_amounts(value) for key, value in by_asset.items()},
            "sources": {key: self._serialise_amounts(value) for key, value in by_source.items()},
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

