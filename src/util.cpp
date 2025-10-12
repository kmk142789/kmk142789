#include "echo/util.hpp"

#include <chrono>

namespace echo {

uint64_t now_ms() {
    const auto now = std::chrono::time_point_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now());
    return static_cast<uint64_t>(now.time_since_epoch().count());
}

}  // namespace echo

