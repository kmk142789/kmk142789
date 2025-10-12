#pragma once

#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>

namespace echo {

class MemoryStore {
public:
    explicit MemoryStore(std::filesystem::path root_dir);

    std::string put_blob(const std::vector<uint8_t>& blob);

    void remember_event(const std::string& actor_did,
                        const std::string& type,
                        const std::string& key,
                        const std::vector<uint8_t>& value);

    std::string head_hash() const;

    std::string export_since(uint64_t since_ms) const;

    std::filesystem::path root() const { return root_dir_; }

private:
    struct Event {
        uint64_t ts_ms{};
        std::string actor_did;
        std::string type;
        std::string key;
        std::vector<uint8_t> value;
    };

    void ensure_paths();
    void load_events();
    void append_event(const Event& ev);
    void update_head_hash(const Event& ev);

    static std::string to_hex(const std::vector<uint8_t>& data);
    static std::vector<uint8_t> from_hex(const std::string& hex);
    static std::vector<uint8_t> digest_bytes(const std::vector<uint8_t>& data);
    static std::string digest_hex(const std::vector<uint8_t>& data);

    std::filesystem::path root_dir_;
    std::filesystem::path blobs_dir_;
    std::filesystem::path events_file_;
    std::vector<Event> events_;
    uint64_t head_hash_state_;
};

}  // namespace echo

