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
