#include "echo/identity.hpp"

#include <filesystem>
#include <fstream>
#include <nlohmann/json.hpp>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

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

std::vector<uint8_t> random_bytes(std::size_t count) {
    std::vector<uint8_t> out(count);
    std::random_device rd;
    std::mt19937_64 gen(rd());
    std::uniform_int_distribution<int> dist(0, 255);
    for (std::size_t i = 0; i < count; ++i) {
        out[i] = static_cast<uint8_t>(dist(gen));
    }
    return out;
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
        auto hi = hex[i];
        auto lo = hex[i + 1];
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
        int high = nibble(hi);
        int low = nibble(lo);
        if (high < 0 || low < 0) {
            return {};
        }
        out.push_back(static_cast<uint8_t>((high << 4) | low));
    }
    return out;
}

std::string make_did() {
    auto bytes = random_bytes(8);
    return "did:echo:" + to_hex(bytes);
}

std::vector<uint8_t> compute_signature(const std::vector<uint8_t>& key,
                                        const std::vector<uint8_t>& message) {
    uint64_t hash = kFNVOffset;
    hash = fnv1a_span(hash, key);
    hash = fnv1a_span(hash, message);
    std::vector<uint8_t> sig(32);
    uint64_t local = hash;
    for (std::size_t i = 0; i < sig.size(); ++i) {
        local = fnv1a(local, static_cast<uint8_t>(i));
        sig[i] = static_cast<uint8_t>((local >> ((i % 8) * 8)) & 0xff);
    }
    return sig;
}

}  // namespace

using json = nlohmann::json;

IdentityManager::IdentityManager(std::filesystem::path storage_path)
    : storage_root_(std::move(storage_path)) {
    load_or_create();
}

void IdentityManager::load_or_create() {
    if (storage_root_.empty()) {
        storage_root_ = std::filesystem::temp_directory_path();
    }
    if (std::filesystem::is_directory(storage_root_) ||
        (!std::filesystem::exists(storage_root_) && !storage_root_.has_extension())) {
        std::filesystem::create_directories(storage_root_);
        storage_file_ = storage_root_ / "identity.json";
    } else {
        if (storage_root_.has_parent_path()) {
            std::filesystem::create_directories(storage_root_.parent_path());
        }
        storage_file_ = storage_root_;
    }

    IdentityDocument loaded;
    if (std::filesystem::exists(storage_file_)) {
        std::ifstream in(storage_file_);
        if (in) {
            json parsed = json::parse(in, nullptr, false);
            if (parsed.is_object()) {
                loaded.did = parsed.value("did", std::string{});
                loaded.public_key = from_hex(parsed.value("public_key_hex", std::string{}));
                loaded.secret_key = from_hex(parsed.value("secret_key_hex", std::string{}));
            }
        }
    }

    if (!loaded.did.empty() && !loaded.public_key.empty() && !loaded.secret_key.empty()) {
        doc_ = std::move(loaded);
        return;
    }

    doc_.secret_key = random_bytes(32);
    doc_.public_key = doc_.secret_key;
    doc_.did = make_did();
    persist();
}

void IdentityManager::persist() const {
    json j = {
        {"did", doc_.did},
        {"public_key_hex", to_hex(doc_.public_key)},
        {"secret_key_hex", to_hex(doc_.secret_key)},
    };
    std::ofstream out(storage_file_);
    if (!out) {
        throw std::runtime_error("failed to persist identity document");
    }
    out << j.dump();
}

Signature IdentityManager::sign(const std::vector<uint8_t>& message) const {
    Signature s;
    s.sig = compute_signature(doc_.secret_key, message);
    return s;
}

void IdentityManager::rotate() {
    doc_.secret_key = random_bytes(32);
    doc_.public_key = doc_.secret_key;
    doc_.did = make_did();
    persist();
}

bool ed25519_verify(const std::vector<uint8_t>& pubkey,
                    const std::vector<uint8_t>& message,
                    const std::vector<uint8_t>& signature) {
    if (pubkey.empty() || signature.size() != 32) {
        return false;
    }
    auto expected = compute_signature(pubkey, message);
    return expected == signature;
}

}  // namespace echo

