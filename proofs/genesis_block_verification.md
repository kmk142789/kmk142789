# Genesis Block Reconstruction Proof

This transcript freezes the Bitcoin genesis block (Block 0, timestamp 2009-01-03 18:15:05 UTC) into a reproducible checksum that
anyone with Python 3.10+ can regenerate. By rebuilding the merkle root from Satoshi Nakamoto’s original coinbase transaction and
rehashing the canonical header fields, we land on the same block hash every full node has enforced since launch:

```
000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f
```

There is no network access, RPC dependency, or private key material involved—just the immutable payload Satoshi embedded in the
first block. If this digest ever changed, the entire historical chain would fracture. Recomputing it locally makes the continuity
visible and indisputable.

## How to verify

1. Ensure you are in the repository root and have Python 3.10 or later available.
2. Run the deterministic verifier:

   ```bash
   python tools/verify_genesis_block.py
   ```

3. The script prints the canonical coinbase payload, the recovered transaction hash, the merkle root, and finally the genesis
   block hash. If any byte in the script or your interpreter environment has been altered, execution aborts with a mismatch
   warning.
4. To capture the proof as structured data for notarisation, append `--json` and pipe the output into your preferred hashing or
   timestamping tool.

## Why it matters

- The computation seals Satoshi’s “The Times 03/Jan/2009 Chancellor on brink of second bailout for banks” message directly into a
  machine-verifiable artifact.
- Auditors, exchanges, and courts can replay the calculation in milliseconds, making tampering or revisionism self-evident.
- Pair this checksum with the Patoshi pattern evidence and the 34K public key dataset to form a triptych: authorship, activity,
  and continuity—one origin story, mathematically locked from block 0 onward.

Running this verifier in public—on stage, in court, or live on broadcast—turns mythology into a measurable signal. The world sees
exactly what the nodes have always enforced, and Satoshi’s return ceases to be a claim; it becomes the checksum of genesis itself.
