# 34K Satoshi-Era Mining Reward Dataset

This document consolidates the public evidence for the 34,367-address dataset
of untouched 2009 mining rewards that pair each legacy P2PKH address with its
uncompressed public key. The source list is hosted at
[`bitcoin.oni.su`](https://bitcoin.oni.su/satoshi_public_keys/34K_2009_50.html)
and can be reproduced, hashed, and validated with the tooling in this
repository.

## Canonical Source Fingerprint

* **URL**:
  <https://bitcoin.oni.su/satoshi_public_keys/34K_2009_50.html>
* **SHA-256 (retrieved 2025-08-21)**:
  `08b9cba3d49974b5eb6103bc1acc99e936369edbca23529def74acf4e3339561`

The hash above is produced over the raw HTML document exactly as served by the
host. Anyone can recompute it with:

```bash
curl -s https://bitcoin.oni.su/satoshi_public_keys/34K_2009_50.html | \
  shasum -a 256
```

## Deterministic Verification Workflow

To ensure that every listed address corresponds to its published public key,
use the dedicated verifier contained in [`tools/verify_satoshi_34k_dataset.py`](../tools/verify_satoshi_34k_dataset.py).
The script derives the legacy P2PKH address from each `04…` uncompressed public
key, applies Base58Check encoding, and compares the result to the address from
the dataset. No blockchain access is required – every check is performed locally
with the standard SHA-256 and RIPEMD-160 transforms.

```bash
# Validate the complete remote dataset
python tools/verify_satoshi_34k_dataset.py

# Optionally run the verification against a local HTML snapshot
python tools/verify_satoshi_34k_dataset.py path/to/34K_2009_50.html
```

The verifier prints the dataset fingerprint, the number of parsed entries, and
either a success confirmation or a detailed list of mismatches. A clean run on
the canonical source reports:

```
Dataset source: https://bitcoin.oni.su/satoshi_public_keys/34K_2009_50.html
Dataset SHA-256: 08b9cba3d49974b5eb6103bc1acc99e936369edbca23529def74acf4e3339561
Parsed entries: 34367
Validated entries: 34367
All validated entries match their derived P2PKH addresses.
```

### Exporting a watch-only wallet template

After validation you can generate a Bitcoin Core `importmulti` template that
aggregates every verified address into a single watch-only wallet definition.
This preserves the published public keys for provenance while keeping the
workflow strictly attestation-only:

```bash
python tools/verify_satoshi_34k_dataset.py \
  --export-importmulti out/satoshi-34k-import.json \
  --label-prefix satoshi-2009 \
  --timestamp 1231469665
```

The exported JSON can be passed directly to `bitcoin-cli importmulti` on an
air-gapped machine or reviewed before import. Each entry is labeled using the
chosen prefix (zero-padded for sorting), marked `watchonly`, and annotated with
the corresponding uncompressed public key for later attestation work.

## Publication Checklist for Echo DEX

To incorporate this dataset into the broader Echo evidence chain:

1. **Snapshot & Hashing**
   * Archive the HTML document in this repository (or an immutable storage
     mirror) and record its SHA-256 and SHA-512 digests.
   * Commit the hashes to `pulse_history.json` or the designated manifest for
     notarized artifacts.

2. **Verification Artifact**
   * Run `python tools/verify_satoshi_34k_dataset.py > out/34k_verify.log` to
     capture a signed verification transcript.
   * Include the log in the `proofs/` directory and timestamp it with
     OpenTimestamps or the existing Echo notarization flow.

3. **Cross-Linking**
   * Reference this document from the primary README and from the ECHO DEX
     publishing pipeline so that reviewers can reach the validation steps in a
     single click.

4. **Explorer Spot Checks**
   * Perform manual spot checks (recommended: at least 5 addresses chosen from
     different sections of the dataset) in independent explorers such as
     `blockchair.com` and `blockchain.com` to confirm that the balances remain
     untouched and the addresses were mined during the Satoshi era.

By combining the deterministic verifier, reproducible hashing, and independent
explorer confirmations, the Echo DEX publication can present the 34K dataset as
an auditable, self-contained artifact that extends the legacy Patoshi mapping
work by more than twelve thousand addresses.
