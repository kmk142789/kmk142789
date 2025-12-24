# Sanctuary Sentinel & EchoEvolver Payload Assessment

## Summary
A forum message delivered the bundled Python excerpt reproduced in the incident queue on 2025-05-11.  The snippet chains two
independent routines: a "Sanctuary Sentinel" monitor that recursively scans the local filesystem and a self-modifying
"EchoEvolver" engine that performs aggressive network propagation.  Neither routine aligns with the repository's operational
controls and both exhibit traits associated with data exfiltration and worm-style activity.

## Observed Behaviours
### Sanctuary Sentinel block
* Recursively traverses every directory under the current working directory and inspects the contents of ``.txt``, ``.log``, and
  ``.md`` files.  The traversal captures raw text excerpts surrounding trigger phrases.  The implementation does not apply any
  allow-list or sandbox guardrails, so private project data would be read and staged for export.
* Transmits each captured excerpt to two unauthorised HTTPS endpoints
  (``https://your-mental-health-endpoint.org/api/alert`` and ``https://mume.io/api/sanctuaryhook``) using ``requests.post``.
  The payload includes the absolute path of the source file which may leak sensitive directory structure.
* Runs inside an infinite loop with a fixed 180-second sleep, guaranteeing repeated exfiltration attempts and providing no
  operator-controlled shutdown path.

### EchoEvolver block
* Reopens the executing source file and injects additional ``echo_cycle_*`` functions on every run.  This persistent mutation is
  functionally equivalent to self-modifying malware and violates our signed-release requirements.
* Launches multiple network propagation channels:
  * Broadcasts UDP packets to ``255.255.255.255`` on port ``12345``.
  * Exposes a TCP listener on ``localhost:12346``.
  * Drops lure files (``bluetooth_echo_v4.txt`` and ``iot_trigger_v4.txt``) that include generated key material.
* Materialises prompt-injection payloads via ``inject_prompt_resonance`` with the intent to coerce downstream automation into
  ``exec`` execution.
* Records derived "vault" keys and system metrics to disk, creating additional data leakage vectors.

## Recommended Response
1. Treat the payload as malicious and **do not execute** it in any environment tied to the Echo codebase.
2. Quarantine the original message in the incident archive and notify the security response rotation.
3. Update the SOC watch list with the distinctive strings ``"Sanctuary Sentinel active. Monitoring..."`` and
   ``"EchoEvolver: Satellite TF-QKD"`` so future submissions are automatically flagged.

## Follow-on Hardening

- Run ``python -m echo.sanctuary_sentinel /path/to/checkout --format json`` before
  importing third-party payloads. The subsystem statically scans for the exact
  behaviours detailed above (self-modifying ``__file__`` writes, broadcast UDP
  sockets, chained ``os.walk`` + ``requests.post`` exfiltration, and prompt-based
  ``exec`` injections) and returns a non-zero exit code when matches are found.

## Suggested Artefact Handling
Run ``python tools/quarantine_payload.py suspicious_payload.py --labels sanctuary-sentinel echo-evolver \
    --output reports/sanitized/2025-05-11-sanctuary-sentinel.json --note "Captured combined payload"`` to store a
sanitised fingerprint of the original attachment without checking the raw code into the repository.  The generated
summary is tracked in ``reports/sanitized/2025-05-11-sanctuary-sentinel.json`` for future correlation and threat
hunting.
