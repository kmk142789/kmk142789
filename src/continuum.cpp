#include "echo/continuum.hpp"

#include <algorithm>
#include <cstddef>
#include <iomanip>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

#include <nlohmann/json.hpp>

#include "echo/util.hpp"

namespace echo {
namespace {

using json = nlohmann::json;

std::string iso8601(uint64_t ms) {
    std::ostringstream out;
    out << "ms" << ms;
    return out.str();
}

std::vector<uint8_t> hex_to_bytes(const std::string& hex) {
    if (hex.size() % 2 != 0) {
        throw std::invalid_argument("hex string must have even length");
    }
    std::vector<uint8_t> bytes;
    bytes.reserve(hex.size() / 2);
    for (std::size_t i = 0; i < hex.size(); i += 2) {
        auto byte = std::stoul(hex.substr(i, 2), nullptr, 16);
        bytes.push_back(static_cast<uint8_t>(byte));
    }
    return bytes;
}

std::string bytes_to_hex(const std::vector<uint8_t>& bytes) {
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (auto b : bytes) {
        out << std::setw(2) << static_cast<int>(b);
    }
    return out.str();
}

}  // namespace

Continuum::Continuum(MemoryStore& store, IdentityManager& id)
    : store_(store), id_(id) {}

std::string Continuum::make_epoch_id(uint64_t start_ms) {
    return "epoch-" + iso8601(start_ms);
}

std::string Continuum::metrics_to_json(const std::map<std::string, double>& metrics) {
    json manifest_metrics = json::object();
    for (const auto& [key, value] : metrics) {
        manifest_metrics[key] = value;
    }
    return manifest_metrics.dump();
}

std::vector<uint8_t> Continuum::canonicalize(const EpochManifest& manifest) {
    json j = {
        {"epoch_id", manifest.epoch_id},
        {"parent_id", manifest.parent_id},
        {"head_hash", manifest.head_hash},
        {"manifesto_cid", manifest.manifesto_cid},
        {"metrics", manifest.metrics},
        {"start_ms", manifest.start_ms},
        {"end_ms", manifest.end_ms},
        {"did", manifest.did},
    };
    auto dumped = j.dump();
    return std::vector<uint8_t>(dumped.begin(), dumped.end());
}

std::string Continuum::manifest_to_json(const EpochManifest& manifest) {
    json j = {
        {"epoch_id", manifest.epoch_id},
        {"parent_id", manifest.parent_id},
        {"head_hash", manifest.head_hash},
        {"manifesto_cid", manifest.manifesto_cid},
        {"metrics", manifest.metrics},
        {"start_ms", manifest.start_ms},
        {"end_ms", manifest.end_ms},
        {"did", manifest.did},
        {"sig_hex", bytes_to_hex(manifest.sig)},
    };
    return j.dump();
}

EpochManifest Continuum::parse_manifest_json(const std::string& json_blob) {
    json parsed = json::parse(json_blob);
    EpochManifest manifest;
    manifest.epoch_id = parsed.value("epoch_id", std::string{});
    manifest.parent_id = parsed.value("parent_id", std::string{});
    manifest.head_hash = parsed.value("head_hash", std::string{});
    manifest.manifesto_cid = parsed.value("manifesto_cid", std::string{});
    manifest.metrics = parsed.value("metrics", std::map<std::string, double>{});
    manifest.start_ms = parsed.value("start_ms", uint64_t{0});
    manifest.end_ms = parsed.value("end_ms", uint64_t{0});
    manifest.did = parsed.value("did", std::string{});

    const auto sig_hex = parsed.value("sig_hex", std::string{});
    if (!sig_hex.empty()) {
        manifest.sig = hex_to_bytes(sig_hex);
    }

    return manifest;
}

std::string Continuum::begin_epoch(const std::string& manifesto_json) {
    if (current_epoch_.has_value()) {
        end_epoch({});
    }

    current_start_ = now_ms();
    auto epoch_id = make_epoch_id(current_start_);
    current_epoch_ = epoch_id;

    std::string cid;
    if (!manifesto_json.empty()) {
        std::vector<uint8_t> manifesto_bytes(manifesto_json.begin(), manifesto_json.end());
        cid = store_.put_blob(manifesto_bytes);
    }

    json begin_event = {
        {"epoch_id", epoch_id},
        {"manifesto_cid", cid},
        {"start_ms", current_start_},
    };
    const auto serialized = begin_event.dump();
    store_.remember_event(id_.doc().did, "epoch_begin", epoch_id,
                          std::vector<uint8_t>(serialized.begin(), serialized.end()));

    return epoch_id;
}

EpochManifest Continuum::end_epoch(const std::map<std::string, double>& metrics) {
    if (!current_epoch_) {
        return {};
    }

    const auto end = now_ms();
    EpochManifest manifest;
    manifest.epoch_id = *current_epoch_;
    const auto recent_history = history(1);
    manifest.parent_id = recent_history.empty() ? std::string{} : recent_history.front().epoch_id;
    manifest.head_hash = store_.head_hash();
    manifest.manifesto_cid.clear();
    manifest.metrics = metrics;
    manifest.start_ms = current_start_;
    manifest.end_ms = end;
    manifest.did = id_.doc().did;

    auto message = canonicalize(manifest);
    auto signed_msg = id_.sign(message);
    manifest.sig = signed_msg.sig;

    auto manifest_json = manifest_to_json(manifest);
    store_.remember_event(id_.doc().did, "epoch_end", manifest.epoch_id,
                          std::vector<uint8_t>(manifest_json.begin(), manifest_json.end()));

    current_epoch_.reset();
    current_start_ = 0;
    return manifest;
}

std::pair<std::string, EpochManifest> Continuum::with_epoch(
    const std::string& manifesto_json, const std::function<void()>& work,
    const std::map<std::string, double>& metrics_at_end) {
    const auto epoch_id = begin_epoch(manifesto_json);
    try {
        work();
    } catch (...) {
        // Optional: callers can extend with rollback/mark-failed semantics.
    }
    auto manifest = end_epoch(metrics_at_end);
    return {epoch_id, manifest};
}

std::optional<EpochManifest> Continuum::latest() const {
    const auto dump = store_.export_since(0);
    auto pos = dump.rfind("\"type\":\"epoch_end\"");
    if (pos == std::string::npos) {
        return std::nullopt;
    }

    auto value_pos = dump.find("\"value_hex\":\"", pos);
    if (value_pos == std::string::npos) {
        return std::nullopt;
    }
    value_pos += 13;  // length of "\"value_hex\":\""
    auto value_end = dump.find("\"", value_pos);
    if (value_end == std::string::npos) {
        return std::nullopt;
    }

    const auto hex = dump.substr(value_pos, value_end - value_pos);
    try {
        auto bytes = hex_to_bytes(hex);
        return parse_manifest_json(std::string(bytes.begin(), bytes.end()));
    } catch (...) {
        return std::nullopt;
    }
}

std::vector<EpochManifest> Continuum::history(std::size_t limit) const {
    std::vector<EpochManifest> manifests;
    const auto dump = store_.export_since(0);
    std::size_t start = 0;
    while (true) {
        auto pos = dump.find("\"type\":\"epoch_end\"", start);
        if (pos == std::string::npos) {
            break;
        }

        auto value_pos = dump.find("\"value_hex\":\"", pos);
        if (value_pos == std::string::npos) {
            break;
        }
        value_pos += 13;
        auto value_end = dump.find("\"", value_pos);
        if (value_end == std::string::npos) {
            break;
        }

        const auto hex = dump.substr(value_pos, value_end - value_pos);
        try {
            auto bytes = hex_to_bytes(hex);
            manifests.push_back(parse_manifest_json(std::string(bytes.begin(), bytes.end())));
        } catch (...) {
            // skip malformed entries but continue scanning for the rest.
        }
        start = value_end;
    }

    if (limit > 0 && manifests.size() > limit) {
        const auto drop = manifests.size() - limit;
        manifests.erase(manifests.begin(), manifests.begin() + static_cast<std::ptrdiff_t>(drop));
    }

    std::reverse(manifests.begin(), manifests.end());
    return manifests;
}

bool Continuum::verify_manifest(const EpochManifest& manifest,
                                const std::vector<uint8_t>& pubkey) {
    if (manifest.sig.empty()) {
        return manifest.parent_id.empty();
    }
    if (pubkey.empty()) {
        return false;
    }
    auto message = canonicalize(manifest);
    return ed25519_verify(pubkey, message, manifest.sig);
}

LineageReport Continuum::analyze_lineage(
    std::size_t limit, const std::vector<uint8_t>& pubkey_override) const {
    LineageReport report;
    const auto manifests = history(limit);
    if (manifests.empty()) {
        return report;
    }

    report.epoch_count = manifests.size();
    report.earliest_start_ms = manifests.front().start_ms;
    report.latest_end_ms = manifests.back().end_ms;

    const auto& verification_key = pubkey_override.empty() ? id_.doc().public_key
                                                          : pubkey_override;
    const bool have_verification_key = !verification_key.empty();
    if (!have_verification_key) {
        report.signatures_valid = false;
    }

    const EpochManifest* previous = nullptr;
    for (const auto& manifest : manifests) {
        if (!report.earliest_start_ms ||
            manifest.start_ms < *report.earliest_start_ms) {
            report.earliest_start_ms = manifest.start_ms;
        }
        if (!report.latest_end_ms || manifest.end_ms > *report.latest_end_ms) {
            report.latest_end_ms = manifest.end_ms;
        }

        if (previous) {
            if (manifest.parent_id != previous->epoch_id) {
                report.is_linear = false;
                report.lineage_breaks.push_back(previous->epoch_id + "->" +
                                               manifest.epoch_id);
            }
        } else if (!manifest.parent_id.empty()) {
            report.is_linear = false;
            report.lineage_breaks.push_back("genesis->" + manifest.epoch_id);
        }

        if (have_verification_key) {
            if (!verify_manifest(manifest, verification_key)) {
                report.signatures_valid = false;
                report.signature_failures.push_back(manifest.epoch_id);
            }
        }

        if (manifest.end_ms >= manifest.start_ms) {
            report.total_duration_ms += manifest.end_ms - manifest.start_ms;
        }

        for (const auto& [metric_key, metric_value] : manifest.metrics) {
            auto& summary = report.metrics[metric_key];
            summary.samples += 1;
            summary.total += metric_value;
            if (summary.samples == 1) {
                summary.minimum = metric_value;
                summary.maximum = metric_value;
            } else {
                summary.minimum = std::min(summary.minimum, metric_value);
                summary.maximum = std::max(summary.maximum, metric_value);
            }
            summary.average =
                summary.total / static_cast<double>(summary.samples);
        }

        previous = &manifest;
    }

    return report;
}

}  // namespace echo

