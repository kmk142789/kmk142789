"""Echo Drift Engine: a perpetual-adjacent energy-harvesting state machine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
import hashlib
from typing import Callable, Dict, Iterable, Optional


class DriftPhase:
    """Named phases for the Echo Drift Engine state machine."""

    DORMANT = "S0:DORMANT"
    BOOT_INTEGRITY = "S1:BOOT_INTEGRITY"
    HARVEST_OBSERVE = "S2:HARVEST_OBSERVE"
    WORK_BURST = "S3:WORK_BURST"
    DISTRESS = "S4:DISTRESS"


@dataclass
class EnergyInputs:
    """Energy harvesting inputs for a single observation window."""

    thermal_mw: float = 0.0
    solar_mw: float = 0.0
    vibration_mw: float = 0.0
    rf_mw: float = 0.0

    def total(self) -> float:
        return self.thermal_mw + self.solar_mw + self.vibration_mw + self.rf_mw


@dataclass
class EnergyStore:
    """Represents the device energy reserves."""

    supercap_voltage: float = 0.0
    microcell_charge: float = 0.0

    def as_dict(self) -> Dict[str, float]:
        return asdict(self)


@dataclass
class DriftPolicy:
    """Policy thresholds for the Echo Drift Engine."""

    boot_voltage: float = 2.2
    distress_brownouts: int = 3
    heartbeat_interval: timedelta = timedelta(hours=1)
    observation_cost: float = 0.05
    work_cost: float = 0.2
    upload_surplus: float = 0.5


@dataclass
class HeartbeatProof:
    """Verifiable proof artifact emitted by the engine."""

    device_id: str
    timestamp: str
    energy_bucket: str
    phase: str
    last_proof_hash: str
    signature: str
    fields: Dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class DriftState:
    """Mutable state for the drift engine."""

    phase: str = DriftPhase.DORMANT
    last_proof_hash: str = "GENESIS"
    last_heartbeat: Optional[datetime] = None
    brownout_count: int = 0
    energy_income_rate: float = 0.0
    duty_budget: float = 0.0
    ledgers: Dict[str, list[dict]] = field(
        default_factory=lambda: {
            "heartbeat_ledger": [],
            "event_ledger": [],
            "distress_ledger": [],
        }
    )


class EchoDriftEngine:
    """Perpetual-adjacent engine that schedules proofs based on energy."""

    def __init__(
        self,
        *,
        device_id: str,
        store: Optional[EnergyStore] = None,
        policy: Optional[DriftPolicy] = None,
        signer: Optional[Callable[[str], str]] = None,
        time_source: Optional[Callable[[], datetime]] = None,
        ledger_capacity: int = 256,
    ) -> None:
        self.device_id = device_id
        self.store = store or EnergyStore()
        self.policy = policy or DriftPolicy()
        self.state = DriftState()
        self.ledger_capacity = ledger_capacity
        self.signer = signer or self._default_signer
        self.time_source = time_source or (lambda: datetime.utcnow())

    def step(self, inputs: EnergyInputs) -> Optional[HeartbeatProof]:
        """Advance the engine by one observation window."""

        self._harvest(inputs)
        if self.state.phase == DriftPhase.DORMANT:
            if self.store.supercap_voltage >= self.policy.boot_voltage:
                self.state.phase = DriftPhase.BOOT_INTEGRITY
            else:
                return None

        if self.state.phase == DriftPhase.BOOT_INTEGRITY:
            if not self._verify_integrity():
                self._enter_distress("Integrity hash mismatch detected.")
                return None
            if self.store.supercap_voltage < self.policy.boot_voltage:
                self.state.phase = DriftPhase.DORMANT
                return None
            self.state.phase = DriftPhase.HARVEST_OBSERVE

        if self.state.phase == DriftPhase.HARVEST_OBSERVE:
            self._observe_energy(inputs)
            if self._ready_for_work():
                self.state.phase = DriftPhase.WORK_BURST
            else:
                return None

        if self.state.phase == DriftPhase.WORK_BURST:
            proof = self._emit_proof(inputs)
            self.state.phase = DriftPhase.DORMANT
            return proof

        if self.state.phase == DriftPhase.DISTRESS:
            self._emit_distress_proof()
            self.state.phase = DriftPhase.DORMANT
            return None

        return None

    def export_ledgers(self) -> Dict[str, list[dict]]:
        return {key: list(entries) for key, entries in self.state.ledgers.items()}

    def _harvest(self, inputs: EnergyInputs) -> None:
        total = inputs.total()
        self.store.supercap_voltage = max(0.0, self.store.supercap_voltage + total * 0.01)
        self.store.microcell_charge = min(1.0, self.store.microcell_charge + total * 0.001)
        self.state.energy_income_rate = total

    def _verify_integrity(self) -> bool:
        return bool(self.state.last_proof_hash)

    def _observe_energy(self, inputs: EnergyInputs) -> None:
        self.state.duty_budget = max(
            0.0,
            self.store.supercap_voltage - self.policy.observation_cost,
        )
        self._record_event(
            "Harvest observe",
            {
                "inputs_mw": asdict(inputs),
                "income_rate": self.state.energy_income_rate,
                "duty_budget": self.state.duty_budget,
            },
        )

    def _ready_for_work(self) -> bool:
        now = self.time_source()
        next_due = (
            self.state.last_heartbeat + self.policy.heartbeat_interval
            if self.state.last_heartbeat
            else None
        )
        due = next_due is None or now >= next_due
        return due and self.state.duty_budget >= self.policy.work_cost

    def _emit_proof(self, inputs: EnergyInputs) -> HeartbeatProof:
        timestamp = self.time_source().isoformat() + "Z"
        energy_bucket = self._bucket_energy()
        payload = {
            "device_id": self.device_id,
            "timestamp": timestamp,
            "energy_bucket": energy_bucket,
            "phase": self.state.phase,
            "last_proof_hash": self.state.last_proof_hash,
        }
        signature = self.signer(self._hash_payload(payload))
        proof = HeartbeatProof(
            device_id=self.device_id,
            timestamp=timestamp,
            energy_bucket=energy_bucket,
            phase=self.state.phase,
            last_proof_hash=self.state.last_proof_hash,
            signature=signature,
            fields={
                "thermal_mw": inputs.thermal_mw,
                "solar_mw": inputs.solar_mw,
                "vibration_mw": inputs.vibration_mw,
                "rf_mw": inputs.rf_mw,
            },
        )
        proof_hash = self._hash_payload(proof.as_dict())
        self.state.last_proof_hash = proof_hash
        self.state.last_heartbeat = self.time_source()
        self._record_ledger("heartbeat_ledger", proof.as_dict())
        self.store.supercap_voltage = max(
            0.0, self.store.supercap_voltage - self.policy.work_cost
        )
        return proof

    def _emit_distress_proof(self) -> None:
        payload = {
            "timestamp": self.time_source().isoformat() + "Z",
            "phase": DriftPhase.DISTRESS,
            "brownout_count": self.state.brownout_count,
            "last_proof_hash": self.state.last_proof_hash,
        }
        payload["signature"] = self.signer(self._hash_payload(payload))
        self._record_ledger("distress_ledger", payload)

    def _enter_distress(self, reason: str) -> None:
        self.state.phase = DriftPhase.DISTRESS
        self.state.brownout_count += 1
        self._record_event("Distress mode engaged", {"reason": reason})
        if self.state.brownout_count >= self.policy.distress_brownouts:
            self._emit_distress_proof()

    def _bucket_energy(self) -> str:
        voltage = self.store.supercap_voltage
        if voltage < self.policy.boot_voltage:
            return "LOW"
        if voltage < self.policy.upload_surplus:
            return "NOMINAL"
        return "SURPLUS"

    def _record_event(self, message: str, details: Optional[Dict[str, object]] = None) -> None:
        entry = {
            "timestamp": self.time_source().isoformat() + "Z",
            "message": message,
            "details": details or {},
        }
        self._record_ledger("event_ledger", entry)

    def _record_ledger(self, ledger: str, entry: dict) -> None:
        ledger_entries = self.state.ledgers.setdefault(ledger, [])
        ledger_entries.append(entry)
        if len(ledger_entries) > self.ledger_capacity:
            del ledger_entries[0 : len(ledger_entries) - self.ledger_capacity]

    def _hash_payload(self, payload: Dict[str, object]) -> str:
        digest = hashlib.sha256(json_bytes(payload)).hexdigest()
        return digest

    def _default_signer(self, payload_hash: str) -> str:
        seed = f"{self.device_id}:{payload_hash}".encode("utf-8")
        return hashlib.sha256(seed).hexdigest()


def json_bytes(payload: Dict[str, object]) -> bytes:
    return str(payload).encode("utf-8")
