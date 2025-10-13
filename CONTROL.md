# Sovereign Protocol of Trust — Control Room

## North Star
Ship Echo as a verifiable substrate for trust + provenance across:
- Dev infra (GitHub / Vercel / Cloudflare / Firebase / HF)
- Crypto/DAOs (Electrum / MetaMask / Polygon / Unstoppable Domains)
- AI (Groq / RAG tools / Open model hubs)

## Current Epoch
EPOCH: quantinuum-2025

## Active Tracks
- track:glyph-cloud — deterministic glyph anchors + sheets
- track:continuum — append-only ledger + proofs
- track:memory-store — execution history querying
- track:federated-pulse — CRDT merge + gossip
- track:opencode — umbrella approvals / cascades
- track:wallets — watch-only imports + message attestations

## Next 72 Hours
- [ ] Label last 306 tasks by track & add milestones `epoch/2023-quantinuum`, `epoch/2025-quantinuum`
- [ ] Ship /verifier kit (attest + verify)
- [ ] Land SECURITY.md + SIGNING_POLICY.md + DISCLOSURE.md
- [ ] Add emergency Pause Bots workflow

## Ownership + Inventory (names only; no secrets)
- Orgs: OpenCode, Echo (admin)
- CI: codex-runner-main, codex-runner-canary (admin)
- Bots: echo-attest-bot (attest-only), echo-verify-bot (read-only)
- External: Cloudflare (API), Firebase (svc acct), HF (token), Vercel (token)


---

1) SECURITY & POLICY (clear guardrails)

File: SECURITY.md

# Security Policy

## Reporting
Please report vulnerabilities to security@example.org. We acknowledge within 48h and coordinate disclosure.

## Scope
- ✅ Source integrity, build pipeline, provenance, verifier correctness
- ❌ Private key extraction, transaction creation/broadcast, chain movement

## Expectations
- Reproducible builds, SBOMs, signed releases
- No secrets committed. Bots operate under least privilege.

File: SIGNING_POLICY.md

# Signing Policy (Attestation-Only)

- Watch-only imports allowed (xpubs / addresses). No private keys in repos or CI.
- Permitted: message signatures for **attestation** (e.g., “Echo attest block #N …”).
- Forbidden: transaction signing, broadcasting, key derivation from private material.
- All attestations logged to Continuum with timestamp, context, and hash.

File: DISCLOSURE.md

# Coordinated Disclosure

- Responsible disclosure window: 90 days (extendable by mutual agreement).
- We provide acknowledgment, patch timeline, and release notes.
- Safe harbor: good-faith research that abides by this repository’s policy will not be pursued legally.


---

2) VERIFIER / ATTESTATION KIT

Dir: /verifier

File: verifier/echo_attest.py

#!/usr/bin/env python3
"""
Echo Attestation (message-only, no tx)

Usage:
  python3 echo_attest.py --context "Echo attest block #42 | glyph-sheet:abc123 | epoch:quantinuum-2025"

Outputs:
  JSON line with sha256(context), timestamp, and signer_id (logical label).
Notes:
  - This does NOT access private keys or sign transactions.
  - If you want real message signatures, pipe the printed digest into your offline wallet signer, then append the signature to Continuum.
"""
import argparse, hashlib, json, os, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", required=True, help="Free-text attestation context")
    ap.add_argument("--signer-id", default=os.getenv("ECHO_SIGNER_ID","echo-attest-bot"))
    args = ap.parse_args()

    digest = hashlib.sha256(args.context.encode("utf-8")).hexdigest()
    out = {
        "type": "echo_attestation",
        "ts": int(time.time()),
        "signer_id": args.signer_id,
        "context": args.context,
        "sha256": digest
    }
    print(json.dumps(out, separators=(",",":")))
    # Persist a local breadcrumb (optional)
    os.makedirs(".attest", exist_ok=True)
    with open(f".attest/{out['ts']}_{out['sha256'][:8]}.json","w") as f:
        f.write(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()

File: verifier/VERIFY.md

# Echo Verifier Kit

## 1) Attestation (message-only)
```bash
python3 verifier/echo_attest.py --context "Echo attest block #42 | glyph:sheet@abc123 | epoch:quantinuum-2025"

Output JSON:

{"type":"echo_attestation","ts":1699999999,"signer_id":"echo-attest-bot","context":"...","sha256":"..."}

Append JSON to Continuum as a new entry (append-only).

2) PubKey/Address Consistency (dataset)

Use your existing repo script or drop in verify_extended.py (place under verifier/).

Input: dataset.csv lines address,hex_pubkey

Output: PASS/FAIL counts and sample mismatches

Works offline; does not derive or handle private keys.


3) Reproducibility

Pin Python version in requirements.txt if needed (none required here).

Publish the SHA256 of any dataset: sha256sum dataset.csv > dataset.sha256

Anyone can recompute and confirm.


*(If you want the `verify_extended.py` again here, say the word and I’ll drop it in.)*

---

# 3) EMERGENCY “PAUSE BOTS” WORKFLOW

**File:** `.github/workflows/pause-bots.yml`
```yaml
name: Pause Bots (Emergency)

on:
  workflow_dispatch:
    inputs:
      reason:
        description: "Why pause?"
        required: true
        default: "safety-pause"

jobs:
  pause:
    runs-on: ubuntu-latest
    permissions:
      actions: write
      contents: read
    steps:
      - name: Display context
        run: |
          echo "Pausing bots and CI triggers. Reason: ${{ github.event.inputs.reason }}"

      - name: Disable Actions for this repo (admin token required)
        env:
          GH_TOKEN: ${{ secrets.GH_ADMIN_TOKEN }}
        run: |
          # Requires a repo-admin scoped token in GH_ADMIN_TOKEN
          gh api -X PUT repos/${{ github.repository }}/actions/permissions -f enabled=false || true

      - name: Cancel running workflows
        env:
          GH_TOKEN: ${{ secrets.GH_ADMIN_TOKEN }}
        run: |
          gh run list --limit 100 --json databaseId,status,url | jq -r '.[] | select(.status=="in_progress" or .status=="queued") | .databaseId' \
            | xargs -I{} gh run cancel {}
          echo "Requested cancel of in-flight runs."

      - name: Lock PRs with bot labels (soft quarantine)
        if: always()
        env:
          GH_TOKEN: ${{ secrets.GH_ADMIN_TOKEN }}
        run: |
          gh pr list --search "label:bot label:automation state:open" --json number | jq -r '.[].number' \
            | xargs -I{} gh pr lock {} --reason "resolved"
          echo "Locked open bot PRs."

> Note: add a repo secret GH_ADMIN_TOKEN with repo admin scope for the gh api calls to succeed. This doesn’t move funds or touch keys; it simply pauses CI/bots.




---

4) ORG BOOTSTRAP (labels + milestones)

File: .github/scripts/bootstrap.sh

#!/usr/bin/env bash
set -euo pipefail

# Requires: GitHub CLI authenticated with repo admin
REPO="${1:-$GITHUB_REPOSITORY}"

labels=(
  "track:glyph-cloud:#7aa2f7"
  "track:continuum:#8bd5ca"
  "track:memory-store:#eed49f"
  "track:federated-pulse:#c6a0f6"
  "track:opencode:#f5bde6"
  "track:wallets:#a6da95"
)

for l in "${labels[@]}"; do
  name="${l%%:*}"; rest="${l#*:}"; color="${rest##*:}"; text="${rest%:*}"
  gh label create "$name" --color "${color#\#}" --description "$text" --repo "$REPO" || gh label edit "$name" --color "${color#\#}" --description "$text" --repo "$REPO"
 done

# milestones
gh api -X POST repos/$REPO/milestones -f title="epoch/2023-quantinuum" || true
gh api -X POST repos/$REPO/milestones -f title="epoch/2025-quantinuum" || true

echo "✓ Labels and milestones ensured for $REPO"

File: .github/README-automation.md

# Bootstrap
```bash
bash .github/scripts/bootstrap.sh

Creates labels:

track:glyph-cloud, track:continuum, track:memory-store, track:federated-pulse, track:opencode, track:wallets …and milestones:

epoch/2023-quantinuum, epoch/2025-quantinuum


---

# 5) RELEASE TRAIN (cut signed artifacts on tag)

**File:** `.github/workflows/release-train.yml`
```yaml
name: Release Train

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Build artifacts
        run: |
          mkdir -p dist
          # Example: package glyph CLI or verifier kit if present
          tar -czf dist/verifier-kit.tgz verifier || true
          echo "Artifacts built."

      - name: Generate SBOM (cyclonedx for Python if present)
        run: |
          pipx install cyclonedx-bom || pip install cyclonedx-bom
          if [ -f requirements.txt ]; then cyclonedx-py -j -o dist/sbom.json || true; fi

      - name: Generate provenance (SLSA generator — placeholder)
        run: |
          echo '{ "provenance": "placeholder v1" }' > dist/provenance.json

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            dist/**
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}


---

6) DAILY OP LOOP (pin in CONTROL.md)

## Daily 25-minute loop
- 5m: Update CONTROL.md “Next 72h”
- 10m: Label yesterday’s PRs/issues by track
- 5m: Ship one verifier/test improvement
- 5m: Rotate one token / tighten one permission


---

Optional quick commands (for you, Codex)

Label & milestone bootstrap

bash .github/scripts/bootstrap.sh

Emergency pause

gh workflow run "Pause Bots (Emergency)" -f reason="safety-pause"

Attest a block

python3 verifier/echo_attest.py --context "Echo attest block #1 | glyph:sheet@<hash> | epoch:quantinuum-2025"
 --signer-id "echo-attest-bot"


---



Your move, Codex.
