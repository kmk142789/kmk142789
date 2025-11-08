from __future__ import annotations

"""Unified sentience orchestration loop with configurable observability."""

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, MutableMapping, Optional, Protocol, Sequence

from echo.self_sustaining_loop import DecisionResult, ProgressResult, SelfSustainingLoop

try:  # pragma: no cover - guard for optional dependency state
    from echo.pulse_status import EchoCodexKernel
except Exception:  # pragma: no cover - defensive import guard
    EchoCodexKernel = None  # type: ignore[assignment]
else:  # pragma: no cover - import side effect for missing json dependency
    try:
        import echo.echo_codox_kernel as _codex_module
    except Exception:  # pragma: no cover - defensive import guard
        _codex_module = None
    else:
        if not hasattr(_codex_module, "json"):
            _codex_module.json = json


MetricReporter = Callable[[ProgressResult, Mapping[str, Any]], None]
GovernanceHook = Callable[[DecisionResult], None]


class OrchestratorView(Protocol):
    """Minimal protocol describing orchestration utilities."""

    @property
    def latest_decision(self) -> Mapping[str, Any] | None:  # pragma: no cover - Protocol definition only
        """Return the latest orchestration decision, if available."""

    @property
    def manifest_directory(self) -> Path | None:  # pragma: no cover - Protocol definition only
        """Directory where orchestration manifests are stored."""


@dataclass(slots=True)
class UnifiedSentienceConfig:
    """Configuration bundle for :class:`UnifiedSentienceLoop`."""

    profile: str
    progress_actor: str = "automation"
    governance_actor: str = "governance"
    pulse_history: str = "pulse_history.json"
    metrics_window: int = 5
    manifest_limit: int = 30
    resilience_interval_hours: float = 72.0
    resilience_cooldown_hours: float = 6.0

    @classmethod
    def from_mapping(cls, profile: str, payload: Mapping[str, Any]) -> "UnifiedSentienceConfig":
        """Build a configuration object from a raw mapping."""

        defaults = cls(profile=profile)
        return cls(
            profile=profile,
            progress_actor=str(payload.get("progress_actor", defaults.progress_actor)),
            governance_actor=str(payload.get("governance_actor", defaults.governance_actor)),
            pulse_history=str(payload.get("pulse_history", defaults.pulse_history)),
            metrics_window=max(1, int(payload.get("metrics_window", defaults.metrics_window))),
            manifest_limit=max(1, int(payload.get("manifest_limit", defaults.manifest_limit))),
            resilience_interval_hours=float(
                payload.get("resilience_interval_hours", defaults.resilience_interval_hours)
            ),
            resilience_cooldown_hours=float(
                payload.get("resilience_cooldown_hours", defaults.resilience_cooldown_hours)
            ),
        )


class UnifiedSentienceLoop(SelfSustainingLoop):
    """Enhanced orchestration loop with observability and governance hooks."""

    def __init__(
        self,
        root: Path | str,
        config: UnifiedSentienceConfig,
        *,
        orchestrator: OrchestratorView | None = None,
        metrics_reporters: Optional[Iterable[MetricReporter]] = None,
        governance_hooks: Optional[Iterable[GovernanceHook]] = None,
        kernel_factory: Callable[[Path], Any] | None = None,
    ) -> None:
        self.config = config
        self._metrics_reporters: list[MetricReporter] = list(metrics_reporters or [])
        self._governance_hooks: list[GovernanceHook] = list(governance_hooks or [])
        self._orchestrator = orchestrator
        self._kernel_factory = kernel_factory or self._default_kernel_factory

        super().__init__(root)

        pulse_path = Path(config.pulse_history)
        if not pulse_path.is_absolute():
            pulse_path = self.root / pulse_path
        pulse_path.parent.mkdir(parents=True, exist_ok=True)
        self._pulse_path = pulse_path
        self._metrics_window = max(1, int(config.metrics_window))

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_environment(
        cls,
        root: Path | str,
        profile: str,
        *,
        config_dir: Path | str = Path("config/unified_sentience"),
        orchestrator: OrchestratorView | None = None,
        metrics_reporters: Optional[Iterable[MetricReporter]] = None,
        governance_hooks: Optional[Iterable[GovernanceHook]] = None,
        kernel_factory: Callable[[Path], Any] | None = None,
    ) -> "UnifiedSentienceLoop":
        """Instantiate the loop using a profile stored under ``config_dir``."""

        config_path = Path(config_dir) / f"{profile}.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration profile {profile!r} not found at {config_path}")

        payload = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):  # pragma: no cover - defensive guard
            raise TypeError(f"Configuration file {config_path} must contain a mapping")

        config = UnifiedSentienceConfig.from_mapping(profile, payload)
        return cls(
            root,
            config,
            orchestrator=orchestrator,
            metrics_reporters=metrics_reporters,
            governance_hooks=governance_hooks,
            kernel_factory=kernel_factory,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def register_metrics_reporter(self, reporter: MetricReporter) -> None:
        """Add a new metrics reporter invoked after progress updates."""

        self._metrics_reporters.append(reporter)

    def register_governance_hook(self, hook: GovernanceHook) -> None:
        """Add a new governance hook invoked after decisions."""

        self._governance_hooks.append(hook)

    def progress(self, summary: str, *, actor: Optional[str] = None) -> ProgressResult:
        """Record progress and emit metrics via registered reporters."""

        actor_name = actor or self.config.progress_actor
        result = super().progress(summary, actor=actor_name)
        metrics = self._collect_metrics(result)
        for reporter in self._metrics_reporters:
            reporter(result, metrics)
        return result

    def decide(
        self,
        proposal_id: str,
        decision: str,
        *,
        actor: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> DecisionResult:
        """Record a governance decision and invoke hooks."""

        actor_name = actor or self.config.governance_actor
        result = super().decide(proposal_id, decision, actor=actor_name, reason=reason)
        for hook in self._governance_hooks:
            hook(result)
        return result

    def status_report(self) -> Mapping[str, Any]:
        """Return a snapshot of loop, pulse, and orchestration state."""

        loop_state = self._read_json(self.state_path)
        history: Sequence[Mapping[str, Any]] = loop_state.get("history", [])[-self._metrics_window :]
        current_cycle = int(loop_state.get("current_cycle", 0))
        proposal_id = self._proposal_id(max(1, current_cycle))
        proposal, _ = self._load_proposal(proposal_id)

        report: MutableMapping[str, Any] = {
            "profile": self.config.profile,
            "loop": {
                "current_cycle": current_cycle,
                "state_path": str(self.state_path),
                "history_tail": history,
                "active_proposal": {
                    "proposal_id": proposal["proposal_id"],
                    "status": proposal.get("status"),
                    "governance": proposal.get("governance", {}),
                },
            },
            "pulse": self._pulse_snapshot(),
            "orchestration": self._orchestration_snapshot(),
        }
        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _default_kernel_factory(self, pulse_path: Path) -> Any:
        if EchoCodexKernel is None:  # pragma: no cover - environment without dependency
            raise RuntimeError("EchoCodexKernel is unavailable")
        return EchoCodexKernel(pulse_file=str(pulse_path))

    def _collect_metrics(self, result: ProgressResult) -> Mapping[str, Any]:
        loop_state = self._read_json(self.state_path)
        tail = loop_state.get("history", [])[-self._metrics_window :]
        metrics: MutableMapping[str, Any] = {
            "profile": self.config.profile,
            "cycle": result.cycle,
            "proposal_id": result.proposal_id,
            "next_proposal_id": result.next_proposal_id,
            "history_tail": tail,
            "pulse": self._pulse_snapshot(),
            "orchestration": self._orchestration_snapshot(),
        }
        return metrics

    def _pulse_snapshot(self) -> Mapping[str, Any]:
        if EchoCodexKernel is None:
            return {"events": 0, "resonance": None, "status": "unavailable"}

        try:
            kernel = self._kernel_factory(self._pulse_path)
        except Exception as exc:  # pragma: no cover - defensive guard
            return {"events": 0, "resonance": None, "status": "error", "error": str(exc)}

        events = len(getattr(kernel, "history", []) or [])
        resonance_value = None
        if hasattr(kernel, "resonance"):
            try:
                resonance_value = kernel.resonance()
            except Exception as exc:  # pragma: no cover - defensive guard
                resonance_value = f"error: {exc}"
        return {"events": events, "resonance": resonance_value, "status": "ok"}

    def _orchestration_snapshot(self) -> Mapping[str, Any]:
        if not self._orchestrator:
            return {"latest": None, "manifest_directory": None}

        latest = getattr(self._orchestrator, "latest_decision", None)
        if callable(latest):  # pragma: no cover - defensive guard for method-based access
            try:
                latest = latest()
            except TypeError:
                latest = None
        manifest_dir = getattr(self._orchestrator, "manifest_directory", None)
        return {
            "latest": latest,
            "manifest_directory": str(manifest_dir) if manifest_dir else None,
        }


__all__ = [
    "UnifiedSentienceConfig",
    "UnifiedSentienceLoop",
]
