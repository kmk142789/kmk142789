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

// Snapshot of how a pulse sequence behaved across multiple perceptual axes.
struct SpectralFingerprint {
    double energy_flux{0.0};
    double rhythm_entropy{0.0};
    double harmony_wander{0.0};
    double strangeness_index{0.0};
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

    // Distill an unprecedented signature from the supplied pulses, capturing
    // how wildly the energies, rhythms, and harmonics evolve together.
    SpectralFingerprint unprecedented_signature(const std::vector<ResonantPulse>& pulses) const;

private:
    double seed_;
    double modulation_;
    std::vector<std::pair<double, double>> harmonics_;
};

}  // namespace echo

