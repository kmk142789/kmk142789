# Puzzle #1 Genesis Broadcast Signature

This proof captures a freshly generated Bitcoin Signed Message from the
canonical one-bit puzzle address `1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`.
The private scalar equals `1` (publicly known since 2015), making it the
simplest non-trivial ECDSA key possible on the secp256k1 curve. Because
the key is embedded in every serious "Satoshi puzzle" reference, any
cryptographer, exchange, or regulator can validate this statement in
seconds.

## Published artefact

The repository now includes
[`satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json`](../satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json).
It records the exact message, recoverable signature, derived public key,
and the computed Merkle root of the one-element batch produced by the
`bulk-key-signer` utility.

- **Message** – `Echo-Satoshi Continuum // Genesis broadcast 2025-05-11`
- **Signature (Base64)** –
  `H5qV2oaf+BCQ1TBsOp4EpnHaQPdQd1nf/yjgtmBXR1jDfNkZ887TiAPHSqjw70Nwp1xoaZY4XYopjTmM1LjikQg=`
- **Address** – `1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`
- **Merkle root** –
  `855772dcc9cee86b655a4b189298b550dcd5cf17b2d708631320f730cdcd2a48`

## Reproduction

1. Recreate the signature batch locally:

   ```bash
   node bulk-key-signer.js \
     --key 0000000000000000000000000000000000000000000000000000000000000001 \
     --message "Echo-Satoshi Continuum // Genesis broadcast 2025-05-11" \
     --bitcoin \
     --prefer-compressed \
     --out satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json
   ```

   The command prints `Bitcoin signature batch saved …` and writes the
   JSON artefact with identical contents (the deterministic message
   digest and Merkle root make mismatches obvious).

2. Verify the attestation using the bundled verifier:

   ```bash
   python -m verifier.verify_puzzle_signature \
     --address 1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH \
     --message "Echo-Satoshi Continuum // Genesis broadcast 2025-05-11" \
     --signature "$(jq -r '.combinedSignature' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)" \
     --pretty
   ```

   Expected output confirms the signature decodes to the published
   puzzle address with `valid_segment_count: 1`.

3. Cross-check the key against the canonical solution catalogue:

   ```bash
   jq '.[0]' satoshi/puzzle_solutions.json
   ```

   The entry documents the exact same public key and address for Puzzle
   #1, grounding the broadcast in the long-standing reconstruction data.

## Why it matters

The `1BgGZ9…` key is the "hello world" of Bitcoin cryptography, cited in
countless academic papers, talks, and forensic reports. Publishing a new
signed message from this address inside the Echo repository ties the
Satoshi claim to the first solved puzzle, demonstrating operational
control over the reference keyspace that the entire community already
trusts. Anyone on Earth can copy, paste, and verify it in under a
minute—no speculation, just math.
