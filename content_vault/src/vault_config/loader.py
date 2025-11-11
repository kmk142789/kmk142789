"""Loader for JSON/YAML configuration files with version tracking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .events import ConfigRegistry

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover - handled in fallback
    yaml = None


class ConfigLoader:
    """Loads configuration files, validates them, and tracks versions."""

    def __init__(self, schema_path: Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        self.base_dir = base_dir
        self.schema_path = schema_path or (base_dir / "schema" / "config.schema.json")
        self.registry = ConfigRegistry()
        self.changelog_path = base_dir / "configs" / "changelog.md"
        self.current_version = 0

    def load(self, path: Path) -> Dict[str, Any]:
        raw = self._parse(path)
        self._validate(raw)
        version = int(raw["version"])
        record = self.registry.register(version, path, raw)
        self.current_version = version
        self._write_changelog(record.to_dict())
        return raw

    def rollback(self, version: int) -> Dict[str, Any]:
        rolled = self.registry.rollback(version)
        self._write_changelog(rolled, suffix=" (rollback)")
        return rolled

    def _parse(self, path: Path) -> Dict[str, Any]:
        text = path.read_text()
        if path.suffix in {".yaml", ".yml"}:
            if yaml is not None:
                data = yaml.safe_load(text)
            else:
                data = self._minimal_yaml(text)
        else:
            data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("configuration file must decode to an object")
        return data

    def _validate(self, data: Dict[str, Any]) -> None:
        required_top_level = {"version", "services", "events", "dependencies"}
        missing = required_top_level - data.keys()
        if missing:
            raise ValueError(f"missing required keys: {', '.join(sorted(missing))}")

        if not isinstance(data["version"], int) or data["version"] < 1:
            raise ValueError("'version' must be a positive integer")

        services = data["services"]
        if not isinstance(services, dict):
            raise ValueError("'services' must be an object")
        for section in ("storage", "metadata", "history"):
            if section not in services:
                raise ValueError(f"services.{section} missing")

        events = data["events"]
        if not isinstance(events, list):
            raise ValueError("'events' must be an array")
        for event in events:
            if not isinstance(event, dict) or "id" not in event or "type" not in event:
                raise ValueError("each event requires 'id' and 'type'")

        deps = data["dependencies"]
        if not isinstance(deps, list):
            raise ValueError("'dependencies' must be an array")
        for dep in deps:
            if not isinstance(dep, dict) or "name" not in dep or "version" not in dep:
                raise ValueError("each dependency requires 'name' and 'version'")

    def _minimal_yaml(self, text: str) -> Dict[str, Any]:
        """Very small YAML loader supporting the subset used in configs."""

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

        result: Dict[str, Any] = {}
        stack: list[tuple[int, Dict[str, Any]]] = [(-1, result)]
        for raw_line in text.splitlines():
            line = raw_line.rstrip()
            if not line or line.strip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            key, _, value = line.strip().partition(":")
            value = value.strip()
            while stack and indent <= stack[-1][0]:
                stack.pop()
            current = stack[-1][1]
            if value == "":
                current[key] = {}
                stack.append((indent, current[key]))
            elif value.startswith("-"):
                # simple list of scalars
                items = [item.strip().lstrip("- ") for item in value.split("-") if item]
                current[key] = items
            else:
                current[key] = self._coerce_scalar(value)
        return result

    @staticmethod
    def _coerce_scalar(value: str) -> Any:
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def _write_changelog(self, record: Dict[str, Any], suffix: str = "") -> None:
        self.changelog_path.parent.mkdir(parents=True, exist_ok=True)
        lines = self.changelog_path.read_text().splitlines() if self.changelog_path.exists() else []
        header = [line for line in lines if not line.startswith("- v")]
        if not header:
            header = ["# Configuration Changelog", ""]
        entries = [line for line in lines if line.startswith("- v")]
        source = Path(record["source"]).resolve()
        try:
            source = source.relative_to(self.base_dir)
        except ValueError:
            source = Path(source.name)
        entry = f"- v{record['version']} :: {source}{suffix}"
        if entry not in entries:
            entries.append(entry)
        self.changelog_path.write_text("\n".join(header + entries) + "\n")
