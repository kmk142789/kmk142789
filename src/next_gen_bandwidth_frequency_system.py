"""Next-generation bandwidth frequency propagation system v2.

This module expands the propagation engine with advanced frequency bands,
adaptive modulation, interference mitigation, ML-inspired prediction, and
quantum-ready encryption hooks. The implementation aims to be both expressive
and safe to import, with optional demonstrations guarded by CLI entry points.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
from typing import Callable, Dict, Iterable, List, Optional, Tuple
import hashlib
import json
import time

import numpy as np


class FrequencyBand(Enum):
    """Extended frequency band support including 6G."""

    SUB_1GHZ = "sub_1ghz"
    WIFI_2_4GHZ = "2.4ghz"
    WIFI_5GHZ = "5ghz"
    WIFI_6GHZ = "6ghz"
    WIFI_6E = "6e"
    MMWAVE_24GHZ = "mmwave_24"
    MMWAVE_39GHZ = "mmwave_39"
    MMWAVE_60GHZ = "mmwave_60"
    TERAHERTZ = "terahertz"
    BLUETOOTH = "bluetooth"
    BLUETOOTH_LE = "ble"
    ZIGBEE = "zigbee"
    LORA = "lora"
    NB_IOT = "nb_iot"
    SATELLITE = "satellite"


class ModulationScheme(Enum):
    """Advanced modulation schemes."""

    BPSK = "bpsk"
    QPSK = "qpsk"
    QAM_16 = "16qam"
    QAM_64 = "64qam"
    QAM_256 = "256qam"
    QAM_1024 = "1024qam"
    QAM_4096 = "4096qam"
    OFDM = "ofdm"
    OFDMA = "ofdma"
    NOMA = "noma"
    OTFS = "otfs"


class EnvironmentType(Enum):
    """Detailed environment classifications."""

    DENSE_URBAN = "dense_urban"
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL = "rural"
    INDOOR_OFFICE = "indoor_office"
    INDOOR_HOME = "indoor_home"
    INDUSTRIAL = "industrial"
    OUTDOOR_OPEN = "outdoor_open"
    FOREST = "forest"
    MARITIME = "maritime"


@dataclass
class LinkQualityMetrics:
    """Comprehensive link quality assessment."""

    snr_db: float
    rssi_dbm: float
    packet_loss_rate: float
    latency_ms: float
    jitter_ms: float
    ber: float
    per: float
    throughput_mbps: float
    modulation: ModulationScheme
    sinr_db: float
    channel_quality: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, float | str]:
        """Serialize metrics for reporting."""

        return {
            "snr_db": self.snr_db,
            "rssi_dbm": self.rssi_dbm,
            "packet_loss_rate": self.packet_loss_rate,
            "latency_ms": self.latency_ms,
            "jitter_ms": self.jitter_ms,
            "ber": self.ber,
            "per": self.per,
            "throughput_mbps": self.throughput_mbps,
            "modulation": self.modulation.value,
            "sinr_db": self.sinr_db,
            "channel_quality": self.channel_quality,
            "timestamp": self.timestamp,
        }


@dataclass
class InterferenceSource:
    """Track interference sources."""

    source_id: str
    frequency_mhz: float
    power_dbm: float
    bandwidth_mhz: float
    location: Tuple[float, float, float]


@dataclass
class PropagationModel:
    """Physical propagation model parameters."""

    path_loss_exponent: float = 2.7
    shadowing_std_db: float = 8.0
    rayleigh_fading_enabled: bool = True
    doppler_shift_hz: float = 0.0
    multipath_delay_spread_ns: float = 50.0


@dataclass
class EncryptionHook:
    """Quantum-ready encryption hook for telemetry and control."""

    name: str
    signer: Callable[[bytes], str]

    def sign_payload(self, payload: bytes) -> str:
        """Return a signed payload fingerprint."""

        return self.signer(payload)


def default_quantum_ready_hook() -> EncryptionHook:
    """Provide a safe, deterministic hash-based hook."""

    def signer(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    return EncryptionHook(name="sha256-fallback", signer=signer)


class AdaptiveModulationController:
    """ML-inspired adaptive modulation and coding."""

    def __init__(self) -> None:
        self.snr_history = deque(maxlen=100)
        self.throughput_history = deque(maxlen=100)
        self.modulation_map = {
            ModulationScheme.BPSK: (0, 5),
            ModulationScheme.QPSK: (5, 10),
            ModulationScheme.QAM_16: (10, 15),
            ModulationScheme.QAM_64: (15, 20),
            ModulationScheme.QAM_256: (20, 25),
            ModulationScheme.QAM_1024: (25, 30),
            ModulationScheme.QAM_4096: (30, 40),
        }

    def select_modulation(
        self, current_snr_db: float, historical_snr: Optional[List[float]] = None
    ) -> ModulationScheme:
        """Select optimal modulation based on SNR and trend."""

        effective_snr = current_snr_db - 3.0
        if historical_snr and len(historical_snr) >= 3:
            trend = np.polyfit(range(len(historical_snr)), historical_snr, 1)[0]
            if trend < -0.5:
                effective_snr -= 2.0
            elif trend > 0.5:
                effective_snr += 1.0

        selected = ModulationScheme.BPSK
        for scheme, (min_snr, max_snr) in self.modulation_map.items():
            if min_snr <= effective_snr < max_snr:
                selected = scheme
        return selected

    def predict_throughput(
        self, modulation: ModulationScheme, bandwidth_mhz: float, coding_rate: float
    ) -> float:
        """Predict throughput for given parameters."""

        bits_per_symbol = {
            ModulationScheme.BPSK: 1,
            ModulationScheme.QPSK: 2,
            ModulationScheme.QAM_16: 4,
            ModulationScheme.QAM_64: 6,
            ModulationScheme.QAM_256: 8,
            ModulationScheme.QAM_1024: 10,
            ModulationScheme.QAM_4096: 12,
        }.get(modulation, 2)

        spectral_eff = bits_per_symbol * coding_rate
        return spectral_eff * bandwidth_mhz

    def infer_coding_rate(self, sinr_db: float) -> float:
        """Infer a conservative coding rate from SINR."""

        if sinr_db < 5:
            return 0.45
        if sinr_db < 10:
            return 0.6
        if sinr_db < 20:
            return 0.75
        if sinr_db < 30:
            return 0.85
        return 0.92


class InterferenceManager:
    """Advanced interference detection and mitigation."""

    def __init__(self) -> None:
        self.interference_sources: Dict[str, InterferenceSource] = {}
        self.frequency_occupancy: Dict[float, float] = {}

    def add_interference(self, source: InterferenceSource) -> None:
        """Register an interference source."""

        self.interference_sources[source.source_id] = source
        for freq in np.arange(
            source.frequency_mhz - source.bandwidth_mhz / 2,
            source.frequency_mhz + source.bandwidth_mhz / 2,
            1.0,
        ):
            self.frequency_occupancy[freq] = (
                self.frequency_occupancy.get(freq, 0) + source.power_dbm
            )

    def calculate_sinr(
        self,
        target_freq_mhz: float,
        target_power_dbm: float,
        bandwidth_mhz: float,
        noise_floor_dbm: float = -100.0,
    ) -> float:
        """Calculate Signal-to-Interference-plus-Noise Ratio."""

        interference_power = 0.0
        for freq, power in self.frequency_occupancy.items():
            if abs(freq - target_freq_mhz) < bandwidth_mhz / 2:
                interference_power += 10 ** (power / 10)

        interference_dbm = (
            10 * np.log10(interference_power) if interference_power > 0 else -200
        )

        noise_power = 10 ** (noise_floor_dbm / 10)
        total_interference = 10 ** (interference_dbm / 10) + noise_power
        total_interference_dbm = 10 * np.log10(total_interference)
        return target_power_dbm - total_interference_dbm

    def find_clean_channels(
        self, bandwidth_mhz: float, num_channels: int = 3
    ) -> List[float]:
        """Find least-interfered frequency channels."""

        start_freq = 2400.0
        end_freq = 6000.0
        step = 5.0
        channel_scores: Dict[float, float] = {}

        for center_freq in np.arange(start_freq, end_freq, step):
            interference = 0.0
            samples = 0
            for freq in np.arange(
                center_freq - bandwidth_mhz / 2,
                center_freq + bandwidth_mhz / 2,
                1.0,
            ):
                interference += self.frequency_occupancy.get(freq, -150)
                samples += 1

            avg_interference = interference / samples if samples > 0 else -150
            channel_scores[center_freq] = -avg_interference

        sorted_channels = sorted(channel_scores.items(), key=lambda x: x[1], reverse=True)
        return [freq for freq, _ in sorted_channels[:num_channels]]


class AdvancedPropagationEngine:
    """Next-gen propagation engine with ML prediction and 6G support."""

    def __init__(
        self,
        *,
        encryption_hook: EncryptionHook | None = None,
        rng_seed: int | None = None,
    ) -> None:
        self.modulation_controller = AdaptiveModulationController()
        self.interference_manager = InterferenceManager()
        self.link_history: Dict[Tuple[str, str], deque[float]] = {}
        self.frequency_bands = self._init_frequency_bands()
        self.environment_models = self._init_environment_models()
        self.encryption_hook = encryption_hook or default_quantum_ready_hook()
        self.rng = np.random.default_rng(rng_seed)

    def _init_frequency_bands(self) -> Dict[FrequencyBand, Dict[str, float]]:
        """Initialize extended frequency band characteristics."""

        return {
            FrequencyBand.SUB_1GHZ: {
                "center_freq_mhz": 868.0,
                "max_bandwidth_mhz": 20.0,
                "range_km": 10.0,
                "penetration_factor": 0.9,
                "power_efficiency": 0.95,
                "weather_sensitivity": 0.1,
            },
            FrequencyBand.WIFI_2_4GHZ: {
                "center_freq_mhz": 2437.0,
                "max_bandwidth_mhz": 80.0,
                "range_km": 0.1,
                "penetration_factor": 0.7,
                "power_efficiency": 0.7,
                "weather_sensitivity": 0.2,
            },
            FrequencyBand.WIFI_5GHZ: {
                "center_freq_mhz": 5180.0,
                "max_bandwidth_mhz": 160.0,
                "range_km": 0.05,
                "penetration_factor": 0.5,
                "power_efficiency": 0.6,
                "weather_sensitivity": 0.3,
            },
            FrequencyBand.WIFI_6GHZ: {
                "center_freq_mhz": 6495.0,
                "max_bandwidth_mhz": 320.0,
                "range_km": 0.03,
                "penetration_factor": 0.4,
                "power_efficiency": 0.5,
                "weather_sensitivity": 0.4,
            },
            FrequencyBand.MMWAVE_24GHZ: {
                "center_freq_mhz": 24000.0,
                "max_bandwidth_mhz": 2000.0,
                "range_km": 0.001,
                "penetration_factor": 0.1,
                "power_efficiency": 0.3,
                "weather_sensitivity": 0.8,
            },
            FrequencyBand.MMWAVE_39GHZ: {
                "center_freq_mhz": 39000.0,
                "max_bandwidth_mhz": 2000.0,
                "range_km": 0.0005,
                "penetration_factor": 0.05,
                "power_efficiency": 0.25,
                "weather_sensitivity": 0.9,
            },
            FrequencyBand.TERAHERTZ: {
                "center_freq_mhz": 300000.0,
                "max_bandwidth_mhz": 50000.0,
                "range_km": 0.0001,
                "penetration_factor": 0.01,
                "power_efficiency": 0.15,
                "weather_sensitivity": 0.95,
            },
            FrequencyBand.LORA: {
                "center_freq_mhz": 915.0,
                "max_bandwidth_mhz": 0.5,
                "range_km": 15.0,
                "penetration_factor": 0.85,
                "power_efficiency": 0.98,
                "weather_sensitivity": 0.1,
            },
            FrequencyBand.SATELLITE: {
                "center_freq_mhz": 12000.0,
                "max_bandwidth_mhz": 500.0,
                "range_km": 1000.0,
                "penetration_factor": 0.0,
                "power_efficiency": 0.4,
                "weather_sensitivity": 0.7,
            },
        }

    def _init_environment_models(self) -> Dict[EnvironmentType, PropagationModel]:
        """Initialize environment-specific propagation models."""

        return {
            EnvironmentType.DENSE_URBAN: PropagationModel(
                path_loss_exponent=4.0,
                shadowing_std_db=10.0,
                multipath_delay_spread_ns=200.0,
            ),
            EnvironmentType.URBAN: PropagationModel(
                path_loss_exponent=3.5,
                shadowing_std_db=8.0,
                multipath_delay_spread_ns=100.0,
            ),
            EnvironmentType.SUBURBAN: PropagationModel(
                path_loss_exponent=3.0,
                shadowing_std_db=6.0,
                multipath_delay_spread_ns=50.0,
            ),
            EnvironmentType.RURAL: PropagationModel(
                path_loss_exponent=2.5,
                shadowing_std_db=4.0,
                multipath_delay_spread_ns=20.0,
            ),
            EnvironmentType.INDOOR_OFFICE: PropagationModel(
                path_loss_exponent=3.2,
                shadowing_std_db=7.0,
                multipath_delay_spread_ns=80.0,
            ),
            EnvironmentType.OUTDOOR_OPEN: PropagationModel(
                path_loss_exponent=2.0,
                shadowing_std_db=3.0,
                multipath_delay_spread_ns=10.0,
            ),
        }

    def calculate_path_loss(
        self, distance_km: float, freq_mhz: float, environment: EnvironmentType
    ) -> float:
        """Calculate path loss using environment-specific model."""

        model = self.environment_models.get(environment, PropagationModel())
        distance_km = max(distance_km, 0.001)

        fspl_db = 20 * np.log10(distance_km * 1000) + 20 * np.log10(freq_mhz) - 27.55
        distance_factor = 10 * model.path_loss_exponent * np.log10(distance_km)
        shadowing = self.rng.normal(0, model.shadowing_std_db)

        total_loss = fspl_db + distance_factor + shadowing
        if model.rayleigh_fading_enabled:
            total_loss += self.rng.rayleigh(scale=2.0)
        return total_loss

    def calculate_received_power(
        self, tx_power_dbm: float, path_loss_db: float, antenna_gain_dbi: float = 0.0
    ) -> float:
        """Calculate received signal power."""

        return tx_power_dbm - path_loss_db + antenna_gain_dbi

    def estimate_link_quality(
        self,
        source_id: str,
        dest_id: str,
        *,
        distance_km: float,
        freq_mhz: float,
        tx_power_dbm: float,
        bandwidth_mhz: float,
        environment: EnvironmentType,
    ) -> LinkQualityMetrics:
        """Comprehensive link quality estimation."""

        path_loss = self.calculate_path_loss(distance_km, freq_mhz, environment)
        rx_power = self.calculate_received_power(tx_power_dbm, path_loss)
        sinr = self.interference_manager.calculate_sinr(freq_mhz, rx_power, bandwidth_mhz)

        link_key = (source_id, dest_id)
        if link_key not in self.link_history:
            self.link_history[link_key] = deque(maxlen=50)

        snr_history = list(self.link_history[link_key])
        modulation = self.modulation_controller.select_modulation(sinr, snr_history)
        self.link_history[link_key].append(sinr)

        coding_rate = self.modulation_controller.infer_coding_rate(sinr)
        throughput = self.modulation_controller.predict_throughput(
            modulation, bandwidth_mhz, coding_rate
        )

        ber = self._calculate_ber(sinr, modulation)
        per = 1 - (1 - ber) ** 1000

        propagation_delay_ms = (distance_km / 300000) * 1000
        processing_delay_ms = 5.0
        latency = propagation_delay_ms + processing_delay_ms
        jitter = self.rng.exponential(2.0)
        packet_loss = per
        channel_quality = max(0.0, min(1.0, (sinr + 10) / 40))

        return LinkQualityMetrics(
            snr_db=sinr,
            rssi_dbm=rx_power,
            packet_loss_rate=packet_loss,
            latency_ms=latency,
            jitter_ms=jitter,
            ber=ber,
            per=per,
            throughput_mbps=throughput * (1 - packet_loss),
            modulation=modulation,
            sinr_db=sinr,
            channel_quality=channel_quality,
        )

    def _calculate_ber(self, snr_db: float, modulation: ModulationScheme) -> float:
        """Calculate bit error rate for given SNR and modulation."""

        snr_linear = 10 ** (snr_db / 10)
        if modulation == ModulationScheme.BPSK:
            ber = 0.5 * np.exp(-snr_linear)
        elif modulation == ModulationScheme.QPSK:
            ber = 0.5 * np.exp(-snr_linear / 2)
        elif modulation == ModulationScheme.QAM_16:
            ber = (3 / 8) * np.exp(-snr_linear / 5)
        elif modulation == ModulationScheme.QAM_64:
            ber = (7 / 24) * np.exp(-snr_linear / 14)
        elif modulation == ModulationScheme.QAM_256:
            ber = (15 / 64) * np.exp(-snr_linear / 42)
        else:
            ber = 0.1 * np.exp(-snr_linear / 50)
        return max(1e-10, min(0.5, ber))

    def predict_link_availability(
        self, source_id: str, dest_id: str, time_horizon_hours: float = 24.0
    ) -> Dict[str, float | str]:
        """Predict future link availability using a trend model."""

        link_key = (source_id, dest_id)
        if link_key not in self.link_history or len(self.link_history[link_key]) < 10:
            return {"prediction": "insufficient_data", "confidence": 0.0}

        history = list(self.link_history[link_key])
        recent_avg = np.mean(history[-10:])
        overall_avg = np.mean(history)
        trend = recent_avg - overall_avg
        future_snr = recent_avg + (trend * time_horizon_hours / 24)

        if future_snr > 10:
            status = "available"
            confidence = min(0.95, 0.5 + (future_snr - 10) / 40)
        else:
            status = "degraded"
            confidence = min(0.95, 0.5 + (10 - future_snr) / 40)

        return {
            "prediction": status,
            "confidence": confidence,
            "predicted_snr_db": future_snr,
            "current_snr_db": history[-1],
            "trend": "improving" if trend > 0 else "degrading",
        }

    def optimize_multi_band_selection(
        self,
        *,
        distance_km: float,
        required_throughput_mbps: float,
        environment: EnvironmentType,
        available_bands: Iterable[FrequencyBand],
    ) -> List[FrequencyBand]:
        """Select optimal combination of bands for requirements."""

        band_scores: List[Tuple[FrequencyBand, float]] = []
        for band in available_bands:
            band_info = self.frequency_bands[band]
            if band_info["range_km"] < distance_km:
                continue

            max_throughput = band_info["max_bandwidth_mhz"]
            if max_throughput < required_throughput_mbps * 0.5:
                continue

            range_score = min(1.0, band_info["range_km"] / distance_km)
            throughput_score = min(1.0, max_throughput / required_throughput_mbps)
            penetration_score = band_info["penetration_factor"]
            efficiency_score = band_info["power_efficiency"]
            weather_score = 1.0 - band_info["weather_sensitivity"]

            total_score = (
                range_score * 0.25
                + throughput_score * 0.30
                + penetration_score * 0.20
                + efficiency_score * 0.15
                + weather_score * 0.10
            )
            diversity_bonus = 0.05 if band in (FrequencyBand.WIFI_6GHZ, FrequencyBand.TERAHERTZ) else 0.0
            band_scores.append((band, total_score + diversity_bonus))

        band_scores.sort(key=lambda x: x[1], reverse=True)
        return [band for band, _ in band_scores[:3]]

    def generate_comprehensive_report(
        self, source_id: str, dest_id: str
    ) -> Dict[str, object]:
        """Generate detailed propagation analysis report."""

        link_key = (source_id, dest_id)
        history = list(self.link_history.get(link_key, []))

        report = {
            "link": f"{source_id} -> {dest_id}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "historical_data": {
                "samples": len(history),
                "avg_snr_db": float(np.mean(history)) if history else 0.0,
                "snr_std_db": float(np.std(history)) if history else 0.0,
            },
            "prediction_24h": self.predict_link_availability(source_id, dest_id, 24.0),
            "interference_sources": len(self.interference_manager.interference_sources),
            "recommended_channels": self.interference_manager.find_clean_channels(
                20.0, 3
            ),
            "band_catalog": {
                band.value: dict(metrics) for band, metrics in self.frequency_bands.items()
            },
        }

        payload = json.dumps(report, sort_keys=True).encode("utf-8")
        report["signature"] = self.encryption_hook.sign_payload(payload)
        report["signature_hook"] = self.encryption_hook.name
        return report


def demo() -> str:
    """Run a deterministic demonstration for the propagation system."""

    engine = AdvancedPropagationEngine(rng_seed=7)

    metrics = engine.estimate_link_quality(
        source_id="node_a",
        dest_id="node_b",
        distance_km=0.05,
        freq_mhz=5180.0,
        tx_power_dbm=20.0,
        bandwidth_mhz=80.0,
        environment=EnvironmentType.INDOOR_OFFICE,
    )

    engine.link_history[("node_a", "node_b")] = deque(
        [20 + engine.rng.normal(0, 2) for _ in range(20)], maxlen=50
    )

    prediction = engine.predict_link_availability("node_a", "node_b", 24.0)
    optimal_bands = engine.optimize_multi_band_selection(
        distance_km=0.1,
        required_throughput_mbps=500,
        environment=EnvironmentType.URBAN,
        available_bands=[
            FrequencyBand.WIFI_5GHZ,
            FrequencyBand.WIFI_6GHZ,
            FrequencyBand.MMWAVE_24GHZ,
        ],
    )

    report = engine.generate_comprehensive_report("node_a", "node_b")
    response = {
        "metrics": metrics.to_dict(),
        "prediction": prediction,
        "optimal_bands": [band.value for band in optimal_bands],
        "report": report,
    }
    return json.dumps(response, indent=2)


def main() -> None:  # pragma: no cover - CLI helper
    print("🚀 Next-Gen Bandwidth Frequency System v2")
    print("=" * 70)
    print(demo())


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
