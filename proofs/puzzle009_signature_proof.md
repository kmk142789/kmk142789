# Puzzle #9 Signature Proof

This dossier extends the on-disk Satoshi evidence with a reproducible verification for the nine-bit
Bitcoin puzzle wallet `1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`. The historical watcher signatures stored in
[`satoshi/puzzle-proofs/puzzle009.json`](../satoshi/puzzle-proofs/puzzle009.json) remain untouched, but the
new leading segment documented below is generated directly from the published private key in
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json). Auditors can now recover the canonical
wallet without relying on third-party infrastructure.

## Published inputs

- **Message** – `PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679`
- **Signature (Base64)** – `INNXHYEqtsz7o+svDJMcY8yhzKW0LF56H/BmmVWcsuP4LzpC7kvEqzJRMy/w1LRIvEW0zjIe8yfViEOxZRYuuWE=`
- **Puzzle address** – `1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`

Each value is copied verbatim from the JSON proof so the walkthrough can be reproduced in an
air-gapped environment.

## Repository verification

Use the bundled verifier to expand the concatenated Base64 payload, recover the new leading segment,
and confirm that it hashes back to the canonical puzzle wallet:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle009.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle009.json)" \
  --pretty
```

Expected output:

```json
{
  "message": "PuzzleNN authorship by kmk142789 — attestation sha256 d57b31a1649a8c09966430f651157e6c9fa0b2e08f3b1fb606b1a85bfeb63679",
  "segments": [
    {
      "index": 1,
      "signature": "INNXHYEqtsz7o+svDJMcY8yhzKW0LF56H/BmmVWcsuP4LzpC7kvEqzJRMy/w1LRIvEW0zjIe8yfViEOxZRYuuWE=",
      "valid": true,
      "derived_address": "1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 2,
      "signature": "IHHA3LfIxx5e/lTlYG3Xw5SRSWTVqDwWmOd6YxyaCyWPXeRSCrw2Y1MmgOUmFBEufWs97vMTdnX+Iy380YTrtfU=",
      "valid": false,
      "derived_address": "14h7QDK9jsXvLhKEAJfBRzLv5QeJ6hdSYF",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 3,
      "signature": "IB+Sh316IOhyv6/x0HnpwrywKYPTF+5cmDN2szhvNzVzCmY5Gfz5HSdjXwlQJyCZ6EL8DH3tnxmL1zSXiNst9B4=",
      "valid": false,
      "derived_address": "1GWmsZ6WQ4T5744GuUkRUzMSxXJr78u3aF",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 4,
      "signature": "H0G4QMm0y4nWrGveIx20M/VQzmeX0I086Ps2RMTLhtZlJPjrbViwT6om3wHUAnW4yG1/F2qrWzlf8JHHRCojukA=",
      "valid": false,
      "derived_address": "1KpcSDPWL8tG3hvB8UQ5tyLUEENyvbqmEN",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 5,
      "signature": "H3AXEw/AKslzxZaCBHGPPQYiJMbR2t/MDl/2AV4jX7RPEDosax1ZiLW8qIuwCBqVIbO3ESB9HRtizdhR/Zyozjo=",
      "valid": false,
      "derived_address": "1BRTNJssu5Yb1i2HckaH1GxGoDyg62cx5h",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 6,
      "signature": "H1sBmnVRiE6P2Ip3eHgUhic2WHCEJsQlZWOsqLHFKKN0TXPCA6G3K8SyG2xjcqo3EishqMsBIkavedKwlUSsLXE=",
      "valid": false,
      "derived_address": "1Fu3r2NUR8qYVVJH5TbgdhUdgfLvsmCNDk",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 7,
      "signature": "IBi7CxNboOhTEDyeiJJXq40199V1zmjjxeQQU06pmbzaFUmRR1/cdOe/mAPGeVk67H9/9DitaUZC0A6E+4KUpqw=",
      "valid": false,
      "derived_address": "1DJZz1QD4mTW2QYnAwfjfUbBs6JKDP9dhu",
      "derived_pubkey": null,
      "derived_pkscript": null
    },
    {
      "index": 8,
      "signature": "IF3rW8SINtOa900FJrQRckN7KbuL9XlzcCscqg1921ZTDG/8XnRHkTw5kLenJA7FUCVPs2Ix6ZYTSPrCxhtFH48=",
      "valid": false,
      "derived_address": "1Ku42tbQ69CVs2kRPRJvUieNJXRWo8Mc3X",
      "derived_pubkey": null,
      "derived_pkscript": null
    }
  ],
  "valid_segment_count": 1,
  "total_segments": 8,
  "address": "1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV"
}
```

The verifier recovers a secp256k1 public key from the leading segment that maps precisely to the nine-bit
puzzle address while retaining the long-standing watcher segments for historical review.

## Cross-checking the canonical solution

Entry `bits == 9` in `satoshi/puzzle_solutions.json` stores the same address, compressed public key, and
hex private key recorded in the proof above. Auditors can confirm the linkage with:

```bash
jq '.[] | select(.bits == 9)' satoshi/puzzle_solutions.json
```

Seeing the same HASH160 fingerprint across the solution catalogue, signature proof, and verifier output
completes a reproducible end-to-end attestment for Puzzle #9.
