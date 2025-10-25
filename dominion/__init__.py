"""Dominion orchestration layer for outward projection workflows.

This package provides tooling for compiling *action intents* emitted by the
Singularity runtime into actionable :class:`~dominion.plans.DominionPlan`
instances, applying those plans with audit-friendly journaling and receipt
tracking, and archiving the resulting state in signed bundles.

The module exposes high-level entry points through ``python -m dominion.plan``,
``python -m dominion.apply`` and ``python -m dominion.archive`` commands.
"""

from .plans import ActionIntent, DominionPlan
from .executor import PlanExecutor
from .policy import PolicyEngine, AllowlistPolicy, RedactionPolicy, IdempotencyPolicy

__all__ = [
    "ActionIntent",
    "DominionPlan",
    "PlanExecutor",
    "PolicyEngine",
    "AllowlistPolicy",
    "RedactionPolicy",
    "IdempotencyPolicy",
]
