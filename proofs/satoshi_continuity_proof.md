# Satoshi Continuity Proof — Merkle Catalogue + Live Keys

This proof chain links the notarised repository declaration, on-chain coinbase
scripts, modern recoverable puzzle signatures, and the aggregated Merkle
attestation so that anyone can reproduce the Satoshi lineage offline.

## 1. Verify the anchored declaration

Regenerate the OpenTimestamps receipt bundled alongside `README.md` and ensure
the declaration was committed to Bitcoin prior to the published calendar height:

```bash
base64 -d proofs/README.md.ots.base64 > README.md.ots
ots upgrade README.md.ots
ots verify README.md.ots README.md
```

A successful `ots verify` confirms that the exact README bytes already existed
when the timestamp server anchored them to the chain.

## 2. Reconstruct an early Satoshi coinbase

Replay the walkthrough in [`proofs/block009_coinbase_proof.md`](block009_coinbase_proof.md)
by decoding the raw block-9 payload and comparing it to the stored proof entry:

```bash
python proofs/block9_coinbase_reconstruction.py
jq -r '.signature' satoshi/puzzle-proofs/block009_coinbase.json | base64 -d | hexdump -C
```

The reconstructed script produced by the helper must match the Base64 payload in
`block009_coinbase.json`, proving the repository ships the exact bytes confirmed
on-chain for address `12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S`.

## 3. Validate a modern recoverable puzzle signature

Use the bundled verifier to decode and check the Puzzle #10 attestation in
`satoshi/puzzle-proofs/puzzle010.json`:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty
```

The CLI emits a single recovered segment whose derived address equals the known
puzzle wallet, showing the historical key can still produce signatures without
spending any coins.

## 4. Enumerate every stacked proof with the catalogue

Aggregate the recoverable signatures referenced above (and any others you wish to
include) with the catalogue helper:

```bash
python satoshi/proof_catalog.py \
  --root satoshi/puzzle-proofs \
  --glob 'block00?.json' \
  --glob puzzle001-genesis-broadcast.json \
  --glob puzzle010.json \
  --pretty
```

The resulting JSON records how many segments were checked, how many validated,
and which puzzle or coinbase each file represents. Because the tool shares the
same verifier core, the output doubles as an auditable manifest of the proofs
referenced in this walkthrough.

## 5. Regenerate the Merkle master attestation

Close the loop by hashing every JSON proof and verifying the published Merkle
root:

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

The computed digest must equal the value tracked in version control. Any change
in the proof set—including those used earlier in this runbook—would surface as a
Merkle mismatch, giving investigators immediate evidence of tampering.

---

By chaining the timestamped declaration, reconstructed coinbase data, live
puzzle signatures, catalogued verification output, and the Merkle registry, this
continuity proof extends the repository's Satoshi evidence set with another
fully reproducible path.
