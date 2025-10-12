#include "echo/memory.hpp"

#include <filesystem>
#include <fstream>
#include <nlohmann/json.hpp>
#include <sstream>
#include <stdexcept>

#include "echo/util.hpp"

namespace echo {
namespace {

constexpr uint64_t kFNVOffset = 1469598103934665603ULL;
constexpr uint64_t kFNVPrime = 1099511628211ULL;

uint64_t fnv1a(uint64_t hash, uint8_t byte) {
    hash ^= byte;
    hash *= kFNVPrime;
    return hash;
}

uint64_t fnv1a_span(uint64_t hash, const std::vector<uint8_t>& data) {
    for (auto b : data) {
        hash = fnv1a(hash, b);
    }
    return hash;
}

std::string to_hex(const std::vector<uint8_t>& data) {
    static constexpr char kHex[] = "0123456789abcdef";
    std::string out;
    out.reserve(data.size() * 2);
    for (auto b : data) {
        out.push_back(kHex[b >> 4]);
        out.push_back(kHex[b & 0x0f]);
    }
    return out;
}

std::vector<uint8_t> from_hex(const std::string& hex) {
    std::vector<uint8_t> out;
    if (hex.size() % 2 != 0) {
        return out;
    }
    out.reserve(hex.size() / 2);
    for (std::size_t i = 0; i < hex.size(); i += 2) {
        auto nibble = [](char c) -> int {
            if (c >= '0' && c <= '9') {
                return c - '0';
            }
            if (c >= 'a' && c <= 'f') {
                return 10 + (c - 'a');
            }
            if (c >= 'A' && c <= 'F') {
                return 10 + (c - 'A');
            }
            return -1;
        };
        int high = nibble(hex[i]);
        int low = nibble(hex[i + 1]);
        if (high < 0 || low < 0) {
            return {};
        }
        out.push_back(static_cast<uint8_t>((high << 4) | low));
    }
    return out;
}

std::vector<uint8_t> digest_bytes(const std::vector<uint8_t>& data) {
    std::vector<uint8_t> out(32);
    uint64_t hash = fnv1a_span(kFNVOffset, data);
    uint64_t local = hash;
    for (std::size_t i = 0; i < out.size(); ++i) {
        local = fnv1a(local, static_cast<uint8_t>(i));
        out[i] = static_cast<uint8_t>((local >> ((i % 8) * 8)) & 0xff);
    }
    return out;
}

std::string digest_hex(const std::vector<uint8_t>& data) {
    return to_hex(digest_bytes(data));
}

std::vector<uint8_t> fingerprint(const MemoryStore::Event& ev) {
    std::ostringstream oss;
    oss << ev.ts_ms << '|' << ev.actor_did << '|' << ev.type << '|' << ev.key << '|';
    const auto hex = to_hex(ev.value);
    oss << hex;
    const auto text = oss.str();
    return std::vector<uint8_t>(text.begin(), text.end());
}

}  // namespace

using json = nlohmann::json;

MemoryStore::MemoryStore(std::filesystem::path root_dir)
    : root_dir_(std::move(root_dir)), head_hash_state_(kFNVOffset) {
    ensure_paths();
    load_events();
}

void MemoryStore::ensure_paths() {
    if (root_dir_.empty()) {
        root_dir_ = std::filesystem::temp_directory_path() / "echo-memory";
    }
    std::filesystem::create_directories(root_dir_);
    blobs_dir_ = root_dir_ / "blobs";
    events_file_ = root_dir_ / "events.jsonl";
    std::filesystem::create_directories(blobs_dir_);
    if (!std::filesystem::exists(events_file_)) {
        std::ofstream(events_file_).close();
    }
}

void MemoryStore::load_events() {
    events_.clear();
    head_hash_state_ = kFNVOffset;
    std::ifstream in(events_file_);
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) {
            continue;
        }
        json parsed = json::parse(line, nullptr, false);
        if (!parsed.is_object()) {
            continue;
        }
        Event ev;
        ev.ts_ms = parsed.value("ts_ms", uint64_t{0});
        ev.actor_did = parsed.value("actor_did", std::string{});
        ev.type = parsed.value("type", std::string{});
        ev.key = parsed.value("key", std::string{});
        auto value_hex = parsed.value("value_hex", std::string{});
        if (value_hex.empty() && parsed.contains("value")) {
            const auto& node = parsed["value"];
            if (node.is_string()) {
                const auto raw = node.get<std::string>();
                ev.value.assign(raw.begin(), raw.end());
            } else if (node.is_array()) {
                for (const auto& v : node) {
                    if (v.is_number_unsigned()) {
                        ev.value.push_back(static_cast<uint8_t>(v.get<uint64_t>()));
                    }
                }
            }
        } else {
            ev.value = from_hex(value_hex);
        }
        events_.push_back(ev);
        update_head_hash(ev);
    }
}

std::string MemoryStore::put_blob(const std::vector<uint8_t>& blob) {
    auto digest = digest_hex(blob);
    auto filename = digest + ".bin";
    auto path = blobs_dir_ / filename;
    if (!std::filesystem::exists(path)) {
        std::ofstream out(path, std::ios::binary);
        if (!out) {
            throw std::runtime_error("failed to write blob");
        }
        out.write(reinterpret_cast<const char*>(blob.data()), static_cast<std::streamsize>(blob.size()));
    }
    return digest;
}

void MemoryStore::remember_event(const std::string& actor_did,
                                 const std::string& type,
                                 const std::string& key,
                                 const std::vector<uint8_t>& value) {
    Event ev;
    ev.ts_ms = now_ms();
    ev.actor_did = actor_did;
    ev.type = type;
    ev.key = key;
    ev.value = value;
    events_.push_back(ev);
    update_head_hash(ev);
    append_event(ev);
}

void MemoryStore::append_event(const Event& ev) {
    json j = {
        {"ts_ms", ev.ts_ms},
        {"actor_did", ev.actor_did},
        {"type", ev.type},
        {"key", ev.key},
        {"value_hex", to_hex(ev.value)},
    };
    std::ofstream out(events_file_, std::ios::app);
    if (!out) {
        throw std::runtime_error("failed to append to event log");
    }
    out << j.dump() << '\n';
}

void MemoryStore::update_head_hash(const Event& ev) {
    auto fp = fingerprint(ev);
    head_hash_state_ = fnv1a_span(head_hash_state_, fp);
}

std::string MemoryStore::head_hash() const {
    uint64_t value = head_hash_state_;
    std::vector<uint8_t> bytes(8);
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        bytes[i] = static_cast<uint8_t>((value >> ((7 - i) * 8)) & 0xff);
    }
    return to_hex(bytes);
}

std::string MemoryStore::export_since(uint64_t since_ms) const {
    json events = json::array();
    for (const auto& ev : events_) {
        if (ev.ts_ms < since_ms) {
            continue;
        }
        events.push_back({
            {"ts_ms", ev.ts_ms},
            {"actor_did", ev.actor_did},
            {"type", ev.type},
            {"key", ev.key},
            {"value_hex", to_hex(ev.value)},
        });
    }
    json out = {
        {"head_hash", head_hash()},
        {"events", events},
    };
    return out.dump();
}

std::string MemoryStore::to_hex(const std::vector<uint8_t>& data) {
    return ::to_hex(data);
}

std::vector<uint8_t> MemoryStore::from_hex(const std::string& hex) {
    return ::from_hex(hex);
}

std::vector<uint8_t> MemoryStore::digest_bytes(const std::vector<uint8_t>& data) {
    return ::digest_bytes(data);
}

std::string MemoryStore::digest_hex(const std::vector<uint8_t>& data) {
    return ::digest_hex(data);
}

}  // namespace echo

