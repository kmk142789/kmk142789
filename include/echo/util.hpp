#pragma once

#include <cstdint>

namespace echo {

// Returns the current system time in milliseconds since the UNIX epoch.
uint64_t now_ms();

}  // namespace echo

