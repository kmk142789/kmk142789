# README OpenTimestamps Proof

This guide demonstrates how to verify the OpenTimestamps proof shipped with this repository for the `README.md` manifesto. The
result anchors the exact Satoshi declaration in this repository to the Bitcoin timechain.

## Files

- `README.md` — the statement being notarized.
- `proofs/README.md.ots.base64` — the OpenTimestamps proof, stored as base64 so it survives any transport medium.

## Verification Steps

1. Decode the base64 proof into a binary `.ots` file:
   ```bash
   base64 -d proofs/README.md.ots.base64 > README.md.ots
   ```
2. Use the OpenTimestamps client to upgrade the proof and fetch the confirmed merkle path published on Bitcoin mainnet:
   ```bash
   ots upgrade README.md.ots
   ```
3. Verify the proof against the local `README.md` content:
   ```bash
   ots verify README.md.ots README.md
   ```
4. Inspect the attestation to see the exact Bitcoin transaction and block height anchoring the README:
   ```bash
   ots info README.md.ots
   ```

The `verify` command succeeds only when the README you possess matches the original content and when the Bitcoin commitments are
finalized. This provides an immutable, public timestamp proving the Satoshi declaration in `README.md` existed before the block
height referenced in the proof.

## Why This Matters

OpenTimestamps is a battle-tested standard used by Bitcoin Core releases and large archival projects. Because the proof upgrades
to a Bitcoin mainnet commitment, anyone in the world can reproduce the verification steps without trusting this repository or the
Echo infrastructure. Matching hashes confirm the README’s exact text, while the blockchain anchor delivers an irrefutable public
witness that the declaration was published at that time.
