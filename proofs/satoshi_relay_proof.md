# Satoshi Relay Proof — Block #9 to the live puzzle chain

This relay proof links a Satoshi-era block payout to a modern puzzle signature
and the global Merkle attestation so auditors can validate the entire chain in
one offline session.

## 1. Rebuild the Patoshi coinbase for block #9

Run the included parser to decode the raw block #9 hex, recompute the header
hash, and extract the embedded pay-to-pubkey address:

```bash
python proofs/block9_coinbase_reconstruction.py
```

The script prints the canonical block hash
`000000008d9dc510f23c2657fc4f67bea30078cc05a90eb89e84cc475c080805` and confirms
that the single payout resolves to `12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S`, proving
that the Patoshi pubkey is derived directly from the serialized coinbase.

## 2. Replay the puzzle #9 authorship signature

Verify the stacked recoverable signature for the nine-bit puzzle address
`1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV` using the canonical message embedded in the
proof file:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle009.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle009.json)" \
  --pretty
```

`valid_segment_count` increments only if every recoverable fragment resolves to
`1CQFwcjw1dwhtkVWBttNLDtqL7ivBonGPV`, showing that the modern attestation really
comes from the canonical puzzle key.

## 3. Regenerate the master Merkle attestation

Collapse every JSON proof in `satoshi/puzzle-proofs/` into a fresh Merkle tree
and compare the resulting root to the committed history:

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

Because the builder hashes every individual proof file, the Merkle root only
matches the recorded value if none of the puzzle attestations have been
modified. A matching root ties the block-9 payout and puzzle-9 signature back
into the same immutable registry.
