"""Advanced bandwidth frequency propagation utilities."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple


class FrequencyBand(Enum):
    """Supported frequency bands for propagation."""

    SUB_1GHZ = "sub_1ghz"
    WIFI_2_4GHZ = "2.4ghz"
    WIFI_5GHZ = "5ghz"
    WIFI_6GHZ = "6ghz"
    MMWAVE = "mmwave"
    BLUETOOTH = "bluetooth"
    ZIGBEE = "zigbee"
    LORA = "lora"


@dataclass(frozen=True)
class BandProfile:
    """Physical characteristics for a frequency band."""

    range_km: float
    penetration: float
    bandwidth_max_mhz: float
    power_efficiency: float
    noise_floor_dbm: float
    path_loss_exponent: float


@dataclass(frozen=True)
class EnvironmentProfile:
    """Environment-dependent attenuation and latency values."""

    name: str
    penetration_factor: float
    clutter_loss_db: float
    fading_margin_db: float
    hop_latency_ms: float


@dataclass
class ChannelConfig:
    """Configuration for a communication channel."""

    band: FrequencyBand
    center_freq_mhz: float
    bandwidth_mhz: float
    tx_power_dbm: float
    modulation: str
    coding_rate: float

    def spectral_efficiency(self, snr_db: float) -> float:
        """Estimate bits per second per Hz based on the link SNR."""

        if snr_db <= -5:
            return 0.0
        snr_linear = 10 ** (snr_db / 10)
        shannon = math.log2(1 + snr_linear) * self.coding_rate
        modulation_caps = {
            "BPSK": 1.0,
            "QPSK": 2.0,
            "16QAM": 4.0,
            "64QAM": 6.0,
            "256QAM": 8.0,
            "OFDM": 6.0,
        }
        cap = modulation_caps.get(self.modulation.upper(), 6.0)
        return max(0.0, min(shannon, cap))

    def max_throughput_mbps(self, snr_db: float) -> float:
        """Calculate theoretical maximum throughput in Mbps."""

        return self.spectral_efficiency(snr_db) * self.bandwidth_mhz


@dataclass
class PropagationMetrics:
    """Real-time propagation health metrics."""

    packet_loss_rate: float = 0.0
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    signal_strength_dbm: float = -50.0
    throughput_mbps: float = 0.0
    active_channels: int = 0
    hop_count: int = 0
    spectral_efficiency: float = 0.0
    link_quality: float = 0.0


@dataclass
class NetworkNode:
    """Node in the mesh network."""

    id: str
    position: Tuple[float, float, float]
    supported_bands: List[FrequencyBand]
    is_gateway: bool = False
    power_level: float = 1.0
    routing_table: Dict[str, List[str]] = field(default_factory=dict)


class BandwidthFrequencyManager:
    """Advanced frequency management with multi-band propagation awareness."""

    def __init__(self, environment: str = "urban") -> None:
        self.channels: Dict[str, ChannelConfig] = {}
        self.active_bands: List[FrequencyBand] = []
        self.metrics = PropagationMetrics()
        self.nodes: Dict[str, NetworkNode] = {}
        self.frequency_map = self._initialize_frequency_map()
        self.environment_profiles = self._initialize_environment_profiles()
        self.environment = environment
        self.bandwidth_multiplier = 1.0

    def _initialize_frequency_map(self) -> Dict[FrequencyBand, BandProfile]:
        return {
            FrequencyBand.SUB_1GHZ: BandProfile(10.0, 0.9, 20.0, 0.95, -114.0, 2.2),
            FrequencyBand.WIFI_2_4GHZ: BandProfile(0.1, 0.7, 80.0, 0.7, -101.0, 2.6),
            FrequencyBand.WIFI_5GHZ: BandProfile(0.05, 0.5, 160.0, 0.6, -100.0, 2.8),
            FrequencyBand.WIFI_6GHZ: BandProfile(0.03, 0.4, 320.0, 0.5, -99.0, 2.9),
            FrequencyBand.MMWAVE: BandProfile(0.001, 0.1, 2000.0, 0.3, -90.0, 3.2),
            FrequencyBand.BLUETOOTH: BandProfile(0.01, 0.6, 2.0, 0.95, -100.0, 2.4),
            FrequencyBand.ZIGBEE: BandProfile(0.02, 0.75, 2.0, 0.9, -104.0, 2.3),
            FrequencyBand.LORA: BandProfile(15.0, 0.85, 0.5, 0.98, -124.0, 2.1),
        }

    def _initialize_environment_profiles(self) -> Dict[str, EnvironmentProfile]:
        return {
            "urban": EnvironmentProfile("urban", 0.5, 18.0, 8.0, 5.0),
            "suburban": EnvironmentProfile("suburban", 0.7, 12.0, 6.0, 4.0),
            "rural": EnvironmentProfile("rural", 0.9, 6.0, 4.0, 3.0),
            "indoor": EnvironmentProfile("indoor", 0.3, 22.0, 10.0, 6.0),
        }

    def set_environment(self, environment: str) -> None:
        if environment not in self.environment_profiles:
            raise ValueError(f"Unknown environment profile: {environment}")
        self.environment = environment

    def add_channel(
        self,
        channel_id: str,
        band: FrequencyBand,
        bandwidth_mhz: float,
        tx_power_dbm: float = 20.0,
        modulation: str = "OFDM",
        coding_rate: float = 0.75,
    ) -> ChannelConfig:
        """Add a new communication channel."""

        band_info = self.frequency_map[band]
        bandwidth_mhz = min(bandwidth_mhz, band_info.bandwidth_max_mhz)

        channel = ChannelConfig(
            band=band,
            center_freq_mhz=self._get_center_frequency(band),
            bandwidth_mhz=bandwidth_mhz,
            tx_power_dbm=tx_power_dbm,
            modulation=modulation,
            coding_rate=coding_rate,
        )

        self.channels[channel_id] = channel
        if band not in self.active_bands:
            self.active_bands.append(band)

        self._update_metrics()

        return channel

    def _get_center_frequency(self, band: FrequencyBand) -> float:
        freq_map = {
            FrequencyBand.SUB_1GHZ: 868.0,
            FrequencyBand.WIFI_2_4GHZ: 2437.0,
            FrequencyBand.WIFI_5GHZ: 5180.0,
            FrequencyBand.WIFI_6GHZ: 6495.0,
            FrequencyBand.MMWAVE: 28000.0,
            FrequencyBand.BLUETOOTH: 2442.0,
            FrequencyBand.ZIGBEE: 2405.0,
            FrequencyBand.LORA: 915.0,
        }
        return freq_map[band]

    def enable_channel_bonding(self, channel_ids: List[str]) -> float:
        """Bond multiple channels for increased bandwidth."""

        valid_channels = [self.channels[cid] for cid in channel_ids if cid in self.channels]
        if len(valid_channels) < 2:
            return 0.0

        total_bandwidth = sum(channel.bandwidth_mhz for channel in valid_channels)
        effective_bandwidth = total_bandwidth * 0.9
        anchor_bandwidth = valid_channels[0].bandwidth_mhz or 1.0
        self.bandwidth_multiplier = effective_bandwidth / anchor_bandwidth
        self._update_metrics()
        return effective_bandwidth

    def select_optimal_band(
        self,
        distance_km: float,
        required_bandwidth_mbps: float,
        environment: Optional[str] = None,
    ) -> FrequencyBand:
        """Select the best frequency band for the given conditions."""

        env = self.environment_profiles.get(environment or self.environment)
        if env is None:
            env = self.environment_profiles["suburban"]

        best_band = FrequencyBand.WIFI_2_4GHZ
        best_score = -1.0

        for band, info in self.frequency_map.items():
            if info.range_km < distance_km:
                continue

            snr = self._estimate_snr_db(
                tx_power_dbm=20.0,
                distance_km=distance_km,
                frequency_mhz=self._get_center_frequency(band),
                band_profile=info,
                env_profile=env,
            )
            max_throughput = info.bandwidth_max_mhz * max(0.1, math.log2(1 + 10 ** (snr / 10)))
            if max_throughput < required_bandwidth_mbps:
                continue

            score = (
                info.penetration * env.penetration_factor * 0.3
                + min(1.0, max_throughput / required_bandwidth_mbps) * 0.4
                + info.power_efficiency * 0.3
            )

            if score > best_score:
                best_score = score
                best_band = band

        return best_band

    def calculate_hop_index(self, source_node: str, dest_node: str) -> Tuple[int, List[str]]:
        """Calculate optimal hop path and hop count."""

        if source_node not in self.nodes or dest_node not in self.nodes:
            return (0, [])

        visited = set()
        distances = {node_id: float("inf") for node_id in self.nodes}
        distances[source_node] = 0.0
        previous: Dict[str, str] = {}

        while len(visited) < len(self.nodes):
            current = None
            min_dist = float("inf")
            for node_id in self.nodes:
                if node_id not in visited and distances[node_id] < min_dist:
                    min_dist = distances[node_id]
                    current = node_id

            if current is None or current == dest_node:
                break

            visited.add(current)

            for neighbor_id in self._get_neighbors(current):
                if neighbor_id in visited:
                    continue

                distance = self._calculate_link_cost(current, neighbor_id)
                new_dist = distances[current] + distance

                if new_dist < distances[neighbor_id]:
                    distances[neighbor_id] = new_dist
                    previous[neighbor_id] = current

        path = []
        current = dest_node
        while current in previous:
            path.insert(0, current)
            current = previous[current]
        if path or source_node == dest_node:
            path.insert(0, source_node)

        return (max(0, len(path) - 1), path)

    def _get_neighbors(self, node_id: str) -> List[str]:
        if node_id not in self.nodes:
            return []

        node = self.nodes[node_id]
        neighbors = []

        for other_id, other_node in self.nodes.items():
            if other_id == node_id:
                continue

            distance = self._calculate_distance(node.position, other_node.position)

            for band in node.supported_bands:
                if band in other_node.supported_bands:
                    if self.frequency_map[band].range_km >= distance:
                        neighbors.append(other_id)
                        break

        return neighbors

    def _calculate_distance(
        self, pos1: Tuple[float, float, float], pos2: Tuple[float, float, float]
    ) -> float:
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))

    def _calculate_path_loss(
        self,
        distance_km: float,
        frequency_mhz: float,
        band_profile: BandProfile,
    ) -> float:
        distance_km = max(distance_km, 0.001)
        fspl = 32.44 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz)
        extra_loss = (band_profile.path_loss_exponent - 2.0) * 10 * math.log10(distance_km / 0.001)
        return fspl + max(0.0, extra_loss)

    def _estimate_snr_db(
        self,
        tx_power_dbm: float,
        distance_km: float,
        frequency_mhz: float,
        band_profile: BandProfile,
        env_profile: EnvironmentProfile,
    ) -> float:
        path_loss = self._calculate_path_loss(distance_km, frequency_mhz, band_profile)
        total_loss = path_loss + env_profile.clutter_loss_db + env_profile.fading_margin_db
        rx_power = tx_power_dbm - total_loss
        return rx_power - band_profile.noise_floor_dbm

    def _candidate_channels(self, band: FrequencyBand) -> List[ChannelConfig]:
        return [channel for channel in self.channels.values() if channel.band == band]

    def _estimate_link_metrics(
        self,
        band: FrequencyBand,
        distance_km: float,
        env_profile: EnvironmentProfile,
        power_scale: float,
    ) -> Tuple[float, float]:
        band_profile = self.frequency_map[band]
        candidates = self._candidate_channels(band)
        if not candidates:
            candidates = [
                ChannelConfig(
                    band=band,
                    center_freq_mhz=self._get_center_frequency(band),
                    bandwidth_mhz=band_profile.bandwidth_max_mhz,
                    tx_power_dbm=18.0,
                    modulation="OFDM",
                    coding_rate=0.7,
                )
            ]

        best_throughput = 0.0
        best_snr = -99.0
        for channel in candidates:
            snr = self._estimate_snr_db(
                tx_power_dbm=channel.tx_power_dbm * power_scale,
                distance_km=distance_km,
                frequency_mhz=channel.center_freq_mhz,
                band_profile=band_profile,
                env_profile=env_profile,
            )
            throughput = channel.max_throughput_mbps(snr)
            if throughput > best_throughput:
                best_throughput = throughput
                best_snr = snr

        return best_snr, best_throughput

    def _calculate_link_cost(self, node1_id: str, node2_id: str) -> float:
        node1 = self.nodes[node1_id]
        node2 = self.nodes[node2_id]

        distance = self._calculate_distance(node1.position, node2.position)
        env_profile = self.environment_profiles[self.environment]
        power_scale = (node1.power_level + node2.power_level) / 2

        best_quality = 0.0
        for band in node1.supported_bands:
            if band in node2.supported_bands:
                snr, throughput = self._estimate_link_metrics(
                    band, distance, env_profile, power_scale
                )
                quality = self._score_link_quality(band, snr, throughput, distance)
                best_quality = max(best_quality, quality)

        propagation_delay = distance * 0.0035
        hop_latency = env_profile.hop_latency_ms + propagation_delay
        power_penalty = (2 - node1.power_level - node2.power_level) * 5
        quality_penalty = (1.0 - best_quality) * 20

        return hop_latency + power_penalty + quality_penalty

    def _score_link_quality(
        self, band: FrequencyBand, snr_db: float, throughput: float, distance_km: float
    ) -> float:
        band_profile = self.frequency_map[band]
        snr_score = min(1.0, max(0.0, (snr_db + 5) / 30))
        throughput_score = min(1.0, throughput / max(1.0, band_profile.bandwidth_max_mhz))
        range_score = min(1.0, max(0.0, (band_profile.range_km - distance_km) / band_profile.range_km))
        return 0.4 * snr_score + 0.35 * throughput_score + 0.25 * range_score

    def add_node(
        self,
        node_id: str,
        position: Tuple[float, float, float],
        bands: List[FrequencyBand],
        is_gateway: bool = False,
        power_level: float = 1.0,
    ) -> NetworkNode:
        node = NetworkNode(
            id=node_id,
            position=position,
            supported_bands=bands,
            is_gateway=is_gateway,
            power_level=power_level,
        )
        self.nodes[node_id] = node
        return node

    def simulate_propagation(self, source: str, destination: str, data_size_mb: float) -> Dict[str, object]:
        hop_count, path = self.calculate_hop_index(source, destination)

        if not path:
            return {"success": False, "reason": "No path found"}

        env_profile = self.environment_profiles[self.environment]
        total_latency = 0.0
        link_throughputs: List[float] = []
        link_qualities: List[float] = []
        link_snrs: List[float] = []

        for i in range(len(path) - 1):
            node_a = self.nodes[path[i]]
            node_b = self.nodes[path[i + 1]]
            distance = self._calculate_distance(node_a.position, node_b.position)
            power_scale = (node_a.power_level + node_b.power_level) / 2

            best_band = None
            best_throughput = 0.0
            best_snr = -99.0
            best_quality = 0.0

            for band in node_a.supported_bands:
                if band not in node_b.supported_bands:
                    continue
                snr, throughput = self._estimate_link_metrics(band, distance, env_profile, power_scale)
                quality = self._score_link_quality(band, snr, throughput, distance)
                if throughput > best_throughput:
                    best_band = band
                    best_throughput = throughput
                    best_snr = snr
                    best_quality = quality

            if best_band is None:
                return {"success": False, "reason": "No viable band for hop"}

            link_throughputs.append(best_throughput)
            link_qualities.append(best_quality)
            link_snrs.append(best_snr)
            total_latency += env_profile.hop_latency_ms + distance * 0.0035

        bottleneck_throughput = max(0.1, min(link_throughputs))
        transfer_time_ms = (data_size_mb / bottleneck_throughput) * 1000
        avg_quality = sum(link_qualities) / len(link_qualities)

        self.metrics.hop_count = hop_count
        self.metrics.latency_ms = total_latency
        self.metrics.throughput_mbps = bottleneck_throughput
        self.metrics.link_quality = avg_quality
        if link_snrs:
            self.metrics.signal_strength_dbm = sum(link_snrs) / len(link_snrs)
        self.metrics.packet_loss_rate = max(0.0, 0.1 - avg_quality * 0.08)

        return {
            "success": True,
            "path": path,
            "hop_count": hop_count,
            "latency_ms": total_latency,
            "transfer_time_ms": transfer_time_ms,
            "throughput_mbps": bottleneck_throughput,
            "link_quality": avg_quality,
        }

    def _update_metrics(self) -> None:
        if not self.channels:
            return

        env_profile = self.environment_profiles[self.environment]
        total_throughput = 0.0
        total_efficiency = 0.0
        for channel in self.channels.values():
            snr = self._estimate_snr_db(
                tx_power_dbm=channel.tx_power_dbm,
                distance_km=min(self.frequency_map[channel.band].range_km, 0.05),
                frequency_mhz=channel.center_freq_mhz,
                band_profile=self.frequency_map[channel.band],
                env_profile=env_profile,
            )
            total_throughput += channel.max_throughput_mbps(snr)
            total_efficiency += channel.spectral_efficiency(snr)

        self.metrics.active_channels = len(self.channels)
        self.metrics.throughput_mbps = total_throughput * self.bandwidth_multiplier
        self.metrics.spectral_efficiency = total_efficiency / len(self.channels)

    def generate_health_snapshot(self) -> Dict[str, object]:
        return {
            "timestamp": datetime.now().isoformat(),
            "active_bands": [band.value for band in self.active_bands],
            "total_channels": len(self.channels),
            "total_nodes": len(self.nodes),
            "environment": self.environment,
            "bandwidth_multiplier": self.bandwidth_multiplier,
            "metrics": {
                "packet_loss": self.metrics.packet_loss_rate,
                "latency_ms": self.metrics.latency_ms,
                "throughput_mbps": self.metrics.throughput_mbps,
                "spectral_efficiency": self.metrics.spectral_efficiency,
                "active_channels": self.metrics.active_channels,
                "link_quality": self.metrics.link_quality,
            },
            "channel_details": {
                cid: {
                    "band": channel.band.value,
                    "freq_mhz": channel.center_freq_mhz,
                    "bandwidth_mhz": channel.bandwidth_mhz,
                }
                for cid, channel in self.channels.items()
            },
        }
