#pragma once

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

    // Verify signature & lineage of a manifest against local DID (or provided pk)
    static bool verify_manifest(const EpochManifest& manifest,
                                const std::vector<uint8_t>& pubkey);

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

