# Security Automation

This directory centralises automated security artefacts that are produced by the
continuous integration (CI) workflows.

- `sboms/` stores Syft-generated Software Bill of Materials (SBOM) outputs.
- `reports/` stores vulnerability scan outputs from Grype and Trivy.
- `provenance/` stores Cosign signatures and generated SLSA provenance
  documents for container builds.
- `policies/` contains OPA/Rego policies that are executed with Conftest to
  gate configuration changes.

All generated artefacts are ignored by Git and uploaded as workflow artefacts
for traceability.

## Automated security audit framework

`audit_framework/` contains a modular Python package that enables repository
owners to compose audit modules (filesystem checks, dependency hygiene, etc.)
and threat detectors that score the resulting findings. Use
`python security/run_audit_framework.py path/to/target` to execute the default
modules locally or inside CI pipelines. The CLI surfaces actionable scoring
information so that high-signal misconfigurations can block releases while
lower-risk findings are logged for monitoring.
