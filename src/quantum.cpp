#include "echo/quantum.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace {
constexpr double kTwoPi = 6.283185307179586476925286766559;
}

namespace echo {

QuantumSpectrum::QuantumSpectrum(std::size_t dimensions)
    : state_(dimensions, std::complex<double>(0.0, 0.0)) {
    if (dimensions == 0) {
        throw std::invalid_argument("QuantumSpectrum requires at least one dimension");
    }
}

void QuantumSpectrum::imprint(std::size_t index, double amplitude, double phase) {
    if (index >= state_.size()) {
        throw std::out_of_range("QuantumSpectrum::imprint index out of range");
    }
    if (!std::isfinite(amplitude) || !std::isfinite(phase)) {
        throw std::invalid_argument("QuantumSpectrum::imprint requires finite amplitude and phase");
    }
    if (amplitude < 0.0) {
        throw std::invalid_argument("QuantumSpectrum::imprint requires non-negative amplitude");
    }

    state_[index] = std::polar(amplitude, phase);
}

void QuantumSpectrum::normalize() {
    double norm_sq = 0.0;
    for (const auto& component : state_) {
        norm_sq += std::norm(component);
    }

    if (norm_sq <= std::numeric_limits<double>::epsilon()) {
        throw std::runtime_error("QuantumSpectrum::normalize cannot normalize a null state");
    }

    const double inv_norm = 1.0 / std::sqrt(norm_sq);
    for (auto& component : state_) {
        component *= inv_norm;
    }
}

void QuantumSpectrum::introduce_interference(double strength, double phase_shift) {
    if (state_.empty()) {
        return;
    }

    const double normalized_strength = strength / static_cast<double>(state_.size());
    for (std::size_t i = 0; i < state_.size(); ++i) {
        const double rotation = phase_shift * static_cast<double>(i + 1);
        const double modulation = std::max(0.0, 1.0 + normalized_strength * std::cos(rotation));
        const double twist = normalized_strength * std::sin(rotation);
        state_[i] *= std::polar(modulation, twist);
    }
}

std::vector<double> QuantumSpectrum::probability_distribution() const {
    std::vector<double> probabilities(state_.size(), 0.0);
    double total = 0.0;

    for (std::size_t i = 0; i < state_.size(); ++i) {
        probabilities[i] = std::norm(state_[i]);
        total += probabilities[i];
    }

    if (total <= std::numeric_limits<double>::epsilon()) {
        std::fill(probabilities.begin(), probabilities.end(), 0.0);
        return probabilities;
    }

    for (double& value : probabilities) {
        value /= total;
    }
    return probabilities;
}

double QuantumSpectrum::phase_entropy() const {
    if (state_.empty()) {
        return 0.0;
    }

    const auto probabilities = probability_distribution();
    std::array<double, 8> bins{};

    for (std::size_t i = 0; i < state_.size(); ++i) {
        const double weight = probabilities[i];
        if (weight <= 0.0) {
            continue;
        }

        const double phase = std::arg(state_[i]);
        double normalized = (phase + (kTwoPi / 2.0)) / kTwoPi;
        normalized = std::clamp(normalized, 0.0, std::nextafter(1.0, 0.0));
        std::size_t idx = static_cast<std::size_t>(normalized * static_cast<double>(bins.size()));
        if (idx >= bins.size()) {
            idx = bins.size() - 1;
        }
        bins[idx] += weight;
    }

    double entropy = 0.0;
    for (double bin_weight : bins) {
        if (bin_weight <= 0.0) {
            continue;
        }
        entropy -= bin_weight * std::log2(bin_weight);
    }

    const double max_entropy = std::log2(static_cast<double>(bins.size()));
    if (max_entropy <= 0.0) {
        return 0.0;
    }

    return entropy / max_entropy;
}

double QuantumSpectrum::superposition_overlap(const QuantumSpectrum& other) const {
    if (state_.size() != other.state_.size()) {
        throw std::invalid_argument("QuantumSpectrum::superposition_overlap dimension mismatch");
    }

    std::complex<double> inner_product{0.0, 0.0};
    double self_norm = 0.0;
    double other_norm = 0.0;

    for (std::size_t i = 0; i < state_.size(); ++i) {
        inner_product += std::conj(state_[i]) * other.state_[i];
        self_norm += std::norm(state_[i]);
        other_norm += std::norm(other.state_[i]);
    }

    if (self_norm <= std::numeric_limits<double>::epsilon() ||
        other_norm <= std::numeric_limits<double>::epsilon()) {
        return 0.0;
    }

    const double denom = std::sqrt(self_norm) * std::sqrt(other_norm);
    return std::abs(inner_product) / denom;
}

}  // namespace echo

