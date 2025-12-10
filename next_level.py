"""Shim module to expose ``packages/core/src/next_level.py`` as ``next_level``.

The repository keeps the implementation under ``packages/core/src`` so unit
tests can import it directly after ``sitecustomize`` adjusts ``sys.path``.
Regular Python invocations do not automatically load ``sitecustomize``, which
makes ``python -m next_level`` fail outside the test harness.  This thin wrapper
loads the underlying module manually and re-exports its public attributes,
keeping CLI usage and imports working without extra environment tweaks.
"""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import Iterable
import sys

_CORE_IMPL = Path(__file__).resolve().parent / "packages" / "core" / "src" / "next_level.py"

_spec = spec_from_file_location("_next_level_impl", _CORE_IMPL)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Unable to load next_level implementation from {_CORE_IMPL}")

_core_module = module_from_spec(_spec)
sys.modules[_spec.name] = _core_module
_spec.loader.exec_module(_core_module)

__doc__ = _core_module.__doc__


def _export_public_members(module) -> Iterable[str]:
    if hasattr(module, "__all__"):
        return module.__all__  # type: ignore[attr-defined]
    return [name for name in dir(module) if not name.startswith("_")]


for _name in _export_public_members(_core_module):
    globals()[_name] = getattr(_core_module, _name)

__all__ = tuple(_export_public_members(_core_module))


if __name__ == "__main__":
    raise SystemExit(_core_module.main())
