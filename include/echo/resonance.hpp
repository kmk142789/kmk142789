#pragma once

#include <cstddef>
#include <utility>
#include <vector>

namespace echo {

// A single resonant measurement within a generated pattern.
struct ResonantPulse {
    double energy{0.0};
    double rhythm{0.0};
    double harmony{0.0};
};

// ResonanceField composes fractal-inspired pulse patterns from a few harmonic hints.
class ResonanceField {
public:
    ResonanceField(double seed_frequency, double modulation_depth);

    // Register an additional harmonic contribution.
    void add_harmonic(double amplitude, double frequency_ratio);

    // Generate a sequence of resonant pulses following the configured harmonics.
    std::vector<ResonantPulse> compose(std::size_t steps) const;

    // Evaluate how internally coherent a sequence of pulses is with this field.
    double coherence_score(const std::vector<ResonantPulse>& pulses) const;

private:
    double seed_;
    double modulation_;
    std::vector<std::pair<double, double>> harmonics_;
};

}  // namespace echo

