"""Plugin registry for interpreting textual pay-to-pubkey scripts."""

from __future__ import annotations

import importlib
import importlib.metadata
import pkgutil
import sys
from contextlib import contextmanager
from types import ModuleType
from typing import Iterable, List, Protocol, Sequence

ENTRY_POINT_GROUP = "verifier.pkscript_plugins"


class PkScriptPlugin(Protocol):
    """Protocol implemented by script token transformation plugins."""

    name: str

    def transform(self, tokens: Sequence[str]) -> Sequence[str]:
        """Return a transformed view of ``tokens``.

        Implementations may collapse adjacent tokens, replace recognised
        opcodes with canonical forms, or drop tokens entirely.  The registry
        will feed the output of one plugin into the next, allowing handlers to
        build on top of one another.
        """


_plugins: List[PkScriptPlugin] = []
_loaded = False
_loaded_modules: set[str] = set()


def register_plugin(plugin: PkScriptPlugin, *, prepend: bool = False) -> None:
    """Register ``plugin`` with the global registry."""

    if prepend:
        _plugins.insert(0, plugin)
    else:
        _plugins.append(plugin)


def _remove_plugin(plugin: PkScriptPlugin) -> None:
    for idx, existing in enumerate(_plugins):
        if existing is plugin:
            del _plugins[idx]
            break


def ensure_plugins_loaded() -> None:
    """Load default plugins exactly once."""

    global _loaded

    if _loaded:
        return

    _loaded = True

    _load_entrypoint_plugins()
    _load_package_plugins()


def _load_entrypoint_plugins() -> None:
    try:
        entry_points = importlib.metadata.entry_points()
    except Exception:  # pragma: no cover - defensive guard
        entry_points = ()

    candidates: Iterable = ()
    if hasattr(entry_points, "select"):
        candidates = entry_points.select(group=ENTRY_POINT_GROUP)
    elif isinstance(entry_points, dict):  # pragma: no cover - legacy support
        candidates = entry_points.get(ENTRY_POINT_GROUP, ())
    else:  # pragma: no cover - fallback for unusual implementations
        candidates = entry_points

    for entry_point in candidates:
        try:
            loaded = entry_point.load()
        except Exception:  # pragma: no cover - defensive guard
            continue

        plugin = _coerce_plugin(loaded, getattr(entry_point, "name", "entrypoint"))
        if plugin is not None:
            register_plugin(plugin)


def _load_package_plugins() -> None:
    try:
        package = importlib.import_module("verifier.pkscript_plugins")
    except ModuleNotFoundError:  # pragma: no cover - defensive guard
        return

    paths = getattr(package, "__path__", None)
    if not paths:  # pragma: no cover - defensive guard
        return

    for module_info in pkgutil.iter_modules(paths, package.__name__ + "."):
        if module_info.name in _loaded_modules:
            continue

        try:
            module = importlib.import_module(module_info.name)
        except Exception:  # pragma: no cover - defensive guard
            continue

        _loaded_modules.add(module_info.name)
        _coerce_module_plugins(module)


def _coerce_module_plugins(module: ModuleType) -> None:
    exported = []

    for attr_name in ("PLUGIN", "PLUGINS", "get_plugin", "get_plugins"):
        if hasattr(module, attr_name):
            exported.append(getattr(module, attr_name))

    if not exported and hasattr(module, "__all__"):
        exported = [getattr(module, name) for name in module.__all__]

    if not exported:
        # Fall back to allowing modules to register themselves at import time.
        return

    for candidate in exported:
        plugin = _coerce_plugin(candidate, getattr(module, "__name__", "module"))
        if plugin is not None:
            register_plugin(plugin)


def _coerce_plugin(candidate, default_name: str) -> PkScriptPlugin | None:
    if isinstance(candidate, type):
        candidate = candidate()

    if callable(candidate) and not hasattr(candidate, "transform"):
        candidate = candidate()

    if not hasattr(candidate, "transform"):
        return None

    if not hasattr(candidate, "name"):
        setattr(candidate, "name", default_name)

    return candidate  # type: ignore[return-value]


def canonicalise_tokens(tokens: Sequence[str]) -> List[str]:
    """Return ``tokens`` after applying all registered plugins."""

    ensure_plugins_loaded()

    result = list(tokens)
    for plugin in _plugins:
        result = list(plugin.transform(result))
    return result


def iter_plugins() -> List[PkScriptPlugin]:
    """Return the list of registered plugins (loading them if necessary)."""

    ensure_plugins_loaded()
    return list(_plugins)


def reload_plugins() -> None:
    """Reload plugins from entry points and the built-in plugin package."""

    global _loaded

    ensure_plugins_loaded()

    modules = [sys.modules[name] for name in _loaded_modules if name in sys.modules]

    _plugins.clear()
    _loaded_modules.clear()
    _loaded = False

    for module in modules:
        try:
            importlib.reload(module)
        except Exception:  # pragma: no cover - defensive guard
            continue

    ensure_plugins_loaded()


@contextmanager
def temporary_plugin(plugin: PkScriptPlugin, *, prepend: bool = False):
    """Context manager that installs ``plugin`` for the duration of the block."""

    register_plugin(plugin, prepend=prepend)
    try:
        yield
    finally:
        _remove_plugin(plugin)


__all__ = [
    "PkScriptPlugin",
    "canonicalise_tokens",
    "ensure_plugins_loaded",
    "iter_plugins",
    "register_plugin",
    "reload_plugins",
    "temporary_plugin",
]

