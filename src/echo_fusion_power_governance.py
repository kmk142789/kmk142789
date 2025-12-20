"""Power governance layer for the Echo Fusion Drone.

This module balances multi-source energy inputs, enforces hard constraints,
applies derating logic, and allocates power by mode without claiming energy
creation. All gains are attributable to known physical mechanisms (e.g. solar
irradiance, thermal gradients, kinetic recovery, regenerative braking).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def _clamp(value: float, low: float = 0.0, high: Optional[float] = None) -> float:
    if high is not None:
        return max(low, min(high, value))
    return max(low, value)


class PowerMode:
    """Named power allocation modes for the Echo Fusion Drone."""

    IDLE = "IDLE"
    CRUISE = "CRUISE"
    HOVER = "HOVER"
    BOOST = "BOOST"
    EMERGENCY = "EMERGENCY"


@dataclass
class PowerSourceTelemetry:
    """Incoming telemetry describing available power from physical sources."""

    battery_w: float = 0.0
    solar_w: float = 0.0
    thermal_w: float = 0.0
    kinetic_w: float = 0.0
    regenerative_w: float = 0.0
    battery_soc: float = 1.0
    battery_temp_c: float = 25.0
    system_temp_c: float = 25.0
    solar_irradiance: float = 1.0
    thermal_gradient: float = 1.0
    kinetic_intensity: float = 1.0
    regen_efficiency: float = 1.0

    def total_requested(self) -> float:
        return (
            self.battery_w
            + self.solar_w
            + self.thermal_w
            + self.kinetic_w
            + self.regenerative_w
        )


@dataclass
class PowerConstraints:
    """Hard safety limits for the power governance layer."""

    max_battery_w: float = 1200.0
    max_solar_w: float = 450.0
    max_thermal_w: float = 180.0
    max_kinetic_w: float = 220.0
    max_regenerative_w: float = 260.0
    max_total_w: float = 1600.0
    min_battery_reserve_soc: float = 0.15
    max_battery_temp_c: float = 55.0
    max_system_temp_c: float = 70.0


@dataclass
class PowerModeProfile:
    """Desired allocation profile for a flight mode."""

    propulsion_weight: float
    avionics_weight: float
    payload_weight: float
    thermal_weight: float
    min_propulsion_w: float = 0.0
    min_avionics_w: float = 60.0
    min_payload_w: float = 0.0
    min_thermal_w: float = 20.0

    def weights(self) -> Dict[str, float]:
        return {
            "propulsion": self.propulsion_weight,
            "avionics": self.avionics_weight,
            "payload": self.payload_weight,
            "thermal": self.thermal_weight,
        }

    def minimums(self) -> Dict[str, float]:
        return {
            "propulsion": self.min_propulsion_w,
            "avionics": self.min_avionics_w,
            "payload": self.min_payload_w,
            "thermal": self.min_thermal_w,
        }


@dataclass
class PowerAllocationResult:
    """Result of a power allocation cycle."""

    timestamp: str
    mode: str
    contributions_w: Dict[str, float]
    allocations_w: Dict[str, float]
    total_available_w: float
    total_allocated_w: float
    unallocated_w: float
    anomalies: List[str] = field(default_factory=list)


class PowerEvidenceLedger:
    """Append-only evidence ledger with hash chaining for auditability."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = "GENESIS"
        if self.path.exists():
            self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        last_hash = "GENESIS"
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                last_hash = record.get("hash", last_hash)
        return last_hash

    def append(self, entry: Dict[str, object]) -> str:
        entry_with_chain = {
            **entry,
            "prev_hash": self._last_hash,
        }
        digest = hashlib.sha256(
            json.dumps(entry_with_chain, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()
        entry_with_chain["hash"] = digest
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry_with_chain, sort_keys=True) + "\n")
        self._last_hash = digest
        return digest


class PowerGovernanceLayer:
    """Govern multi-source power flows for the Echo Fusion Drone."""

    def __init__(
        self,
        *,
        constraints: Optional[PowerConstraints] = None,
        profiles: Optional[Dict[str, PowerModeProfile]] = None,
        ledger_path: Optional[Path] = None,
    ) -> None:
        self.constraints = constraints or PowerConstraints()
        self.profiles = profiles or self._default_profiles()
        self.ledger = PowerEvidenceLedger(
            ledger_path or Path("artifacts") / "echo_fusion_power_ledger.jsonl"
        )
        self._last_mode: Optional[str] = None

    def evaluate(self, telemetry: PowerSourceTelemetry, mode: str) -> PowerAllocationResult:
        anomalies: List[str] = []
        derated = self._apply_derating(telemetry, anomalies)
        total_available = sum(derated.values())
        if total_available > self.constraints.max_total_w:
            anomalies.append("total_available_capped")
            scale = self.constraints.max_total_w / total_available
            for key in derated:
                derated[key] *= scale
            total_available = self.constraints.max_total_w

        allocations, unmet = self._allocate(mode, total_available)
        if unmet > 0:
            anomalies.append("minimum_allocation_shortfall")

        total_allocated = sum(allocations.values())
        if total_allocated > total_available:
            anomalies.append("allocation_overflow_scaled")
            scale = total_available / total_allocated if total_allocated > 0 else 0.0
            for key in allocations:
                allocations[key] *= scale
            total_allocated = sum(allocations.values())

        unallocated = max(0.0, total_available - total_allocated)
        timestamp = _utc_timestamp()
        result = PowerAllocationResult(
            timestamp=timestamp,
            mode=mode,
            contributions_w=derated,
            allocations_w=allocations,
            total_available_w=total_available,
            total_allocated_w=total_allocated,
            unallocated_w=unallocated,
            anomalies=anomalies,
        )
        self._record_allocation(result, telemetry)
        return result

    def _apply_derating(
        self, telemetry: PowerSourceTelemetry, anomalies: List[str]
    ) -> Dict[str, float]:
        constraints = self.constraints
        battery_soc = _clamp(telemetry.battery_soc, 0.0, 1.0)
        if telemetry.battery_soc < 0.0 or telemetry.battery_soc > 1.0:
            anomalies.append("battery_soc_out_of_range")

        reserve = constraints.min_battery_reserve_soc
        if battery_soc <= reserve:
            battery_factor = 0.0
        else:
            battery_factor = (battery_soc - reserve) / max(1e-6, 1.0 - reserve)

        if telemetry.battery_temp_c > constraints.max_battery_temp_c:
            anomalies.append("battery_temp_derate")
            battery_factor *= _clamp(
                1.0 - (telemetry.battery_temp_c - constraints.max_battery_temp_c) / 20.0,
                0.2,
                1.0,
            )

        system_factor = 1.0
        if telemetry.system_temp_c > constraints.max_system_temp_c:
            anomalies.append("system_temp_derate")
            system_factor = _clamp(
                1.0 - (telemetry.system_temp_c - constraints.max_system_temp_c) / 25.0,
                0.3,
                1.0,
            )

        contributions = {
            "battery": self._cap_source(
                telemetry.battery_w,
                constraints.max_battery_w,
                anomalies,
                "battery",
            )
            * battery_factor,
            "solar": self._cap_source(
                telemetry.solar_w,
                constraints.max_solar_w,
                anomalies,
                "solar",
            )
            * _clamp(telemetry.solar_irradiance, 0.0, 1.0),
            "thermal": self._cap_source(
                telemetry.thermal_w,
                constraints.max_thermal_w,
                anomalies,
                "thermal",
            )
            * _clamp(telemetry.thermal_gradient, 0.0, 1.0),
            "kinetic": self._cap_source(
                telemetry.kinetic_w,
                constraints.max_kinetic_w,
                anomalies,
                "kinetic",
            )
            * _clamp(telemetry.kinetic_intensity, 0.0, 1.0),
            "regenerative": self._cap_source(
                telemetry.regenerative_w,
                constraints.max_regenerative_w,
                anomalies,
                "regenerative",
            )
            * _clamp(telemetry.regen_efficiency, 0.0, 1.0),
        }

        if system_factor != 1.0:
            for key in contributions:
                contributions[key] *= system_factor
        return contributions

    def _cap_source(
        self,
        value: float,
        max_value: float,
        anomalies: List[str],
        name: str,
    ) -> float:
        if value < 0.0:
            anomalies.append(f"{name}_negative_input")
            return 0.0
        if value > max_value:
            anomalies.append(f"{name}_input_capped")
            return max_value
        return value

    def _allocate(self, mode: str, total_available: float) -> tuple[Dict[str, float], float]:
        profile = self.profiles.get(mode)
        if profile is None:
            profile = self.profiles[PowerMode.IDLE]
        weights = profile.weights()
        minimums = profile.minimums()
        min_total = sum(minimums.values())
        allocations = dict(minimums)
        remaining = max(0.0, total_available - min_total)
        weight_sum = sum(weights.values())
        for key, weight in weights.items():
            if weight_sum > 0.0:
                allocations[key] += remaining * (weight / weight_sum)
        unmet = max(0.0, min_total - total_available)
        if unmet > 0.0:
            scale = total_available / min_total if min_total > 0 else 0.0
            for key in allocations:
                allocations[key] *= scale
        return allocations, unmet

    def _record_allocation(
        self, result: PowerAllocationResult, telemetry: PowerSourceTelemetry
    ) -> None:
        if result.mode != self._last_mode:
            self.ledger.append(
                {
                    "timestamp": result.timestamp,
                    "event": "mode_transition",
                    "from_mode": self._last_mode,
                    "to_mode": result.mode,
                }
            )
            self._last_mode = result.mode

        self.ledger.append(
            {
                "timestamp": result.timestamp,
                "event": "power_allocation",
                "mode": result.mode,
                "telemetry": asdict(telemetry),
                "contributions_w": result.contributions_w,
                "allocations_w": result.allocations_w,
                "total_available_w": result.total_available_w,
                "total_allocated_w": result.total_allocated_w,
                "unallocated_w": result.unallocated_w,
                "anomalies": list(result.anomalies),
                "energy_conservation_note": (
                    "Total allocated power is clamped to available input after derating."
                ),
            }
        )
        if result.anomalies:
            self.ledger.append(
                {
                    "timestamp": result.timestamp,
                    "event": "anomaly",
                    "mode": result.mode,
                    "anomalies": list(result.anomalies),
                    "inputs_total_w": telemetry.total_requested(),
                    "available_total_w": result.total_available_w,
                }
            )

    @staticmethod
    def _default_profiles() -> Dict[str, PowerModeProfile]:
        return {
            PowerMode.IDLE: PowerModeProfile(
                propulsion_weight=0.2,
                avionics_weight=0.5,
                payload_weight=0.1,
                thermal_weight=0.2,
                min_propulsion_w=0.0,
                min_payload_w=0.0,
            ),
            PowerMode.CRUISE: PowerModeProfile(
                propulsion_weight=0.6,
                avionics_weight=0.2,
                payload_weight=0.1,
                thermal_weight=0.1,
                min_propulsion_w=200.0,
                min_payload_w=50.0,
            ),
            PowerMode.HOVER: PowerModeProfile(
                propulsion_weight=0.7,
                avionics_weight=0.15,
                payload_weight=0.05,
                thermal_weight=0.1,
                min_propulsion_w=320.0,
                min_payload_w=20.0,
            ),
            PowerMode.BOOST: PowerModeProfile(
                propulsion_weight=0.8,
                avionics_weight=0.1,
                payload_weight=0.05,
                thermal_weight=0.05,
                min_propulsion_w=420.0,
                min_payload_w=0.0,
            ),
            PowerMode.EMERGENCY: PowerModeProfile(
                propulsion_weight=0.4,
                avionics_weight=0.4,
                payload_weight=0.0,
                thermal_weight=0.2,
                min_propulsion_w=120.0,
                min_payload_w=0.0,
            ),
        }


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
