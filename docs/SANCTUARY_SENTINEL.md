# Sanctuary Sentinel Subsystem

Sanctuary Sentinel is Echo's defensive companion to the 2025-05-11 incident
report. Instead of running untrusted snippets, the subsystem statically scans a
checkout for the behaviours that defined the "Sanctuary Sentinel" /
"EchoEvolver" payload pair: self-modifying source mutations, broadcast socket
propagation, chained filesystem sweeps, and prompt-injection exec payloads.

## Capabilities

- **Signature-driven scanning** – Each rule captures a distinct behaviour,
  including UDP broadcast beacons, `open(__file__)` writes, inline `exec` class
  injection, and `os.walk` + `requests.post` exfiltration chains.
- **Deterministic reports** – Every run surfaces the files inspected, matches,
  contextual excerpts, and remediation guidance with deterministic sorting so CI
  diffs remain stable.
- **CLI + automation hooks** – The `python -m echo.sanctuary_sentinel` interface
  outputs either human-readable text or JSON and returns a non-zero exit status
  whenever a signature fires, making it safe for presubmit or supply-chain
  scanners.

## Usage

```bash
# Scan the current checkout and render a text summary
python -m echo.sanctuary_sentinel

# Emit JSON for CI uploads
python -m echo.sanctuary_sentinel /workspace/kmk142789 --format json \
    --max-file-bytes 524288 > out/sentinel.json
```

The JSON schema mirrors the dataclasses exposed via
`echo.sanctuary_sentinel.SentinelReport`, so downstream automation can reuse the
module directly without shelling out.

## Extending the ruleset

`SanctuarySentinel` accepts a custom `signatures` sequence, making it easy to add
new heuristics for emerging payloads. Construct a
`SentinelSignature(name, description, severity, recommendation, pattern=...)`
or pass `keywords_all=(...)` for multi-keyword detections.  The
`build_default_signatures()` helper provides the core rules derived from the
incident report.

Pair the subsystem with the existing `security/audit_framework` package to gate
untrusted contributions before they touch Echo's runtime lanes.
