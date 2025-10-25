#pragma once

#include <cstddef>
#include <complex>
#include <vector>

namespace echo {

// QuantumSpectrum models a finite-dimensional quantum state vector. It exposes
// helper routines to normalize amplitudes, estimate phase entropy, and measure
// overlaps between superpositions. The intent is to offer a light-weight
// playground for quantum-inspired ideas alongside the other continuum tools.
class QuantumSpectrum {
public:
    explicit QuantumSpectrum(std::size_t dimensions);

    // Imprint an amplitude/phase pair on a specific basis index. The amplitude
    // is interpreted as a real magnitude, while the phase is measured in
    // radians.
    void imprint(std::size_t index, double amplitude, double phase);

    // Scale the state so that the amplitudes sum to unit probability mass.
    void normalize();

    // Introduce a deterministic interference pattern. The strength parameter
    // controls how much modulation is applied per basis state, while
    // phase_shift tweaks the rotation applied to subsequent components.
    void introduce_interference(double strength, double phase_shift);

    // Retrieve the measurement probabilities associated with each basis state.
    std::vector<double> probability_distribution() const;

    // Estimate the entropy of the phase distribution (0 = perfectly aligned,
    // 1 = maximally diffused across the chosen histogram bins).
    double phase_entropy() const;

    // Compute the normalized overlap between this spectrum and another.
    double superposition_overlap(const QuantumSpectrum& other) const;

private:
    std::vector<std::complex<double>> state_;
};

}  // namespace echo

