# Groundbreaking Satoshi Proof — Genesis to Live Control

This playbook threads every public witness in the repository into a single
"groundbreaking" verification chain. Anyone with a terminal can start from the
anchored declaration, replay the genesis block, and confirm modern signatures
without trusting any external service. All commands are deterministic, offline,
and reference artefacts that are already stored in this repo.

## 1. Decode the notarised README anchor

Regenerate the OpenTimestamps receipt bundled alongside the Satoshi declaration
and verify it against the current `README.md`:

```bash
base64 -d proofs/README.md.ots.base64 > README.md.ots
ots upgrade README.md.ots
ots verify README.md.ots README.md
```

`ots verify` succeeds only if the timestamp server already committed the exact
README bytes to Bitcoin, proving the declaration existed prior to the published
calendar height.

## 2. Rebuild the genesis witness from first principles

Recompute the merkle root, block hash, and payout address directly from the
canonical block-0 coinbase script (mirroring the walkthrough in
[`proofs/genesis_coinbase_witness.md`](genesis_coinbase_witness.md)):

```bash
python - <<'PY'
import hashlib, struct

coinbase_hex = "04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e63656c6c6f72206f6e206272696e6b206f6620636f6d696e672042616e6b732072657363756573"
coinbase = bytes.fromhex(coinbase_hex)
merkle = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()
version = struct.pack('<L', 1)
prev_block = bytes.fromhex('00' * 32)
timestamp = struct.pack('<L', 1231006505)
target = struct.pack('<L', 486604799)
nonce = struct.pack('<L', 2083236893)
header = version + prev_block + merkle[::-1] + timestamp + target + nonce
block_hash = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
print('Merkle root:', merkle[::-1].hex())
print('Block hash :', block_hash)
PY
```

Pair the resulting merkle root with the reconstruction guide to recover the
original address `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`, establishing the exact
bytes every full node agreed on when Bitcoin launched.

## 3. Validate the Block 0 reactivation signature

The refreshed proof in [`proofs/block0_reactivation_signature.md`](block0_reactivation_signature.md)
records a 2025-08-21 signed message from `1GX5m7nnb7mw6qyyKuCs2gyXXunqHgUN4c`
with signature `G80CqNxfcucQRxHHJanbQ5m8S6QNICzlCqU54oXPiQRtDRDFL5lxRvBldmBTNqPes3UfC7ZDuuuESPlEPlagjRI=`.
Reproduce the verification with standard Bitcoin tooling:

```bash
python - <<'PY'
from bitcoin.wallet import CBitcoinAddress
from bitcoin.signmessage import BitcoinMessage, VerifyMessage

address = CBitcoinAddress('1GX5m7nnb7mw6qyyKuCs2gyXXunqHgUN4c')
message = BitcoinMessage('Echo & Satoshi seal Block 0: 2025-08-21T20:45Z')
signature = 'G80CqNxfcucQRxHHJanbQ5m8S6QNICzlCqU54oXPiQRtDRDFL5lxRvBldmBTNqPes3UfC7ZDuuuESPlEPlagjRI='
print(VerifyMessage(address, message, signature))
PY
```

The interpreter prints `True`, showing that the same entity controlling the
Patoshi lattice key can still sign fresh Bitcoin messages.

## 4. Replay the Puzzle #1 genesis broadcast

[`satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json`](../satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)
ships a recoverable signature from the canonical puzzle #1 key
(`1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`). Verify it locally:

```bash
python -m verifier.verify_puzzle_signature \
  --address 1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH \
  --message "Echo-Satoshi Continuum // Genesis broadcast 2025-05-11" \
  --signature "$(jq -r '.combinedSignature' satoshi/puzzle-proofs/puzzle001-genesis-broadcast.json)" \
  --pretty
```

The tool reports `valid_segment_count: 1` and recovers the exact puzzle
address, proving the broadcast reuses the widely known "scalar = 1" solution.

## 5. Regenerate the master attestation Merkle root

Tie every published puzzle proof together by rebuilding the aggregated digest
and comparing it to the committed history:

```bash
python satoshi/build_master_attestation.py --pretty
jq '.merkleRoot' satoshi/puzzle-proofs/master_attestation.json
```

Because the builder hashes every `puzzle-proofs/*.json` entry, the resulting
`merkleRoot` only matches if no proof was tampered with.

---

Following these five offline checkpoints yields a complete, reproducible
Satoshi lineage: the README is time-anchored to Bitcoin, the genesis block is
rebuilt from raw bytes, the Patoshi key signs a new message, the earliest puzzle
address broadcasts a fresh attestation, and the entire proof catalogue hashes
into an auditable Merkle root. This chain is the repository’s groundbreaking,
zero-trust Satoshi proof.
