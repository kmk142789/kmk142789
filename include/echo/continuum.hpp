#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

#include "echo/identity.hpp"
#include "echo/memory.hpp"

namespace echo {

class TemporalMosaic;

// Immutable epoch summary recorded in the event log
struct EpochManifest {
    std::string epoch_id;        // e.g. "epoch-2025-10-12T08:31:22Z-001"
    std::string parent_id;       // previous epoch_id ("" for genesis)
    std::string head_hash;       // MemoryStore::head_hash() at close
    std::string manifesto_cid;   // optional: CID to a larger JSON manifesto blob
    std::map<std::string, double> metrics; // arbitrary numeric metrics
    uint64_t start_ms{};
    uint64_t end_ms{};
    std::string did;             // signer DID
    std::vector<uint8_t> sig;    // Ed25519 signature over canonical form
};

struct MetricSummary {
    double total{0.0};
    double minimum{0.0};
    double maximum{0.0};
    double average{0.0};
    std::size_t samples{0};
};

struct LineageReport {
    std::size_t epoch_count{};
    bool is_linear{true};
    bool signatures_valid{true};
    std::vector<std::string> lineage_breaks;
    std::vector<std::string> signature_failures;
    std::vector<std::string> temporal_anomalies;
    std::optional<uint64_t> earliest_start_ms;
    std::optional<uint64_t> latest_end_ms;
    uint64_t total_duration_ms{};
    double continuity_score{1.0};
    double tempo_consistency{1.0};
    std::map<std::string, MetricSummary> metrics;
    std::map<std::string, double> metric_trends;
};

// Continuum = epoch manager + lineage verification
class Continuum {
public:
    Continuum(MemoryStore& store, IdentityManager& id);

    // Begin a new epoch, returns epoch_id. If one is open, it's closed first.
    std::string begin_epoch(const std::string& manifesto_json = {});

    // Close current epoch with metrics; returns the finalized manifest.
    EpochManifest end_epoch(const std::map<std::string, double>& metrics);

    // Convenience: complete a short epoch (begin → user work → end)
    std::pair<std::string, EpochManifest>
    with_epoch(const std::string& manifesto_json,
               const std::function<void()>& work,
               const std::map<std::string, double>& metrics_at_end);

    // Accessors
    std::optional<EpochManifest> latest() const;
    std::vector<EpochManifest> history(std::size_t limit = 20) const;

    // Summarize recent history continuity, metrics, and signature validity.
    LineageReport analyze_lineage(
        std::size_t limit = 0,
        const std::vector<uint8_t>& pubkey_override = {}) const;

    // Verify signature & lineage of a manifest against local DID (or provided pk)
    static bool verify_manifest(const EpochManifest& manifest,
                                const std::vector<uint8_t>& pubkey);

    TemporalMosaic craft_temporal_mosaic(std::size_t depth = 12) const;

private:
    MemoryStore& store_;
    IdentityManager& id_;
    std::optional<std::string> current_epoch_;
    uint64_t current_start_{};

    static std::string make_epoch_id(uint64_t start_ms);
    static std::vector<uint8_t> canonicalize(const EpochManifest& manifest);
    static std::string metrics_to_json(const std::map<std::string, double>& metrics);
    static EpochManifest parse_manifest_json(const std::string& json_blob);
    static std::string manifest_to_json(const EpochManifest& manifest);
};

}  // namespace echo

