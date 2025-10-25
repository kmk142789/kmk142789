# Genesis Coinbase Proof — Immutable Headline, Immutable Hash

This note documents the most public and irreversible evidence of Satoshi’s
authorship: the Bitcoin genesis block (height 0, mined 2009‑01‑03). The block’s
coinbase script contains the famous headline — “The Times 03/Jan/2009 Chancellor
on brink of second bailout for banks” — and its header hash anchors every chain
of custody that followed. The data is burned into Bitcoin forever; anyone can
reproduce it locally in seconds.

## Step-by-step verification

1. **Run the bundled verifier (offline):**

   ```bash
   python tools/verify_genesis_coinbase.py
   ```

2. **Inspect the output:**

   ```text
   Bitcoin Genesis Block Verification
   ----------------------------------
   Block header hash: 000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
   Transaction ID:   4a5e1e4baab89f3a3251888bc31bc87f618f76673e2cc77ab2127b7afdeda33b
   Merkle root:      3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a

   Decoded coinbase headline:
     The Times 03/Jan/2009 Chancellor on brink of second bailout for banks
   ```

   * The block hash matches every Bitcoin node’s representation of block 0.
   * The decoded ASCII string is the original newspaper headline Satoshi
     embedded as proof-of-publication.
   * The transaction ID equals the Merkle root because the genesis block
     contains a single transaction; this mirrors the value serialized in the
     header.

3. **Cross-check anywhere:** paste the hash and transaction ID into any public
   blockchain explorer, or compare against your own node. Every honest replica
   must agree — otherwise the software (or the claimed blockchain) is not
   Bitcoin.

## Why this matters

* The coinbase headline is a notarized timestamp demonstrating awareness of the
  exact world event that coincided with Bitcoin’s birth. No other person can
  retroactively modify or replace it.
* The block header hash is the root of trust for every subsequent Bitcoin
  block. Matching it means you are reproducing Satoshi’s precise genesis work.
* The raw bytes are archived here verbatim. Anyone can verify without relying
  on third parties, aligning with the cryptographic self-sovereignty Satoshi
  demanded.

This repository preserves the full cryptographic handshake between 2009 and
today. Replaying the genesis block locally is the loudest proof in the world:
the chain still speaks with Satoshi’s voice.
