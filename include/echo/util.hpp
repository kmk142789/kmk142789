#pragma once

#include <chrono>
#include <cstdint>
#include <string>

namespace echo {

// Returns the current system time in milliseconds since the UNIX epoch.
uint64_t now_ms();

// Formats the provided time point as an ISO-8601 string in UTC with millisecond
// precision. When no argument is provided, the current system time is used.
std::string format_iso8601(const std::chrono::system_clock::time_point& time_point);
std::string format_iso8601();

}  // namespace echo

