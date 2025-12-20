from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ..utils import Finding, isoformat


@dataclass(frozen=True)
class SLAWindow:
    label: str
    days: int

    def deadline(self, now: datetime) -> datetime:
        return now - timedelta(days=self.days)


class AutonomousWatcherProbe:
    name = "autonomous-watcher"

    def __init__(
        self,
        dns_sla_days: int | None = None,
        drone_sla_days: int | None = None,
        governance_sla_days: int | None = None,
    ) -> None:
        self.dns_sla = SLAWindow("dns", dns_sla_days or _env_days("SENTINEL_DNS_SLA_DAYS", 7))
        self.drone_sla = SLAWindow("drone", drone_sla_days or _env_days("SENTINEL_DRONE_SLA_DAYS", 14))
        self.governance_sla = SLAWindow(
            "governance", governance_sla_days or _env_days("SENTINEL_GOVERNANCE_SLA_DAYS", 30)
        )

    def run(self, inventory: dict[str, Any]) -> list[Finding]:
        findings: list[Finding] = []
        now = datetime.now(tz=timezone.utc)
        findings.extend(self._check_dns(now))
        findings.extend(self._check_drone_artifacts(now))
        findings.extend(self._check_governance(inventory, now))
        return findings

    def _check_dns(self, now: datetime) -> list[Finding]:
        findings: list[Finding] = []
        tokens_path = Path("dns_tokens.txt")
        domains_path = Path("domains.txt")
        attestation_dir = Path("attestations/dns")

        if not tokens_path.exists():
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(tokens_path),
                    status="error",
                    message="DNS SLA breach: dns_tokens.txt is missing",
                    data={"expected": str(tokens_path)},
                )
            )
            return findings

        tokens_age = _file_age_days(tokens_path, now)
        if tokens_age is not None and tokens_age > self.dns_sla.days:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(tokens_path),
                    status="warning",
                    message="DNS drift detected: token snapshot older than SLA window",
                    data={"age_days": tokens_age, "sla_days": self.dns_sla.days},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(tokens_path),
                    status="ok",
                    message="DNS token snapshot is within SLA window",
                    data={"age_days": tokens_age, "sla_days": self.dns_sla.days},
                )
            )

        if domains_path.exists():
            missing_domains = _domains_missing_in_tokens(domains_path, tokens_path)
            if missing_domains:
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=str(domains_path),
                        status="warning",
                        message="DNS drift detected: domains missing from token snapshot",
                        data={"missing_domains": missing_domains},
                    )
                )

        attestation_files = sorted(attestation_dir.glob("*")) if attestation_dir.exists() else []
        if not attestation_files:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(attestation_dir),
                    status="error",
                    message="Missing DNS attestation artifacts",
                    data={"expected_dir": str(attestation_dir)},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(attestation_dir),
                    status="ok",
                    message="DNS attestation artifacts detected",
                    data={"count": len(attestation_files)},
                )
            )

        return findings

    def _check_drone_artifacts(self, now: datetime) -> list[Finding]:
        findings: list[Finding] = []
        artifacts_dir = Path("artifacts")
        if not artifacts_dir.exists():
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(artifacts_dir),
                    status="error",
                    message="Drone artifact repository missing",
                    data={"expected_dir": str(artifacts_dir)},
                )
            )
            return findings

        drone_artifacts = sorted(
            path for path in artifacts_dir.rglob("*") if path.is_file() and "drone" in path.name.lower()
        )
        if not drone_artifacts:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(artifacts_dir),
                    status="error",
                    message="Missing drone artifacts for SLA monitoring",
                    data={"search_hint": "*drone*"},
                )
            )
            return findings

        stale_artifacts: list[str] = []
        for artifact in drone_artifacts:
            age_days = _file_age_days(artifact, now)
            if age_days is not None and age_days > self.drone_sla.days:
                stale_artifacts.append(str(artifact))
        if stale_artifacts:
            findings.append(
                Finding(
                    probe=self.name,
                    subject="drone-artifacts",
                    status="warning",
                    message="Drone artifact drift detected: artifacts older than SLA window",
                    data={"sla_days": self.drone_sla.days, "artifacts": stale_artifacts},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject="drone-artifacts",
                    status="ok",
                    message="Drone artifacts are within SLA window",
                    data={"count": len(drone_artifacts), "sla_days": self.drone_sla.days},
                )
            )

        attestation_dir = Path("attestations")
        drone_attestations = (
            [path for path in attestation_dir.glob("*drone*") if path.is_file()] if attestation_dir.exists() else []
        )
        if not drone_attestations:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(attestation_dir),
                    status="error",
                    message="Missing drone attestations",
                    data={"expected_pattern": "*drone*"},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(attestation_dir),
                    status="ok",
                    message="Drone attestation artifacts detected",
                    data={"count": len(drone_attestations)},
                )
            )

        return findings

    def _check_governance(self, inventory: dict[str, Any], now: datetime) -> list[Finding]:
        findings: list[Finding] = []
        registry_path = Path("governance/echo_governance.json")
        if not registry_path.exists():
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(registry_path),
                    status="error",
                    message="Governance registry is missing",
                    data={"expected": str(registry_path)},
                )
            )
            return findings

        governance_data = _load_json(registry_path)
        review_schedule = governance_data.get("review_schedule", {}) if isinstance(governance_data, dict) else {}
        next_review_iso = review_schedule.get("next_review_iso") if isinstance(review_schedule, dict) else None
        review_at = _parse_iso(next_review_iso)

        if review_at is None:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(registry_path),
                    status="warning",
                    message="Governance review schedule missing or invalid",
                    data={"next_review_iso": next_review_iso},
                )
            )
        elif review_at < now:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(registry_path),
                    status="error",
                    message="Governance SLA breach: review schedule overdue",
                    data={"next_review_iso": next_review_iso, "evaluated_at": isoformat(now)},
                )
            )
        else:
            findings.append(
                Finding(
                    probe=self.name,
                    subject=str(registry_path),
                    status="ok",
                    message="Governance review schedule is within SLA window",
                    data={"next_review_iso": next_review_iso},
                )
            )

        fragments = inventory.get("registry", {}).get("fragments", [])
        for fragment in fragments:
            if not isinstance(fragment, dict):
                continue
            subject = fragment.get("name") or fragment.get("slug") or "registry-fragment"
            proof = fragment.get("proof")
            last_seen = _parse_iso(fragment.get("last_seen"))
            if not proof:
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=str(subject),
                        status="error",
                        message="Governance attestation missing for registry fragment",
                        data={"fragment": fragment},
                    )
                )
            if last_seen is None:
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=str(subject),
                        status="warning",
                        message="Governance registry fragment missing last_seen timestamp",
                        data={"fragment": fragment},
                    )
                )
                continue
            if last_seen < self.governance_sla.deadline(now):
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=str(subject),
                        status="error",
                        message="Governance SLA breach: registry fragment stale",
                        data={
                            "last_seen": fragment.get("last_seen"),
                            "sla_days": self.governance_sla.days,
                            "evaluated_at": isoformat(now),
                        },
                    )
                )
            else:
                findings.append(
                    Finding(
                        probe=self.name,
                        subject=str(subject),
                        status="ok",
                        message="Governance registry fragment within SLA window",
                        data={"last_seen": fragment.get("last_seen"), "sla_days": self.governance_sla.days},
                    )
                )

        return findings


def _env_days(name: str, fallback: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return fallback
    try:
        parsed = int(value)
    except ValueError:
        return fallback
    return parsed if parsed > 0 else fallback


def _file_age_days(path: Path, now: datetime) -> int | None:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except FileNotFoundError:
        return None
    return max(0, (now - mtime).days)


def _domains_missing_in_tokens(domains_path: Path, tokens_path: Path) -> list[str]:
    try:
        domains_raw = domains_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    tokens_raw = tokens_path.read_text(encoding="utf-8") if tokens_path.exists() else ""
    missing = []
    for line in domains_raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped not in tokens_raw:
            missing.append(stripped)
    return missing


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _load_json(path: Path) -> dict[str, Any]:
    data = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        return {"error": "invalid-json", "path": str(path)}
    if isinstance(payload, dict):
        return payload
    return {"data": payload}


__all__ = ["AutonomousWatcherProbe"]
