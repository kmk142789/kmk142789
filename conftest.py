"""Test configuration helpers for the kmk142789 repository.

``pytest-asyncio`` versions prior to 0.24 expect every collector passed to its
``pytest_collectstart`` hook to expose an ``obj`` attribute.  ``pytest`` 8
removed that attribute from the ``Package`` collector which triggers an
``AttributeError`` during test collection.  Downgrading either dependency is not
an option for this repository, so we shim the hook to gracefully handle the new
collector API.
"""

from __future__ import annotations

try:
    from _pytest.python import Package
except Exception:  # pragma: no cover - guard against internal API changes.
    Package = None
else:
    if not hasattr(Package, "obj"):
        Package.obj = None

try:
    from pytest_asyncio import plugin as pytest_asyncio_plugin
except Exception:  # pragma: no cover - plugin may be absent in some envs.
    pytest_asyncio_plugin = None
else:
    _ORIGINAL_COLLECTSTART = pytest_asyncio_plugin.pytest_collectstart

    def _safe_pytest_collectstart(*args, **kwargs):
        """Ignore collectors that no longer expose ``obj`` on pytest>=8."""

        collector = kwargs.get("collector")
        if collector is None and args:
            collector = args[0]

        if collector is not None and not hasattr(collector, "obj"):
            # ``pytest-asyncio`` only inspects ``collector.obj``.  Early-return
            # when the attribute is missing so we can remain forward compatible
            # with modern pytest releases.
            return None

        return _ORIGINAL_COLLECTSTART(*args, **kwargs)

    _safe_pytest_collectstart.__kmk142789_patch__ = True
    pytest_asyncio_plugin.pytest_collectstart = _safe_pytest_collectstart
