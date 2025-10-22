#include "echo/resonance.hpp"

#include <algorithm>
#include <array>
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

SpectralFingerprint ResonanceField::unprecedented_signature(const std::vector<ResonantPulse>& pulses) const {
    SpectralFingerprint fingerprint;
    if (pulses.empty()) {
        return fingerprint;
    }

    if (pulses.size() == 1) {
        const double seed_guard = std::max(1.0, std::abs(seed_));
        fingerprint.harmony_wander = std::abs(pulses.front().harmony);
        fingerprint.strangeness_index = (std::abs(pulses.front().energy - seed_) + fingerprint.harmony_wander) / seed_guard;
        return fingerprint;
    }

    double energy_flux = 0.0;
    double harmony_wander = 0.0;
    std::array<double, 6> rhythm_bins{};

    for (const auto& pulse : pulses) {
        const double clamped = std::clamp(pulse.rhythm, 0.0, 0.999999);
        std::size_t idx = static_cast<std::size_t>(clamped * static_cast<double>(rhythm_bins.size()));
        if (idx >= rhythm_bins.size()) {
            idx = rhythm_bins.size() - 1;
        }
        rhythm_bins[idx] += 1.0;
    }

    for (std::size_t i = 1; i < pulses.size(); ++i) {
        const auto& prev = pulses[i - 1];
        const auto& current = pulses[i];
        energy_flux += std::abs(current.energy - prev.energy);
        harmony_wander += std::abs(current.harmony - prev.harmony);
    }

    const double total_samples = static_cast<double>(pulses.size());
    double entropy = 0.0;
    for (double count : rhythm_bins) {
        if (count <= 0.0) {
            continue;
        }
        const double probability = count / total_samples;
        entropy -= probability * std::log2(probability);
    }

    const double modulation_guard = std::max(1.0, std::abs(modulation_) + 0.5);
    const double harmonic_weight = std::max(1.0, static_cast<double>(harmonics_.size()));
    const double step_normalizer = std::max(1.0, static_cast<double>(pulses.size() - 1));

    fingerprint.energy_flux = energy_flux / step_normalizer;
    fingerprint.harmony_wander = harmony_wander / step_normalizer;
    fingerprint.rhythm_entropy = entropy;

    const double coherence = coherence_score(pulses);
    const double volatility = (fingerprint.energy_flux + fingerprint.harmony_wander) / (modulation_guard * harmonic_weight);
    fingerprint.strangeness_index = volatility * (1.5 - coherence) + entropy * 0.25;

    return fingerprint;
}

}  // namespace echo

