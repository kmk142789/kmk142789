# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

_No unreleased changes yet._

## [0.9.0] - 2025-05-11

### Added
- Configured `semantic-release` with conventional commit parsing, automated changelog generation, and GitHub asset publishing so new tags are promoted as `v0.9.0` releases with bundled metadata. 
- Introduced a cross-language release pipeline that aggregates pytest, npm, and Go client checks, builds Docker/Helm artifacts, and stages multi-language SDK packages for mock publishing.
- Authored tooling to synthesize release metadata (SLO metrics, aggregated test totals, SBOM inventory, and Cosign attestations) and collate it alongside dashboards, provenance, and site bundles.

### Changed
- Normalized package versions to `0.9.0` across Node and Python distributions to align with the new release cadence.

### Operations
- Documented the v0.9.0 release, including SLO dashboards, Cosign attestations, SBOM references, and release bundle composition.

## [1.0.0] - 2025-11-08

### Added
- Introduced the Echo Titan generator for provisioning the 10k+ scale deployment engine.
- Added documentation anchors describing the Echo Titan subsystems and surprise lore.
- Registered CI integration scaffolding instructions for Echo Titan.
- Published deployment readiness guidance covering setup, environment configuration, and rollout steps.

### Changed
- Curated the primary README to include a deployment checklist that must be followed before promoting a release.

### Operations
- Certified the v1.0 delivery path by executing the repository test suite and documenting the results.
