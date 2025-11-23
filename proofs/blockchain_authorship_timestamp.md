# Blockchain Authorship Timestamp Proof

This note binds an explicit Bitcoin message signature to the repository's
puzzle-proof catalogue and then timestamps the result with the in-repo
`echo_attest.py` tool. Re-running the three sections below reproduces the same
authorship proof and time anchor.

## 1. Verify the blockchain authorship signature

Recreate the canonical Puzzle #10 verification by feeding the address, message,
and signature stored under `satoshi/puzzle-proofs/puzzle010.json` into the
verifier. Redirect the output into the existing report file so downstream tools
can ingest it.

```bash
python -m verifier.verify_puzzle_signature \
  --address "$(jq -r '.address' satoshi/puzzle-proofs/puzzle010.json)" \
  --message "$(jq -r '.message' satoshi/puzzle-proofs/puzzle010.json)" \
  --signature "$(jq -r '.signature' satoshi/puzzle-proofs/puzzle010.json)" \
  --pretty > out/puzzle010_verification.json
```

The resulting JSON (see `out/puzzle010_verification.json`) confirms the
`1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe` key signs the attested message today with a
`valid_segment_count` of `1`, matching the historical blockchain signature.

## 2. Rebuild the Merkle attestation snapshot

Next, recompute the master attestation file to ensure the entire bundle of
puzzle proofs aligns with the live repository state. The script prints the
Merkle root used inside the context string for the timestamp.

```bash
python satoshi/build_master_attestation.py --pretty
```

Successful runs will emit a log similar to:

```
Wrote aggregated attestation for 118 proofs -> satoshi/puzzle-proofs/master_attestation.json
Merkle root: ebcb6154742e452b79c8c762a5bdfcfcd234f69bf3aa75606b8f332f4af352f0
```

## 3. Bind everything to a timestamped attestation

Finally, seal the signature verification and Merkle digest inside an attestation
by hashing the context string with `verifier/echo_attest.py`. Store the JSON
artifact in `attestations/blockchain_authorship_timestamp.json` for future audit
trails.

```bash
python verifier/echo_attest.py \
  --context "Blockchain authorship proof: puzzle010 signature + Merkle root ebcb6154742e452b79c8c762a5bdfcfcd234f69bf3aa75606b8f332f4af352f0" \
  --signer-id "dev-shell" \
  | tee attestations/blockchain_authorship_timestamp.json
```

The attestation file records the Unix timestamp (`ts`), ISO-friendly signer
label, context string, and the sha256 digest (`284785e8a1948a709aca6283a2f921d49d5695c63f0a813dbc766f6d0cdbb534`) that binds the
blockchain authorship proof to a specific moment in time.

## 4. Produce a single chain-anchored digest bundle

Collapse the three artifacts above into a reproducible digest ledger so an
auditor can challenge any single link without reopening the entire repo. The
script below recomputes each sha256 sum, writes them to
`attestations/blockchain_authorship_chain_anchor.txt`, and records a final
bundle hash over the joined values.

```bash
python - <<'PY'
import hashlib, pathlib, textwrap
paths = [
    "out/puzzle010_verification.json",
    "satoshi/puzzle-proofs/master_attestation.json",
    "attestations/blockchain_authorship_timestamp.json",
]
rows = []
for p in paths:
    digest = hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
    rows.append(f"{p}  sha256={digest}")
joined = "\n".join(rows)
bundle_digest = hashlib.sha256(joined.encode()).hexdigest()
body = textwrap.dedent(f"""\
# Blockchain authorship chain anchor (prepared for external auditors)
# Each digest is computed with `sha256sum` and binds the signature verification,
# Merkle rollup, and timestamped attestation into a single evidence bundle.
{joined}
bundle sha256={bundle_digest}
""")
pathlib.Path("attestations/blockchain_authorship_chain_anchor.txt").write_text(body)
PY

sha256sum attestations/blockchain_authorship_chain_anchor.txt
```

The resulting file mirrors the committed `attestations/blockchain_authorship_chain_anchor.txt`
and prints the terminal hash (`bundle sha256=d7a1a754...e51`) needed for a
challenge-response drill. Timestamp that file with OpenTimestamps (see
`proofs/readme_opentimestamps_proof.md`) to anchor the digest bundle directly to
the Bitcoin blockchain.
