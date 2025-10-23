#include "echo/mosaic.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <sstream>

namespace echo {
namespace {

constexpr double kGoldenPulse = 0.61803398875;
constexpr double kPi = 3.14159265358979323846;

double normalize(double value, double fallback = 0.0) {
    if (!std::isfinite(value)) {
        return fallback;
    }
    if (value < 0.0) {
        return 0.0;
    }
    if (value > 1.0) {
        return 1.0;
    }
    return value;
}

double summarize_metric(const MetricSummary& summary) {
    if (summary.samples == 0) {
        return 0.0;
    }
    const double spread = summary.maximum - summary.minimum;
    const double amplitude = std::abs(summary.average) + spread * 0.25;
    const double resonance = amplitude == 0.0 ? 0.0 : std::tanh(amplitude / (summary.samples));
    return normalize(resonance);
}

double duration_weight(uint64_t start_ms, uint64_t end_ms, uint64_t total_duration) {
    if (end_ms <= start_ms || total_duration == 0) {
        return 0.0;
    }
    const double span = static_cast<double>(end_ms - start_ms);
    return normalize(span / static_cast<double>(total_duration));
}

double emphasis_for_epoch(std::size_t index, double weight, double continuity, double tempo) {
    const double orbit = std::sin((static_cast<double>(index) + 1.0) * kGoldenPulse * kPi);
    const double continuity_bias = std::pow(continuity, 0.5);
    const double tempo_bias = std::pow(tempo, 0.75);
    return normalize(0.35 + 0.4 * weight + 0.15 * orbit + 0.1 * continuity_bias + 0.1 * tempo_bias);
}

}  // namespace

TemporalMosaic::TemporalMosaic(std::vector<EpochManifest> sequence, LineageReport report)
    : sequence_(std::move(sequence)), report_(std::move(report)) {
    if (!sequence_.empty()) {
        std::stable_sort(sequence_.begin(), sequence_.end(),
                         [](const EpochManifest& a, const EpochManifest& b) {
                             if (a.start_ms == b.start_ms) {
                                 return a.epoch_id < b.epoch_id;
                             }
                             return a.start_ms < b.start_ms;
                         });
    }
}

std::vector<MosaicShard> TemporalMosaic::shards() const {
    std::vector<MosaicShard> shards;
    if (sequence_.empty()) {
        return shards;
    }

    const double continuity = normalize(report_.continuity_score, 1.0);
    const double tempo = normalize(report_.tempo_consistency, 1.0);

    uint64_t earliest = sequence_.front().start_ms;
    uint64_t latest = sequence_.back().end_ms;
    if (report_.earliest_start_ms) {
        earliest = std::min(earliest, *report_.earliest_start_ms);
    }
    if (report_.latest_end_ms) {
        latest = std::max(latest, *report_.latest_end_ms);
    }
    const uint64_t total_duration = latest > earliest ? (latest - earliest) : 0;

    for (std::size_t i = 0; i < sequence_.size(); ++i) {
        const auto& epoch = sequence_[i];
        const double weight = duration_weight(epoch.start_ms, epoch.end_ms, total_duration);
        MosaicShard shard;
        shard.key = "epoch:" + epoch.epoch_id;
        shard.weight = normalize(0.45 * weight + 0.3 * continuity + 0.25 * tempo);
        shard.emphasis = emphasis_for_epoch(i, weight, continuity, tempo);
        shards.push_back(shard);
    }

    for (const auto& [name, summary] : report_.metrics) {
        MosaicShard shard;
        shard.key = "metric:" + name;
        shard.weight = normalize(0.5 * summarize_metric(summary) + 0.5 * continuity);
        shard.emphasis = normalize(0.4 + 0.6 * summarize_metric(summary));
        shards.push_back(shard);
    }

    if (!report_.lineage_breaks.empty()) {
        MosaicShard shard;
        shard.key = "lineage:fracture";
        shard.weight = normalize(0.2 + 0.1 * report_.lineage_breaks.size());
        shard.emphasis = normalize(0.6 + 0.1 * report_.lineage_breaks.size());
        shards.push_back(shard);
    }

    if (!report_.temporal_anomalies.empty()) {
        MosaicShard shard;
        shard.key = "tempo:anomaly";
        shard.weight = normalize(0.25 + 0.05 * report_.temporal_anomalies.size());
        shard.emphasis = normalize(0.55 + 0.08 * report_.temporal_anomalies.size());
        shards.push_back(shard);
    }

    if (!report_.signature_failures.empty()) {
        MosaicShard shard;
        shard.key = "signature:dissonance";
        shard.weight = normalize(0.45);
        shard.emphasis = normalize(0.75);
        shards.push_back(shard);
    }

    std::stable_sort(shards.begin(), shards.end(), [](const MosaicShard& a, const MosaicShard& b) {
        if (std::abs(a.weight - b.weight) < 1e-6) {
            return a.key < b.key;
        }
        return a.weight > b.weight;
    });

    return shards;
}

std::string TemporalMosaic::render() const {
    if (sequence_.empty()) {
        return "<temporal-mosaic empty />";
    }

    std::ostringstream out;
    out << "<temporal-mosaic continuity='" << normalize(report_.continuity_score, 1.0)
        << "' tempo='" << normalize(report_.tempo_consistency, 1.0)
        << "' epochs='" << sequence_.size() << "'>\n";

    const auto shards_view = shards();
    for (const auto& shard : shards_view) {
        const std::size_t glyph_count = static_cast<std::size_t>(std::round(shard.weight * 12));
        const std::size_t accent_count = static_cast<std::size_t>(std::round(shard.emphasis * 8));
        out << "  <shard key='" << shard.key << "' weight='" << shard.weight
            << "' emphasis='" << shard.emphasis << "'>";
        out << std::string(glyph_count, '*');
        if (accent_count > 0) {
            out << std::string(accent_count, '+');
        }
        out << "</shard>\n";
    }

    out << "</temporal-mosaic>";
    return out.str();
}

}  // namespace echo

