"""Reciprocity Waveform Protocol.

This module introduces a novel, world-changing feature: the ability to turn
acts of goodwill into *reciprocity waveforms* that self-balance across
communities, movements, and even cross-domain missions. The protocol is new in
three ways:

1. **Waveform framing** – contributions are treated as energy packets that decay
   through time but amplify when intent and impact align, producing a living
   reciprocity wave instead of a static ledger.
2. **Echo-symmetric pledging** – beneficiaries receive pledges that mirror the
   contributor's intent while accounting for readiness and horizon, generating
   actionable reciprocity without manual arbitration.
3. **Gratitude pressure** – the protocol surfaces a *gratitude pressure* metric
   that nudges ecosystems toward equilibrium by identifying where unreciprocated
   generosity is accumulating.

While the concept is fantastical, the implementation is deterministic, testable,
and ready to be composed with other orchestration modules in the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import log1p
from typing import Dict, Iterable, List, Mapping, Sequence


@dataclass(frozen=True)
class Contribution:
    """Represents a discrete act of goodwill entering the protocol."""

    contributor: str
    magnitude: float
    intent: float
    timestamp: datetime
    tags: Sequence[str] = field(default_factory=tuple)
    impact_half_life_hours: float = 72.0

    def decayed_magnitude(self, reference_time: datetime) -> float:
        """Return magnitude adjusted for temporal decay with a hard floor at zero."""

        if self.magnitude <= 0:
            return 0.0
        elapsed = reference_time - self.timestamp
        hours = max(0.0, elapsed.total_seconds() / 3600.0)
        if self.impact_half_life_hours <= 0:
            return 0.0
        decay_factor = 0.5 ** (hours / self.impact_half_life_hours)
        return round(self.magnitude * decay_factor, 6)


@dataclass(frozen=True)
class BeneficiarySignal:
    """Describes a beneficiary's readiness to convert reciprocity into action."""

    identifier: str
    need_level: float
    readiness: float
    horizon_hours: float
    tags: Sequence[str] = field(default_factory=tuple)

    def resonance(self, contribution: Contribution) -> float:
        """Score alignment between a contribution and this beneficiary."""

        shared_tags = set(self.tags) & set(contribution.tags)
        affinity = 1.0 + 0.2 * len(shared_tags)
        readiness_term = max(0.0, min(1.0, self.readiness))
        return round(affinity * readiness_term * max(0.1, self.need_level), 6)


@dataclass(frozen=True)
class ReciprocityPledge:
    """A deterministic pledge surfaced by the reciprocity waveform."""

    contributor: str
    beneficiary: str
    amount: float
    trigger: str
    confidence: float


@dataclass
class ReciprocityWaveform:
    """Aggregated view of the reciprocity state."""

    aggregate_energy: float
    fairness_index: float
    gratitude_pressure: float
    pledge_schedule: List[ReciprocityPledge]
    latent_divergences: List[str]


@dataclass
class ReciprocityManifest:
    """Wire-ready representation of a waveform for downstream orchestration."""

    energy: float
    fairness: float
    gratitude_pressure: float
    pledges: Sequence[Mapping[str, object]]
    divergences: Sequence[str]


class ReciprocityWaveformProtocol:
    """Coordinate the creation of reciprocity waveforms.

    The protocol is intentionally deterministic: identical inputs will produce
    identical pledges, gratitude pressure, and fairness indices, making the
    feature suitable for reproducible simulations, governance reviews, and
    auditable social contracts.
    """

    def __init__(self, gratitude_bias: float = 0.5, attenuation_half_life_hours: float = 72.0):
        self.gratitude_bias = max(0.0, min(1.0, gratitude_bias))
        self.attenuation_half_life_hours = max(1.0, attenuation_half_life_hours)

    def _reference_time(self, contributions: Iterable[Contribution]) -> datetime:
        latest = max((c.timestamp for c in contributions), default=datetime.now(timezone.utc))
        return latest + timedelta(hours=1)

    def _decayed_energy(self, contributions: Iterable[Contribution], reference_time: datetime) -> Dict[str, float]:
        decayed: Dict[str, float] = {}
        for contribution in contributions:
            base_energy = contribution.decayed_magnitude(reference_time)
            attenuation = 0.5 ** (
                max(0.0, (reference_time - contribution.timestamp).total_seconds() / 3600.0)
                / self.attenuation_half_life_hours
            )
            energy = base_energy * attenuation * max(0.0, min(1.0, contribution.intent))
            decayed[contribution.contributor] = decayed.get(contribution.contributor, 0.0) + energy
        return decayed

    def _beneficiary_pressure(self, beneficiaries: Iterable[BeneficiarySignal]) -> float:
        signals = [max(0.0, min(1.0, b.need_level * b.readiness)) for b in beneficiaries]
        if not signals:
            return 0.0
        return round(sum(signals) / len(signals), 6)

    def synthesize_waveform(
        self, contributions: Sequence[Contribution], beneficiaries: Sequence[BeneficiarySignal]
    ) -> ReciprocityWaveform:
        reference_time = self._reference_time(contributions)
        decayed_energy = self._decayed_energy(contributions, reference_time)
        total_energy = sum(decayed_energy.values())
        beneficiary_pressure = self._beneficiary_pressure(beneficiaries)

        pledge_schedule = self._build_pledges(contributions, beneficiaries, decayed_energy, total_energy)
        fairness_index = self._fairness(total_energy, beneficiary_pressure)
        gratitude_pressure = self._gratitude(total_energy, len(pledge_schedule))
        divergences = self._latent_divergences(decayed_energy, beneficiaries)

        return ReciprocityWaveform(
            aggregate_energy=round(total_energy, 6),
            fairness_index=round(fairness_index, 6),
            gratitude_pressure=round(gratitude_pressure, 6),
            pledge_schedule=pledge_schedule,
            latent_divergences=divergences,
        )

    def _fairness(self, total_energy: float, beneficiary_pressure: float) -> float:
        if total_energy <= 0:
            return 0.0
        balance = max(0.0, min(1.0, beneficiary_pressure))
        return round(0.6 * balance + 0.4 * self.gratitude_bias, 6)

    def _gratitude(self, total_energy: float, pledge_count: int) -> float:
        if total_energy <= 0:
            return 0.0
        density = log1p(total_energy) / (1.0 + pledge_count)
        return round(max(0.0, min(1.0, density)), 6)

    def _build_pledges(
        self,
        contributions: Sequence[Contribution],
        beneficiaries: Sequence[BeneficiarySignal],
        decayed_energy: Mapping[str, float],
        total_energy: float,
    ) -> List[ReciprocityPledge]:
        if not beneficiaries or total_energy <= 0:
            return []

        pledges: List[ReciprocityPledge] = []
        normalized_energy = {k: v / total_energy for k, v in decayed_energy.items() if v > 0}

        for contribution in contributions:
            if contribution.contributor not in normalized_energy:
                continue
            energy_share = normalized_energy[contribution.contributor]
            best_match = max(beneficiaries, key=lambda b: b.resonance(contribution))
            resonance = best_match.resonance(contribution)
            pledge_amount = energy_share * resonance
            trigger = self._pledge_trigger(best_match)
            confidence = max(0.05, min(1.0, 0.5 + 0.5 * resonance))
            pledges.append(
                ReciprocityPledge(
                    contributor=contribution.contributor,
                    beneficiary=best_match.identifier,
                    amount=round(pledge_amount, 6),
                    trigger=trigger,
                    confidence=round(confidence, 6),
                )
            )

        pledges.sort(key=lambda p: (-p.amount, p.beneficiary, p.contributor))
        return pledges

    def _pledge_trigger(self, beneficiary: BeneficiarySignal) -> str:
        horizon = max(1.0, beneficiary.horizon_hours)
        window = int(horizon // 24) or 1
        return f"activate-within-{window}-days"

    def _latent_divergences(
        self, decayed_energy: Mapping[str, float], beneficiaries: Sequence[BeneficiarySignal]
    ) -> List[str]:
        if not decayed_energy:
            return ["no-contributions"]
        if not beneficiaries:
            return ["no-beneficiaries"]

        energy_values = list(decayed_energy.values())
        spread = max(energy_values) - min(energy_values)
        divergences: List[str] = []

        if spread > 0.5 * max(energy_values):
            divergences.append("energy-imbalance")
        if len(set(b.identifier for b in beneficiaries)) < len(beneficiaries):
            divergences.append("beneficiary-duplication")
        if all(b.need_level < 0.2 for b in beneficiaries):
            divergences.append("low-need-environment")

        return divergences or ["balanced"]

    def manifest(
        self, contributions: Sequence[Contribution], beneficiaries: Sequence[BeneficiarySignal]
    ) -> ReciprocityManifest:
        waveform = self.synthesize_waveform(contributions, beneficiaries)
        return ReciprocityManifest(
            energy=waveform.aggregate_energy,
            fairness=waveform.fairness_index,
            gratitude_pressure=waveform.gratitude_pressure,
            pledges=[
                {
                    "contributor": pledge.contributor,
                    "beneficiary": pledge.beneficiary,
                    "amount": pledge.amount,
                    "trigger": pledge.trigger,
                    "confidence": pledge.confidence,
                }
                for pledge in waveform.pledge_schedule
            ],
            divergences=waveform.latent_divergences,
        )

