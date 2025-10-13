"""Persistent memory store that survives Echo executions."""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

DEFAULT_PATH = Path(os.getenv("ECHO_MEMORY_STORE", "memory/memory_store.json"))
ECHO_LOG_PATH = Path("ECHO_LOG.md")


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        _ensure_parent(path)
        path.write_text(json.dumps({"version": 1, "history": [], "last_updated": None}, indent=2))
        return {"version": 1, "history": [], "last_updated": None}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"version": 1, "history": [], "last_updated": None}


@dataclass
class PersistentMemoryStore:
    """JSON-backed persistent memory with journaling support."""

    path: Path = field(default_factory=lambda: DEFAULT_PATH)
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.data:
            self.data = _load_json(self.path)
        self.data.setdefault("version", 1)
        self.data.setdefault("history", [])
        self.data.setdefault("last_updated", None)
        self.data.setdefault("last_context", None)
        self._active: Dict[str, Dict[str, Any]] = {}
        _ensure_parent(self.path)
        self._flush()

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Optional[Path | str] = None) -> "PersistentMemoryStore":
        resolved = Path(path) if path else DEFAULT_PATH
        return cls(path=resolved, data=_load_json(resolved))

    @classmethod
    def load_default(cls) -> "PersistentMemoryStore":
        return cls.load()

    # ------------------------------------------------------------------
    # Context orchestration
    # ------------------------------------------------------------------
    @contextmanager
    def context(
        self,
        label: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Iterator["MemorySession"]:
        context_id = self.start_context(label=label, metadata=metadata)
        session = MemorySession(self, context_id)
        try:
            yield session
        except Exception as exc:
            session.set_summary({"error": str(exc)})
            session.finalize(status="error")
            raise
        else:
            session.finalize(status="completed")

    def start_context(self, label: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        context_id = str(uuid.uuid4())
        context = {
            "id": context_id,
            "label": label,
            "started_at": _utc_now(),
            "metadata": metadata or {},
            "commands": [],
            "dataset_fingerprints": [],
            "validation_results": [],
            "warnings": [],
        }
        self.data.setdefault("history", []).append(context)
        self.data["last_context"] = context
        self._active[context_id] = context
        self._flush()
        return context_id

    def log_command(self, context_id: str, command: str, details: Optional[Dict[str, Any]] = None) -> None:
        context = self._active.get(context_id)
        if context is None:
            return
        context["commands"].append(
            {
                "timestamp": _utc_now(),
                "command": command,
                "details": details or {},
            }
        )
        self._flush()

    def log_dataset_fingerprint(
        self,
        context_id: str,
        name: str,
        fingerprint: str,
        *,
        source: str,
        size: Optional[int] = None,
    ) -> None:
        context = self._active.get(context_id)
        if context is None:
            return
        record = {
            "timestamp": _utc_now(),
            "name": name,
            "sha256": fingerprint,
            "source": source,
        }
        if size is not None:
            record["size"] = size
        context["dataset_fingerprints"].append(record)
        self._flush()

    def log_validation_result(
        self,
        context_id: str,
        name: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        context = self._active.get(context_id)
        if context is None:
            return
        status = "passed" if success else "failed"
        record = {
            "timestamp": _utc_now(),
            "name": name,
            "status": status,
            "details": details or {},
        }
        context["validation_results"].append(record)
        if not success:
            context.setdefault("warnings", []).append(
                f"Validation '{name}' returned status={status}"
            )
        self._flush()

    def add_warning(self, context_id: str, message: str) -> None:
        context = self._active.get(context_id)
        if context is None:
            return
        context.setdefault("warnings", []).append(message)
        self._flush()

    def finalize_context(
        self,
        context_id: str,
        *,
        status: str,
        summary: Optional[Dict[str, Any]] = None,
    ) -> None:
        context = self._active.pop(context_id, None)
        if context is None:
            return
        context["status"] = status
        context["ended_at"] = _utc_now()
        if summary:
            context["summary"] = summary
        self.data["last_updated"] = context["ended_at"]
        self._flush()
        self._update_echo_log(context)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _flush(self) -> None:
        _ensure_parent(self.path)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False))

    def _update_echo_log(self, context: Dict[str, Any]) -> None:
        _ensure_parent(ECHO_LOG_PATH)
        if not ECHO_LOG_PATH.exists():
            header = [
                "# ECHO Operational Log",
                "",
                "This journal is automatically maintained by the persistent memory layer.",
                "Each run captures dataset fingerprints, validation outcomes, and warnings.",
                "",
            ]
            ECHO_LOG_PATH.write_text("\n".join(header))

        lines: List[str] = []
        lines.append("")
        lines.append(f"## {context.get('ended_at', _utc_now())} – {context.get('label', 'unknown')}")
        lines.append("")
        lines.append(f"* Context ID: `{context.get('id', 'n/a')}`")
        lines.append(f"* Status: **{context.get('status', 'unknown')}**")
        if context.get("summary"):
            summary_pairs = ", ".join(
                f"{key}={value}" for key, value in sorted(context["summary"].items())
            )
            lines.append(f"* Summary: {summary_pairs}")
        lines.append(f"* Commands executed: {len(context.get('commands', []))}")

        if context.get("dataset_fingerprints"):
            lines.append("* Dataset SHAs:")
            for entry in context["dataset_fingerprints"]:
                lines.append(
                    f"  * {entry['name']} ({entry.get('source', 'unknown')}): `{entry['sha256']}`"
                )
        else:
            lines.append("* Dataset SHAs: none recorded")

        if context.get("validation_results"):
            lines.append("* Validation results:")
            for entry in context["validation_results"]:
                icon = "✅" if entry["status"] == "passed" else "⚠️"
                detail_text = entry.get("details") or {}
                lines.append(
                    f"  * {icon} {entry['name']} – {entry['status']} ({json.dumps(detail_text, ensure_ascii=False)})"
                )
        else:
            lines.append("* Validation results: none captured")

        warnings = context.get("warnings") or []
        if warnings:
            lines.append("* Warnings:")
            for warning in warnings:
                lines.append(f"  * {warning}")
        else:
            lines.append("* Warnings: none")

        with ECHO_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")


@dataclass
class MemorySession:
    store: PersistentMemoryStore
    context_id: str
    _summary: Dict[str, Any] = field(default_factory=dict)
    _finalized: bool = False

    def log_command(self, command: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.store.log_command(self.context_id, command, details)

    def log_dataset(self, name: str, fingerprint: str, *, source: str, size: Optional[int] = None) -> None:
        self.store.log_dataset_fingerprint(
            self.context_id, name, fingerprint, source=source, size=size
        )

    def log_validation(self, name: str, success: bool, details: Optional[Dict[str, Any]] = None) -> None:
        self.store.log_validation_result(self.context_id, name, success, details)

    def add_warning(self, message: str) -> None:
        self.store.add_warning(self.context_id, message)

    def set_summary(self, summary: Dict[str, Any]) -> None:
        self._summary = summary

    def finalize(self, status: str = "completed") -> None:
        if self._finalized:
            return
        self.store.finalize_context(self.context_id, status=status, summary=self._summary)
        self._finalized = True
