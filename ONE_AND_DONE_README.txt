# One-and-Done Heartbeat (HARMONIX)
Run this single command inside your repo folder (it will prompt for your keystore password):

python one_and_done_heartbeat.py

Environment overrides (optional):
- ECHO_KEYSTORE=echo.keystore.json
- ECHO_PASSWORD=...           (avoid if you can; safer to type when prompted)
- HARMONIX_SAMPLES=60
- HARMONIX_DURATION=600
- HARMONIX_CYCLES=2.0
- HARMONIX_AMPLITUDE=1.0
- HARMONIX_PHASE=0.0
- HARMONIX_OTS=1               (set 0 to skip OpenTimestamps)

Outputs:
- proofs/harmonix_heartbeat.jsonl    (signed series)
- proofs/harmonix_heartbeat.jsonl.ots (if OpenTimestamps available)
