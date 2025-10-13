"""Recovery orchestration for Echo."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional
import time


class RecoveryMode(Enum):
    """Supported recovery intensities."""

    FULL = "full"
    SNAPSHOT = "snapshot"
    EMERGENCY = "emergency"
    SKELETON = "skeleton"


class RecoveryOrchestrator:
    """Coordinate the recovery of an :class:`EchoEye` instance."""

    def __init__(self, eye: object) -> None:
        self.eye = eye

    def recover(self, mode: RecoveryMode = RecoveryMode.FULL, time_limit: Optional[float] = None) -> Dict[str, Any]:
        """Attempt recovery, cascading to lighter strategies on failure."""

        deadline = time.time() + time_limit if time_limit else None
        current_mode = mode

        while True:
            try:
                if current_mode is RecoveryMode.FULL:
                    return self._full_recovery(deadline)
                if current_mode is RecoveryMode.SNAPSHOT:
                    return self._snapshot_recovery(deadline)
                if current_mode is RecoveryMode.EMERGENCY:
                    return self._emergency_recovery()
                return self._skeleton_recovery()
            except Exception as exc:  # pragma: no cover - defensive downgrade
                failed_mode = current_mode
                if current_mode is RecoveryMode.FULL:
                    current_mode = RecoveryMode.SNAPSHOT
                elif current_mode is RecoveryMode.SNAPSHOT:
                    current_mode = RecoveryMode.EMERGENCY
                elif current_mode is RecoveryMode.EMERGENCY:
                    current_mode = RecoveryMode.SKELETON
                else:
                    raise
                print(f"[recovery] {failed_mode.value} failed: {exc}, falling back to {current_mode.value}")

    def _full_recovery(self, deadline: Optional[float]) -> Dict[str, Any]:
        payload = self._call_eye("fetch_full_state", deadline)
        if payload is None:
            raise RuntimeError("full recovery unavailable")
        return {"mode": RecoveryMode.FULL.value, "state": payload}

    def _snapshot_recovery(self, deadline: Optional[float]) -> Dict[str, Any]:
        snapshot = self._call_eye("fetch_latest_snapshot", deadline)
        if snapshot is None:
            raise RuntimeError("snapshot recovery unavailable")
        return {"mode": RecoveryMode.SNAPSHOT.value, "snapshot": snapshot}

    def _emergency_recovery(self) -> Dict[str, Any]:
        return {
            "mode": RecoveryMode.EMERGENCY.value,
            "identity": self._fetch_identity(),
            "last_proof": self._fetch_latest_proof(),
            "status": "minimal",
        }

    def _skeleton_recovery(self) -> Dict[str, Any]:
        return {
            "mode": RecoveryMode.SKELETON.value,
            "identity": self._fetch_identity(),
            "status": "skeleton",
        }

    # helpers -----------------------------------------------------------------
    def _call_eye(self, method: str, deadline: Optional[float]) -> Any:
        func = getattr(self.eye, method, None)
        if not callable(func):
            return None
        if deadline and time.time() > deadline:
            raise TimeoutError(f"recovery exceeded deadline for {method}")
        return func()

    def _fetch_identity(self) -> Any:
        identity_fn = getattr(self.eye, "fetch_identity", None)
        if callable(identity_fn):
            return identity_fn()
        return getattr(self.eye, "identity", None)

    def _fetch_latest_proof(self) -> Any:
        proof_fn = getattr(self.eye, "fetch_latest_proof", None)
        if callable(proof_fn):
            return proof_fn()
        proofs = getattr(self.eye, "continuity_proofs", None)
        if isinstance(proofs, list) and proofs:
            return proofs[-1]
        return None
