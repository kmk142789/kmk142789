"""Structural blueprint describing the Lil Footsteps nonprofit bank.

This module translates the narrative specification for the "Non Profit Bank"
into concrete, testable objects.  It focuses on the core requirements called
out in the product brief:

* hybrid funding design that mixes nonprofit inflows with low-risk
  for-profit multipliers;
* transparency mechanisms that let donors and parents trace every dollar;
* a growth model that guarantees proceeds are reinvested into Little
  Footsteps; and
* optional "overkill" features that can be toggled on by future work.

The intent is not to implement a full banking stack, but rather to provide a
clear, well-typed representation that other parts of the codebase (dashboards,
CLI tools, simulations) can rely upon.  The dataclasses expose helpers for
common operations—logging a flow, generating an impact token, and producing a
quarterly impact report—while keeping the rest of the brief available as
structured metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, MutableMapping, Sequence
from uuid import uuid4


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    """Normalise numeric inputs into :class:`~decimal.Decimal` values."""

    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True)
class CoreDesign:
    """Outline of the hybrid nonprofit/for-profit engine."""

    nonprofit_inflows: Sequence[str]
    for_profit_multiplier: Sequence[str]
    transparency_layer: str

    def summary(self) -> str:
        items = ", ".join(self.nonprofit_inflows)
        instruments = ", ".join(self.for_profit_multiplier)
        return (
            "Lil Footsteps receives nonprofit inflows from "
            f"{items} and amplifies them through {instruments}. "
            f"Transparency commitment: {self.transparency_layer}"
        )


@dataclass(frozen=True)
class TransparencyMechanisms:
    """Explicit transparency affordances for donors and families."""

    public_ledger_dashboard: str
    impact_tokenization: str
    quarterly_reports: str

    def as_dict(self) -> Mapping[str, str]:
        return {
            "public_ledger_dashboard": self.public_ledger_dashboard,
            "impact_tokenization": self.impact_tokenization,
            "quarterly_reports": self.quarterly_reports,
        }


@dataclass(frozen=True)
class GrowthModel:
    """Narrative describing how proceeds fuel Little Footsteps."""

    guaranteed_reinvestment: str
    direct_support: Sequence[str]
    revenue_engines: Sequence[str]
    circular_design: str

    def portfolio(self) -> Mapping[str, Sequence[str] | str]:
        return {
            "guaranteed_reinvestment": self.guaranteed_reinvestment,
            "direct_support": tuple(self.direct_support),
            "revenue_engines": tuple(self.revenue_engines),
            "circular_design": self.circular_design,
        }


@dataclass(frozen=True)
class OverkillFeatures:
    """Optional but forward-looking enhancements."""

    impact_nfts: str
    community_bonds: str
    partnership_layer: str
    ai_impact_auditor: str

    def catalogue(self) -> Mapping[str, str]:
        return {
            "impact_nfts": self.impact_nfts,
            "community_bonds": self.community_bonds,
            "partnership_layer": self.partnership_layer,
            "ai_impact_auditor": self.ai_impact_auditor,
        }


@dataclass(frozen=True)
class TransparencyLogEntry:
    """Immutable record of an inflow, investment, or deployment."""

    timestamp: datetime
    category: str
    amount: Decimal
    source: str
    destination: str
    label: str
    memo: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def as_dict(self) -> Mapping[str, str | Decimal]:
        payload: MutableMapping[str, str | Decimal] = {
            "timestamp": self.timestamp.isoformat(),
            "category": self.category,
            "amount": self.amount,
            "source": self.source,
            "destination": self.destination,
            "label": self.label,
        }
        if self.memo:
            payload["memo"] = self.memo
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ImpactTokenTrace:
    """Trace a donor dollar from contribution to deployment."""

    token_id: str
    amount: Decimal
    path: Sequence[str]
    issued_at: datetime
    metadata: Mapping[str, str]

    def describe(self) -> str:
        hop_description = " → ".join(self.path)
        return f"{self.token_id} · {self.amount} → {hop_description}"


@dataclass(frozen=True)
class QuarterlyImpactReport:
    """Blend of financial and impact metrics for a reporting period."""

    quarter: str
    financials: Mapping[str, Decimal]
    impact_metrics: Mapping[str, int]
    roi: Decimal
    net_cash_flow: Decimal
    narrative: str

    def as_dict(self) -> Mapping[str, object]:
        return {
            "quarter": self.quarter,
            "financials": {k: str(v) for k, v in self.financials.items()},
            "impact_metrics": dict(self.impact_metrics),
            "roi": str(self.roi),
            "net_cash_flow": str(self.net_cash_flow),
            "narrative": self.narrative,
        }


@dataclass
class NonprofitBankStructure:
    """Runtime helper that makes the Lil Footsteps bank specification tangible."""

    core_design: CoreDesign
    transparency: TransparencyMechanisms
    growth_model: GrowthModel
    overkill_features: OverkillFeatures
    _transparency_log: list[TransparencyLogEntry] = field(default_factory=list, init=False)
    _impact_tokens: list[ImpactTokenTrace] = field(default_factory=list, init=False)
    _reports: list[QuarterlyImpactReport] = field(default_factory=list, init=False)

    # ------------------------------------------------------------------
    # Transparency ledger utilities
    # ------------------------------------------------------------------
    def record_flow(
        self,
        *,
        category: str,
        amount: Decimal | int | float | str,
        source: str,
        destination: str,
        label: str,
        memo: str | None = None,
        metadata: Mapping[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> TransparencyLogEntry:
        """Record a flow event aligned with the public transparency layer."""

        entry = TransparencyLogEntry(
            timestamp=timestamp or datetime.now(tz=UTC),
            category=category,
            amount=_to_decimal(amount),
            source=source,
            destination=destination,
            label=label,
            memo=memo,
            metadata=dict(metadata or {}),
        )
        self._transparency_log.append(entry)
        return entry

    def transparency_snapshot(self) -> Sequence[TransparencyLogEntry]:
        """Return an immutable view of the transparency log."""

        return tuple(self._transparency_log)

    def validate_reinvestment(self) -> bool:
        """Ensure all yield events loop back into Little Footsteps."""

        return all(
            entry.destination.lower().startswith("little footsteps")
            for entry in self._transparency_log
            if entry.category in {"yield", "investment_return"}
        )

    # ------------------------------------------------------------------
    # Impact tokenisation
    # ------------------------------------------------------------------
    def create_impact_token(
        self,
        *,
        donor: str,
        amount: Decimal | int | float | str,
        deployment: str,
        investment_vehicle: str = "Treasuries",
        metadata: Mapping[str, str] | None = None,
        issued_at: datetime | None = None,
    ) -> ImpactTokenTrace:
        """Mint a traceable impact token for a donor contribution."""

        token_id = f"IMPACT-{uuid4().hex[:8].upper()}"
        issued_at = issued_at or datetime.now(tz=UTC)
        amount_decimal = _to_decimal(amount).quantize(Decimal("0.01"))
        path = (
            f"donor:{donor}",
            f"investment:{investment_vehicle}",
            f"destination:{deployment}",
        )
        token = ImpactTokenTrace(
            token_id=token_id,
            amount=amount_decimal,
            path=path,
            issued_at=issued_at,
            metadata=dict(metadata or {}),
        )
        self._impact_tokens.append(token)
        return token

    def impact_tokens(self) -> Sequence[ImpactTokenTrace]:
        """Return all issued impact tokens."""

        return tuple(self._impact_tokens)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def generate_quarterly_report(
        self,
        *,
        quarter: str,
        total_inflows: Decimal | int | float | str,
        investment_returns: Decimal | int | float | str,
        operating_costs: Decimal | int | float | str,
        kids_supported: int,
        meals_served: int,
        stands_operated: int,
    ) -> QuarterlyImpactReport:
        """Blend financial and impact metrics into a transparent report."""

        inflows = _to_decimal(total_inflows)
        returns = _to_decimal(investment_returns)
        costs = _to_decimal(operating_costs)

        if inflows <= 0:
            roi = Decimal("0")
        else:
            roi = (returns / inflows).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        net_cash_flow = (inflows + returns - costs).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        financials = {
            "total_inflows": inflows.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "investment_returns": returns.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "operating_costs": costs.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "cash_on_hand": net_cash_flow,
        }
        impact_metrics = {
            "kids_supported": kids_supported,
            "meals_served": meals_served,
            "stands_operated": stands_operated,
        }
        narrative = (
            f"Quarter {quarter}: reinvested yields from safe instruments into Little Footsteps, "
            f"funding {kids_supported} children, {meals_served} meals, and {stands_operated} "
            "community-run lemonade stands."
        )

        report = QuarterlyImpactReport(
            quarter=quarter,
            financials=financials,
            impact_metrics=impact_metrics,
            roi=roi,
            net_cash_flow=net_cash_flow,
            narrative=narrative,
        )
        self._reports.append(report)
        return report

    def reports(self) -> Sequence[QuarterlyImpactReport]:
        """Return generated quarterly reports."""

        return tuple(self._reports)

    # ------------------------------------------------------------------
    # Convenience metadata
    # ------------------------------------------------------------------
    def as_dict(self) -> Mapping[str, object]:
        """Serialise the entire structure into a mapping."""

        return {
            "core_design": {
                "nonprofit_inflows": list(self.core_design.nonprofit_inflows),
                "for_profit_multiplier": list(self.core_design.for_profit_multiplier),
                "transparency_layer": self.core_design.transparency_layer,
            },
            "transparency": dict(self.transparency.as_dict()),
            "growth_model": dict(self.growth_model.portfolio()),
            "overkill_features": dict(self.overkill_features.catalogue()),
        }


def create_default_structure() -> NonprofitBankStructure:
    """Return the canonical Lil Footsteps nonprofit bank configuration."""

    core = CoreDesign(
        nonprofit_inflows=("Grants", "Donations", "Foundations"),
        for_profit_multiplier=("U.S. Treasuries", "Green bonds", "Community credit unions"),
        transparency_layer="All flows logged on a public ledger dashboard or verifiable blockchain feed.",
    )
    transparency = TransparencyMechanisms(
        public_ledger_dashboard=
        "Every inflow and outflow is timestamped and published to an open dashboard for families and supporters.",
        impact_tokenization=
        "Each contributed dollar is tokenised so donors can trace the journey from donor → investment → daycare → lemonade stand.",
        quarterly_reports=
        "Quarterly proof-of-impact reports merge ROI, cash flow, and childcare impact metrics.",
    )
    growth = GrowthModel(
        guaranteed_reinvestment=
        "100% of yields from the financial engine are redeployed into Little Footsteps operations.",
        direct_support=("Staff", "Space", "Food", "Activities"),
        revenue_engines=("Lemonade stands", "Branded baked goods", "Church partnerships"),
        circular_design=
        "Community ventures create social and micro-financial returns that flow back into the bank, compounding support.",
    )
    overkill = OverkillFeatures(
        impact_nfts=
        "Parents can mint milestone NFTs (first lemonade stand, first paycheck, first art show) backed by bank funding.",
        community_bonds=
        "$25 Footstep Bonds provide locals a redeemable way to finance expansion while earning goodwill.",
        partnership_layer=
        "Churches, grocery chains, and city councils plug into the shared dashboard as federated partners.",
        ai_impact_auditor=
        "Echo's AI auditor monitors flows, flags anomalies, and generates transparent impact stories from raw data.",
    )
    return NonprofitBankStructure(
        core_design=core,
        transparency=transparency,
        growth_model=growth,
        overkill_features=overkill,
    )

