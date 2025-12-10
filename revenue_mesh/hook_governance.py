"""Governance enforcement hooks for revenue operations."""

import importlib
import importlib.util
import sys
from typing import Callable

core_module = sys.modules.get("echo_governance_core")
if core_module is not None and not hasattr(core_module, "__path__"):
    core_module.__path__ = []  # type: ignore[attr-defined]


def _safe_find_spec(name: str):
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__spec__", None) is None:
        return None
    return importlib.util.find_spec(name)

audit_log_spec = _safe_find_spec("echo_governance_core.audit_log")
if audit_log_spec:
    log_event = importlib.import_module("echo_governance_core.audit_log").log_event
else:
    def log_event(actor, action, meta=None):  # type: ignore[override]
        return {"actor": actor, "action": action, "meta": meta or {}}

policy_engine_spec = _safe_find_spec("echo_governance_core.policy_engine")
policy_engine = importlib.import_module("echo_governance_core.policy_engine") if policy_engine_spec else None


def _enforcer() -> Callable[[str, str], bool]:
    if policy_engine is None:
        return lambda actor, action: True
    return getattr(policy_engine, "enforce", lambda actor, action: True)


def authorize_billing(actor):
    if not _enforcer()(actor, "billing_access"):
        log_event(actor, "billing_denied")
        raise PermissionError("Not authorized for billing")

    log_event(actor, "billing_access")
    return True
