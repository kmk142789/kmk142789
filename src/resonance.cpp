#include "echo/resonance.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace echo {
namespace {
constexpr double kTwoPi = 6.283185307179586476925286766559;
}

ResonanceField::ResonanceField(double seed_frequency, double modulation_depth)
    : seed_(seed_frequency), modulation_(modulation_depth) {
    if (seed_frequency <= 0.0) {
        throw std::invalid_argument("seed_frequency must be positive");
    }
    if (modulation_depth < 0.0) {
        throw std::invalid_argument("modulation_depth cannot be negative");
    }
}

void ResonanceField::add_harmonic(double amplitude, double frequency_ratio) {
    if (amplitude == 0.0) {
        return;
    }
    if (frequency_ratio <= 0.0) {
        throw std::invalid_argument("frequency_ratio must be positive");
    }
    harmonics_.emplace_back(amplitude, frequency_ratio);
}

std::vector<ResonantPulse> ResonanceField::compose(std::size_t steps) const {
    if (steps == 0) {
        return {};
    }

    std::vector<ResonantPulse> pulses;
    pulses.reserve(steps);

    const double baseline = seed_;
    for (std::size_t i = 0; i < steps; ++i) {
        const double progress = steps > 1 ? static_cast<double>(i) / static_cast<double>(steps - 1) : 0.0;
        const double modulation = modulation_ * std::sin(progress * kTwoPi);
        double energy = baseline + modulation;
        double rhythm = progress;
        double harmony = 0.0;

        for (const auto& harmonic : harmonics_) {
            const double phase = progress * harmonic.second * kTwoPi;
            const double contribution = harmonic.first * std::cos(phase);
            energy += contribution;
            harmony += std::sin(phase) * harmonic.first;
        }

        pulses.push_back({energy, rhythm, harmony});
    }

    return pulses;
}

double ResonanceField::coherence_score(const std::vector<ResonantPulse>& pulses) const {
    if (pulses.empty()) {
        return 0.0;
    }

    double energy_sum = 0.0;
    double harmony_sum = 0.0;
    for (const auto& pulse : pulses) {
        energy_sum += pulse.energy;
        harmony_sum += std::abs(pulse.harmony);
    }

    const double energy_avg = energy_sum / static_cast<double>(pulses.size());
    const double harmony_avg = harmony_sum / static_cast<double>(pulses.size());
    const double normalizer = seed_ + static_cast<double>(harmonics_.size());
    if (normalizer <= 0.0) {
        return 0.0;
    }

    const double ratio = (energy_avg + harmony_avg) / (2.0 * normalizer);
    return std::clamp(ratio, 0.0, 1.0);
}

}  // namespace echo

