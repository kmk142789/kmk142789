#pragma once

#include <cstddef>
#include <string>
#include <utility>
#include <vector>

#include "echo/continuum.hpp"

namespace echo {

// A MosaicShard captures the relative influence of a single epoch or metric in the
// emergent TemporalMosaic narrative.
struct MosaicShard {
    std::string key;
    double weight{0.0};
    double emphasis{0.0};
};

// TemporalMosaic is a narrative artifact synthesized from the raw lineage history.
// It weaves epochs, metrics, and anomalies into a compact, glyph-like structure that
// can be rendered or post-processed into higher level storytelling layers.
class TemporalMosaic {
public:
    TemporalMosaic(std::vector<EpochManifest> sequence, LineageReport report);

    const std::vector<EpochManifest>& epochs() const noexcept { return sequence_; }
    const LineageReport& report() const noexcept { return report_; }

    std::vector<MosaicShard> shards() const;
    std::string render() const;

private:
    std::vector<EpochManifest> sequence_;
    LineageReport report_;
};

}  // namespace echo

