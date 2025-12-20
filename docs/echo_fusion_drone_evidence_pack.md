# Echo Fusion Drone — Evidence Pack Format

## Purpose
Define a repeatable, auditable evidence pack for the **Echo Fusion Drone** that captures key engineering analyses and their provenance. The format is designed for traceability, review, and independent verification.

## Pack Structure
Each evidence pack is a folder with a mandatory manifest and standardized subfolders.

```
EchoFusionDrone_EvidencePack_<program>_<pack-id>_<version>/
├─ manifest.json
├─ README.md
├─ cfd/
│  ├─ assumptions.md
│  ├─ mesh_summary.json
│  ├─ solver_settings.json
│  ├─ results/
│  │  ├─ pressure_fields.vtk
│  │  ├─ velocity_fields.vtk
│  │  ├─ convergence_plots.pdf
│  ├─ provenance/
│  │  ├─ git_state.json
│  │  ├─ run_log.txt
├─ thrust/
│  ├─ test_plan.md
│  ├─ raw_data/
│  │  ├─ thrust_sweep.csv
│  ├─ processed/
│  │  ├─ thrust_curve.csv
│  │  ├─ efficiency_map.csv
│  ├─ calibration/
│  │  ├─ load_cell_calibration.json
├─ acoustics/
│  ├─ test_plan.md
│  ├─ raw_data/
│  │  ├─ mic_array_signals.wav
│  ├─ processed/
│  │  ├─ spl_spectrum.csv
│  │  ├─ octave_band_levels.csv
│  ├─ environment/
│  │  ├─ background_noise_profile.csv
├─ governance/
│  ├─ test_plan.md
│  ├─ raw_data/
│  │  ├─ state_transitions.jsonl
│  │  ├─ power_ledger.jsonl
│  │  ├─ violation_events.jsonl
│  ├─ processed/
│  │  ├─ derating_summary.csv
│  │  ├─ constraint_compliance_report.pdf
├─ thermal/
│  ├─ test_plan.md
│  ├─ raw_data/
│  │  ├─ thermocouple_logs.csv
│  ├─ processed/
│  │  ├─ thermal_limits_report.pdf
│  ├─ models/
│  │  ├─ thermal_fea_summary.json
├─ fatigue/
│  ├─ test_plan.md
│  ├─ raw_data/
│  │  ├─ strain_gauge_cycles.csv
│  ├─ processed/
│  │  ├─ sn_curve.csv
│  │  ├─ damage_accumulation.json
└─ verification/
   ├─ checksums.sha256
   ├─ signatures/
   │  ├─ manifest.sig
   ├─ verification_report.md
```

## Manifest (Required)
**File:** `manifest.json`

The manifest binds all artifacts to assumptions, models, and test conditions. It is the source of truth for versioning and verification.

### Required Fields
```json
{
  "pack_id": "EFD-EP-00042",
  "program": "EchoFusionDrone",
  "version": "1.2.0",
  "created_utc": "2025-10-08T12:40:00Z",
  "owner": "Echo Aerospace Lab",
  "hardware_revision": "EFD-HW-R3",
  "software_revision": "EFD-SW-4.8.1",
  "configuration_id": "CFG-THRUST-STD-01",
  "assumptions": {
    "cfd": "cfd/assumptions.md",
    "thermal": "thermal/test_plan.md",
    "fatigue": "fatigue/test_plan.md"
  },
  "artifacts": [
    {
      "id": "cfd.mesh_summary",
      "path": "cfd/mesh_summary.json",
      "type": "analysis",
      "sha256": "<sha256>"
    },
    {
      "id": "thrust.thrust_curve",
      "path": "thrust/processed/thrust_curve.csv",
      "type": "test",
      "sha256": "<sha256>"
    },
    {
      "id": "acoustics.spl_spectrum",
      "path": "acoustics/processed/spl_spectrum.csv",
      "type": "test",
      "sha256": "<sha256>"
    },
    {
      "id": "governance.state_transitions",
      "path": "governance/raw_data/state_transitions.jsonl",
      "type": "test",
      "sha256": "<sha256>"
    },
    {
      "id": "governance.power_ledger",
      "path": "governance/raw_data/power_ledger.jsonl",
      "type": "test",
      "sha256": "<sha256>"
    },
    {
      "id": "governance.constraint_compliance_report",
      "path": "governance/processed/constraint_compliance_report.pdf",
      "type": "analysis",
      "sha256": "<sha256>"
    },
    {
      "id": "thermal.thermal_limits_report",
      "path": "thermal/processed/thermal_limits_report.pdf",
      "type": "analysis",
      "sha256": "<sha256>"
    },
    {
      "id": "fatigue.sn_curve",
      "path": "fatigue/processed/sn_curve.csv",
      "type": "analysis",
      "sha256": "<sha256>"
    }
  ],
  "generation": {
    "pipeline_version": "evidence-pack-cli@0.9.0",
    "pipeline_config": "config/evidence_pack.yml",
    "source_repo": "git@repo.example.com:echo/flight.git",
    "source_commit": "<commit-sha>",
    "build_id": "CI-20251008-3371"
  },
  "verification": {
    "checksum_file": "verification/checksums.sha256",
    "signature_file": "verification/signatures/manifest.sig",
    "signed_by": "security@echo-aero.example",
    "verification_report": "verification/verification_report.md"
  }
}
```

## Evidence Categories (Required Content)

### 1) CFD Assumptions
**Location:** `cfd/assumptions.md`

Include:
- Geometry revision and mesh strategy
- Turbulence model and wall functions
- Boundary conditions (inlet/outlet, pressure, temperature)
- Fluid properties and environmental conditions
- Solver convergence criteria and stability settings

### 2) Thrust Data
**Location:** `thrust/`

Include:
- Test plan with instrumentation and calibration (`test_plan.md`)
- Raw thrust sweeps (`raw_data/thrust_sweep.csv`)
- Processed thrust curves and efficiency maps (`processed/*.csv`)
- Calibration certificates for load cells

### 3) Acoustic Profiles
**Location:** `acoustics/`

Include:
- Microphone array configuration and placement
- SPL spectrum and octave-band results (`processed/*.csv`)
- Background noise profile and environmental conditions

### 4) Thermal Tests
**Location:** `thermal/`

Include:
- Thermal test plan with dwell and ramp profiles
- Thermocouple and IR camera logs (`raw_data/*.csv`)
- Thermal FEA summary and limit compliance report

### 5) Governance & Power Compliance
**Location:** `governance/`

Include:
- Governance test plan mapping to the Flight Mode Constitution
- State transition logs and violation events (`raw_data/*.jsonl`)
- Power source contribution ledger with cap enforcement
- Constraint compliance report (thermal, acoustic, power caps)

### 6) Fatigue Analysis
**Location:** `fatigue/`

Include:
- Fatigue test plan and duty cycle definitions
- Strain gauge raw cycles (`raw_data/*.csv`)
- S-N curves and cumulative damage model outputs

## Artifact Generation
Evidence packs are produced with an automated pipeline and controlled manual checkpoints.

1. **Data capture** from lab equipment or simulation pipelines.
2. **Normalization** into standard CSV/JSON/PDF schemas.
3. **Automated processing** (plots, curve fitting, and summaries).
4. **Manifest assembly** with hashes and provenance metadata.
5. **Signing and verification** using the verification bundle.

## Versioning
- **Semantic Versioning** for the pack: `MAJOR.MINOR.PATCH`.
  - **MAJOR**: breaking format changes.
  - **MINOR**: new evidence categories or fields.
  - **PATCH**: corrections, reruns, or metadata updates.
- `pack_id` is immutable and unique per pack.
- Each artifact has a SHA-256 hash recorded in `manifest.json`.
- Source code and pipeline versions are captured in the manifest.

## Verification
Evidence packs are verified before release and during audit.

**Required verification steps:**
1. Generate `verification/checksums.sha256` from all files.
2. Verify all manifest hashes against the checksum file.
3. Sign `manifest.json` with an approved signing key.
4. Produce `verification/verification_report.md` with:
   - Summary of verification results
   - Tooling versions and timestamps
   - Signature validation output

### Example Verification Report Outline
```
# Verification Report

- Pack ID: EFD-EP-00042
- Version: 1.2.0
- Verification Date: 2025-10-08T13:10:00Z

## Checksums
- checksums.sha256: PASS
- manifest.json hashes: PASS

## Signatures
- manifest.sig: VALID
- signer: security@echo-aero.example

## Notes
- All artifacts present and accounted for.
```

## README (Human Summary)
**File:** `README.md`

Include:
- Pack purpose and scope
- Summary of test conditions
- Key findings (thrust ranges, noise peaks, thermal margins, fatigue life)
- Contact for questions
