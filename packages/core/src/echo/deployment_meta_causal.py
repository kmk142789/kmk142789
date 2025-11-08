"""Deployment manifest helpers for the meta-causal engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

from ._paths import REPO_ROOT

CONFIG_PATH = REPO_ROOT / "config" / "meta_causal_engine.json"


@dataclass(slots=True)
class MetaCausalRollout:
    """Structured configuration describing the meta-causal engine rollout."""

    enabled: bool = False
    rollout_channel: str = "canary"
    max_parallel_deployments: int = 1
    preflight_checks: List[str] = field(
        default_factory=lambda: [
            "verify-pulse-weaver",
            "atlas-attestations",
            "resonance-sanity",
        ]
    )
    artifact_path: str = "dist/meta_causal_engine/package.json"
    notes: str = "Meta-causal engine staged rollout manifest."

    def to_dict(self) -> Dict[str, object]:
        return {
            "enabled": self.enabled,
            "rollout_channel": self.rollout_channel,
            "max_parallel_deployments": self.max_parallel_deployments,
            "preflight_checks": list(self.preflight_checks),
            "artifact_path": self.artifact_path,
            "notes": self.notes,
        }

    def with_overrides(
        self,
        *,
        enabled: Optional[bool] = None,
        channel: Optional[str] = None,
        max_parallel: Optional[int] = None,
        preflight_checks: Optional[Iterable[str]] = None,
    ) -> "MetaCausalRollout":
        updated = replace(self)
        if enabled is not None:
            updated.enabled = enabled
        if channel is not None:
            updated.rollout_channel = channel
        if max_parallel is not None:
            updated.max_parallel_deployments = max_parallel
        if preflight_checks is not None:
            updated.preflight_checks = list(preflight_checks)
        return updated


def _read_config_payload(path: Path) -> Mapping[str, object]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_meta_causal_config(path: Path = CONFIG_PATH) -> MetaCausalRollout:
    """Load the stored rollout configuration or fall back to defaults."""

    payload = _read_config_payload(path)
    raw = payload.get("meta_causal_engine") if isinstance(payload, Mapping) else None
    if not isinstance(raw, Mapping):
        raw = {}
    enabled = bool(raw.get("enabled", False))
    channel = str(raw.get("rollout_channel", "canary"))
    try:
        max_parallel = int(raw.get("max_parallel_deployments", 1))
    except (TypeError, ValueError):
        max_parallel = 1
    preflight = raw.get("preflight_checks", [])
    if not isinstance(preflight, Iterable) or isinstance(preflight, (str, bytes)):
        preflight_list: List[str] = ["verify-pulse-weaver", "atlas-attestations", "resonance-sanity"]
    else:
        preflight_list = [str(item) for item in preflight]
    artifact = str(raw.get("artifact_path", "dist/meta_causal_engine/package.json"))
    notes = str(raw.get("notes", "Meta-causal engine staged rollout manifest."))
    return MetaCausalRollout(
        enabled=enabled,
        rollout_channel=channel,
        max_parallel_deployments=max_parallel,
        preflight_checks=preflight_list,
        artifact_path=artifact,
        notes=notes,
    )


def save_meta_causal_config(config: MetaCausalRollout, path: Path = CONFIG_PATH) -> Path:
    """Persist the rollout configuration to *path*."""

    payload: Dict[str, object] = {
        "meta_causal_engine": config.to_dict(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def plan_meta_causal_deployment(
    config: MetaCausalRollout,
    *,
    initiated_by: str,
    reason: Optional[str] = None,
) -> Dict[str, object]:
    """Build a deployment plan payload for the given *config*."""

    plan: Dict[str, object] = {
        "engine": "meta-causal-engine",
        "enabled": config.enabled,
        "rollout_channel": config.rollout_channel,
        "max_parallel_deployments": config.max_parallel_deployments,
        "preflight_checks": list(config.preflight_checks),
        "artifact_path": config.artifact_path,
        "initiated_by": initiated_by,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if reason:
        plan["reason"] = reason
    return plan


__all__ = [
    "CONFIG_PATH",
    "MetaCausalRollout",
    "load_meta_causal_config",
    "plan_meta_causal_deployment",
    "save_meta_causal_config",
]
