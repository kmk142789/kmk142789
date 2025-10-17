"""Pulse package exposing both legacy pulse engine and ledger utilities."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from .ledger import PulseLedger, PulseReceipt, create_app

_LEGACY_PATH = Path(__file__).resolve().parent.parent / "pulse.py"
_spec = importlib.util.spec_from_file_location("echo._pulse_legacy", _LEGACY_PATH)
_legacy = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
sys.modules.setdefault(_spec.name, _legacy)
_spec.loader.exec_module(_legacy)  # type: ignore[union-attr]

# Re-export legacy symbols so existing imports continue to work.
for name in getattr(_legacy, "__all__", []):
    globals()[name] = getattr(_legacy, name)

# Provide a stable fallback for modules accessing attributes directly.
sys.modules.setdefault("echo._pulse_legacy", _legacy)

__all__ = list(getattr(_legacy, "__all__", [])) + ["PulseLedger", "PulseReceipt", "create_app"]
