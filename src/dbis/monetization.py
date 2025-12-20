"""Universal monetization layer built on DBIS primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable
from uuid import uuid4

from .engine import ComplianceProfile, DbisEngine, PartyIdentity, Rail, TransactionIntent


@dataclass
class InstitutionalWallet:
    wallet_id: str
    owner: PartyIdentity
    roles: tuple[str, ...]
    governance_ref: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "wallet_id": self.wallet_id,
            "owner": self.owner.identity_id,
            "roles": list(self.roles),
            "governance_ref": self.governance_ref,
        }


@dataclass
class GrantDisbursement:
    grant_id: str
    intent: TransactionIntent
    policy_tags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "policy_tags": list(self.policy_tags),
            "intent": self.intent.as_dict(),
        }


@dataclass
class RoyaltyStream:
    stream_id: str
    intent: TransactionIntent
    schedule: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "stream_id": self.stream_id,
            "schedule": self.schedule,
            "intent": self.intent.as_dict(),
        }


@dataclass
class SubscriptionCharge:
    subscription_id: str
    intent: TransactionIntent
    cycle: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "subscription_id": self.subscription_id,
            "cycle": self.cycle,
            "intent": self.intent.as_dict(),
        }


@dataclass
class EscrowRelease:
    escrow_id: str
    intent: TransactionIntent
    milestone: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "escrow_id": self.escrow_id,
            "milestone": self.milestone,
            "intent": self.intent.as_dict(),
        }


@dataclass
class MonetizationSimulation:
    scenario_id: str
    intents: list[TransactionIntent] = field(default_factory=list)
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "notes": self.notes,
            "intents": [intent.as_dict() for intent in self.intents],
        }


class MonetizationEngine:
    """Composable monetization workflows grounded in DBIS governance."""

    def __init__(self, *, dbis: DbisEngine) -> None:
        self.dbis = dbis

    def grant(
        self,
        *,
        amount: float,
        currency: str,
        rail: Rail,
        issuer: InstitutionalWallet,
        beneficiary: PartyIdentity,
        governance_ref: str,
        policy_tags: Iterable[str] = (),
    ) -> GrantDisbursement:
        intent = self.dbis.create_intent(
            amount=amount,
            currency=currency,
            rail=rail,
            sender=issuer.owner,
            receiver=beneficiary,
            memo="grant-disbursement",
            governance_ref=governance_ref,
            approvals=issuer.roles,
            metadata={"grant_wallet": issuer.wallet_id},
        )
        return GrantDisbursement(grant_id=str(uuid4()), intent=intent, policy_tags=tuple(policy_tags))

    def royalty(
        self,
        *,
        amount: float,
        currency: str,
        rail: Rail,
        payer: InstitutionalWallet,
        payee: PartyIdentity,
        governance_ref: str,
        schedule: str,
    ) -> RoyaltyStream:
        intent = self.dbis.create_intent(
            amount=amount,
            currency=currency,
            rail=rail,
            sender=payer.owner,
            receiver=payee,
            memo="royalty-payment",
            governance_ref=governance_ref,
            approvals=payer.roles,
            metadata={"royalty_wallet": payer.wallet_id, "schedule": schedule},
        )
        return RoyaltyStream(stream_id=str(uuid4()), intent=intent, schedule=schedule)

    def subscription(
        self,
        *,
        amount: float,
        currency: str,
        rail: Rail,
        subscriber: InstitutionalWallet,
        provider: PartyIdentity,
        governance_ref: str,
        cycle: str,
    ) -> SubscriptionCharge:
        intent = self.dbis.create_intent(
            amount=amount,
            currency=currency,
            rail=rail,
            sender=subscriber.owner,
            receiver=provider,
            memo="subscription-charge",
            governance_ref=governance_ref,
            approvals=subscriber.roles,
            metadata={"subscription_wallet": subscriber.wallet_id, "cycle": cycle},
        )
        return SubscriptionCharge(subscription_id=str(uuid4()), intent=intent, cycle=cycle)

    def escrow_release(
        self,
        *,
        amount: float,
        currency: str,
        rail: Rail,
        escrow_agent: InstitutionalWallet,
        beneficiary: PartyIdentity,
        governance_ref: str,
        milestone: str,
    ) -> EscrowRelease:
        intent = self.dbis.create_intent(
            amount=amount,
            currency=currency,
            rail=rail,
            sender=escrow_agent.owner,
            receiver=beneficiary,
            memo="escrow-release",
            governance_ref=governance_ref,
            approvals=escrow_agent.roles,
            metadata={"escrow_wallet": escrow_agent.wallet_id, "milestone": milestone},
        )
        return EscrowRelease(escrow_id=str(uuid4()), intent=intent, milestone=milestone)

    def simulate(
        self,
        intents: Iterable[TransactionIntent],
        *,
        notes: str,
    ) -> MonetizationSimulation:
        return MonetizationSimulation(scenario_id=str(uuid4()), intents=list(intents), notes=notes)

    def settle_bundle(
        self,
        bundle: Iterable[TransactionIntent],
        compliance: ComplianceProfile,
        *,
        actor: str,
        audit_hooks: Iterable[str] = (),
    ) -> list[dict[str, Any]]:
        receipts = []
        for intent in bundle:
            receipts.append(
                self.dbis.settle_intent(
                    intent,
                    compliance,
                    actor=actor,
                    audit_hooks=audit_hooks,
                ).as_dict()
            )
        return receipts


__all__ = [
    "EscrowRelease",
    "GrantDisbursement",
    "InstitutionalWallet",
    "MonetizationEngine",
    "MonetizationSimulation",
    "RoyaltyStream",
    "SubscriptionCharge",
]
