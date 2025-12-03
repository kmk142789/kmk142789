#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace echo {

struct IdentityDocument {
    std::string did;
    std::vector<uint8_t> public_key;
    std::vector<uint8_t> secret_key;
};

struct Signature {
    std::vector<uint8_t> sig;
};

class IdentityManager {
public:
    explicit IdentityManager(std::filesystem::path storage_path);

    static std::filesystem::path default_storage_path();

    const IdentityDocument& doc() const noexcept { return doc_; }

    Signature sign(const std::vector<uint8_t>& message) const;

    void rotate();

    std::filesystem::path storage_path() const { return storage_file_; }

private:
    void load_or_create();
    void persist() const;

    IdentityDocument doc_;
    std::filesystem::path storage_root_;
    std::filesystem::path storage_file_;
};

bool ed25519_verify(const std::vector<uint8_t>& pubkey,
                    const std::vector<uint8_t>& message,
                    const std::vector<uint8_t>& signature);

}  // namespace echo

