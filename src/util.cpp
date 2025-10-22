#include "echo/util.hpp"

#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>

namespace echo {

uint64_t now_ms() {
    const auto now = std::chrono::time_point_cast<std::chrono::milliseconds>(
        std::chrono::system_clock::now());
    return static_cast<uint64_t>(now.time_since_epoch().count());
}

std::string format_iso8601(const std::chrono::system_clock::time_point& time_point) {
    const auto time = std::chrono::system_clock::to_time_t(time_point);
    std::tm utc{};
#if defined(_WIN32)
    gmtime_s(&utc, &time);
#else
    gmtime_r(&time, &utc);
#endif

    std::ostringstream stream;
    stream << std::put_time(&utc, "%Y-%m-%dT%H:%M:%S");
    const auto milliseconds = std::chrono::duration_cast<std::chrono::milliseconds>(
        time_point.time_since_epoch()) % 1000;
    stream << '.' << std::setw(3) << std::setfill('0') << milliseconds.count() << 'Z';
    return stream.str();
}

std::string format_iso8601() { return format_iso8601(std::chrono::system_clock::now()); }

}  // namespace echo

