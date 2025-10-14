"""Plugin registry for the Echo Meta Agent."""

from __future__ import annotations

import importlib
import logging
import pkgutil
import sys
from importlib import metadata
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .types import PluginSpec, ToolMap

LOGGER = logging.getLogger(__name__)


PLUGIN_ENTRYPOINT = "echo_meta_agent.plugins"
LOCAL_PATTERNS = [
    "aladdin_app",
    "aladdin_research",
    "nan_intelligence",
    "hardhat_monad",
    "LangGraph-*",
]


class PluginRegistry:
    """Registry that discovers and manages tool plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginSpec] = {}
        self._discovered = False

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def discover(self) -> None:
        """Discover available plugins once."""

        if self._discovered:
            return
        self._load_builtin_adapters()
        self._load_entry_points()
        self._load_local_repositories()
        self._discovered = True

    def _load_builtin_adapters(self) -> None:
        """Load adapters bundled with the package."""

        package = __name__.rsplit(".", 1)[0] + ".adapters"
        for module_info in pkgutil.iter_modules([str(Path(__file__).resolve().parent / "adapters")]):
            module_name = f"{package}.{module_info.name}"
            self._try_register(module_name)

    def _load_entry_points(self) -> None:
        """Load plugins registered through package entry points."""

        try:
            entries = metadata.entry_points(group=PLUGIN_ENTRYPOINT)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.debug("Failed to read entry points: %s", exc)
            return
        for entry in entries:
            try:
                plugin: PluginSpec = entry.load()
            except Exception as exc:  # pragma: no cover - defensive
                LOGGER.warning("Failed to load plugin entry point %s: %s", entry.name, exc)
                continue
            self._register_plugin(plugin)

    def _load_local_repositories(self) -> None:
        """Attempt to discover plugins from known local fork directories."""

        root = Path(__file__).resolve().parents[1]
        sys_path_added: List[str] = []
        for pattern in LOCAL_PATTERNS:
            for path in root.glob(pattern):
                if not path.is_dir():
                    continue
                if str(path) not in sys.path:
                    sys.path.append(str(path))
                    sys_path_added.append(str(path))
                module_candidates = self._candidate_modules(path)
                for module_name in module_candidates:
                    self._try_register(module_name)
        for entry in sys_path_added:
            try:
                sys.path.remove(entry)
            except ValueError:  # pragma: no cover - defensive
                pass

    def _candidate_modules(self, repo_path: Path) -> Iterable[str]:
        base = repo_path.name.replace("-", "_")
        possibilities = [
            f"{base}.echo_meta_plugin",
            f"{base}.meta_plugin",
            f"{base}.plugin",
            f"{base}.plugins",
        ]
        # Fallback: look for top-level module matching repo name
        possibilities.append(base)
        return possibilities

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def _try_register(self, module_name: str) -> None:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            LOGGER.debug("Failed to import %s: %s", module_name, exc)
            return
        plugin = getattr(module, "PLUGIN", None)
        if not plugin:
            LOGGER.debug("Module %s missing PLUGIN spec", module_name)
            return
        self._register_plugin(plugin)

    def _register_plugin(self, plugin: PluginSpec) -> None:
        name = plugin.get("name")
        tools = plugin.get("tools")
        if not name or not isinstance(tools, dict):
            LOGGER.debug("Invalid plugin spec %s", plugin)
            return
        normalized_tools: ToolMap = {}
        for tool_name, tool in tools.items():
            if callable(tool):
                normalized_tools[tool_name] = tool  # type: ignore[assignment]
        if not normalized_tools:
            LOGGER.debug("Plugin %s has no callable tools", name)
            return
        plugin_copy = dict(plugin)
        plugin_copy["tools"] = normalized_tools
        self._plugins[name] = plugin_copy

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def list_plugins(self) -> List[str]:
        """Return available plugin names."""

        self.discover()
        return sorted(self._plugins.keys())

    def list_tools(self, plugin: str) -> List[str]:
        """List tools for *plugin*."""

        self.discover()
        data = self._plugins.get(plugin)
        if not data:
            raise KeyError(f"Plugin '{plugin}' not found")
        return sorted(data["tools"].keys())

    def call(self, plugin: str, tool: str, *args: Any, **kwargs: Any) -> Any:
        """Call the specified tool and return its result."""

        self.discover()
        data = self._plugins.get(plugin)
        if not data:
            raise KeyError(f"Plugin '{plugin}' not found")
        tool_map: ToolMap = data["tools"]
        if tool not in tool_map:
            raise KeyError(f"Tool '{tool}' not found in plugin '{plugin}'")
        return tool_map[tool](*args, **kwargs)


__all__ = ["PluginRegistry"]
