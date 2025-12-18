"""Internal python modules used by the Echo toolkit test-suite."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from .harmonic_cognition import HarmonicResponse, HarmonicSettings, harmonic_cognition  # noqa: E402
from .consciousness_bridge import ConsciousnessBridge, ConsciousnessBridgeState, Interaction  # noqa: E402

__all__ = [
    "EllegatoAI",
    "ConsciousnessBridge",
    "ConsciousnessBridgeState",
    "HarmonicResponse",
    "HarmonicSettings",
    "harmonic_cognition",
    "Interaction",
    "MemoryHashFeed",
    "Snapshot",
    "SigilQRGenerator",
    "ScanDecoder",
    "ScanPayload",
    "DecodedResponse",
    "build_decoder",
    "create_app",
]

_IMPORT_MAP = {
    "EllegatoAI": ("ellegato_ai", "EllegatoAI"),
    "ConsciousnessBridge": ("consciousness_bridge", "ConsciousnessBridge"),
    "ConsciousnessBridgeState": ("consciousness_bridge", "ConsciousnessBridgeState"),
    "HarmonicResponse": ("harmonic_cognition", "HarmonicResponse"),
    "HarmonicSettings": ("harmonic_cognition", "HarmonicSettings"),
    "harmonic_cognition": ("harmonic_cognition", "harmonic_cognition"),
    "Interaction": ("consciousness_bridge", "Interaction"),
    "MemoryHashFeed": ("memory_hash_feed", "MemoryHashFeed"),
    "Snapshot": ("memory_hash_feed", "Snapshot"),
    "SigilQRGenerator": ("sigil_qr_generator", "SigilQRGenerator"),
    "ScanDecoder": ("scan_decoder", "ScanDecoder"),
    "ScanPayload": ("scan_decoder", "ScanPayload"),
    "DecodedResponse": ("scan_decoder", "DecodedResponse"),
    "build_decoder": ("scan_decoder", "build_decoder"),
    "create_app": ("scan_decoder", "create_app"),
}

_OPTIONAL_MESSAGES = {
    "sigil_qr_generator": "SigilQRGenerator requires the optional 'numpy' dependency",
    "scan_decoder": "Scan decoder utilities require the optional 'fastapi' dependency",
}

_DEPENDENCY_HINTS = {
    "numpy": "SigilQRGenerator requires the optional 'numpy' dependency",
    "fastapi": "Scan decoder utilities require the optional 'fastapi' dependency",
}


def __getattr__(name: str) -> Any:  # pragma: no cover - simple import hook
    if name not in _IMPORT_MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _IMPORT_MAP[name]
    try:
        module = import_module(f".{module_name}", __name__)
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency missing
        message = _OPTIONAL_MESSAGES.get(module_name) or _DEPENDENCY_HINTS.get(exc.name)
        if message:
            raise ModuleNotFoundError(message) from exc
        raise

    value = getattr(module, attr_name)
    globals()[name] = value
    return value
