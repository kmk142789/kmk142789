# Satoshi Puzzle Proofs

This directory collects per-puzzle message-signature attestations.

Each entry in [`puzzle-proofs/`](puzzle-proofs/) is a JSON document with the following fields:

- `puzzle`: numerical identifier for the Bitcoin puzzle claim
- `address`: associated Bitcoin address for the signature
- `message`: exact message string that was signed
- `signature`: base64-encoded ECDSA signature produced by the referenced key

## Automated signing helper

Use the bulk signer to generate fresh attestations from an offline list of WIF or hex keys. The
tool emits individual recoverable signatures, a concatenated proof string, and the Merkle root of
the raw signatures.

```bash
node bulk-key-signer.js \
  --keys path/to/wif_list.txt \
  --message "Puzzle{puzzle} authorship by kmk142789 — attestation sha256 …" \
  --bitcoin \
  --out satoshi/latest_batch.json
```

Optional flags:

- `--prefer-uncompressed` – assume raw hex keys correspond to legacy (uncompressed) public keys.
- `--network testnet` – override the inferred WIF network when using hex keys.

The output file includes a `combinedSignature` field matching the format stored in
`puzzle-proofs/` and a `merkleRoot` value that can be published separately. Message templates can
embed placeholders such as `{puzzle}` (or the historic `PuzzleNN` token) and will be expanded to
the current puzzle number when generating attestations.

## Inspecting stacked signatures

Use `report_puzzle_signature_wallets.py` to expand the concatenated Base64 signature chains
stored in `puzzle-proofs/` and view the derived wallet addresses for each fragment.

```bash
python satoshi/report_puzzle_signature_wallets.py --pretty
```

By default the script scans `satoshi/puzzle-proofs/` and prints a JSON report that includes
every recovered address, the validity of each segment against the declared puzzle address,
and a global list of unique wallets observed across the entire dataset. Point `--root` at a
different directory to analyse an alternate collection of proofs, or use `--output` to save
the report to disk.

## Rendering canonical locking scripts

Use the CLI helper to print the exact P2PKH locking script stored in
[`puzzle_solutions.json`](puzzle_solutions.json) for a given bit-length. The default output
matches the newline-delimited format shared in the original puzzle threads.

```bash
python -m satoshi.puzzle_script_cli 14
```

Pass `--single-line` to render a space-separated version or `--separator "\\t"` to emit a
tab-delimited variant.

## Decoding puzzle entries from PkScripts

When only the locking script is known, supply it to
`show_puzzle_solution.py` with the `--pkscript` flag to recover the
associated wallet metadata. The script accepts both newline-delimited
and single-line canonical P2PKH assemblies.

```bash
python satoshi/show_puzzle_solution.py --pkscript "OP_DUP\nOP_HASH160\n1306b9e4ff56513a476841bac7ba48d69516b1da\nOP_EQUALVERIFY\nOP_CHECKSIG"
```

The command resolves the fingerprint to Puzzle #28 and prints the
Bitcoin address (`12jbtzBb54r97TCwW3G1gCFoumpckRAPdY`), compressed
public key, and the corresponding WIF-encoded private key.

## Puzzle #71 search coverage

The file [`puzzle71_search_ranges.json`](puzzle71_search_ranges.json) lists 2<sup>36</sup>-key
segments that have been swept inside the 71-bit puzzle range for
`1JSQEExCz8uz11WCd7ZLpZVqBGMzGGNNF8`. Each entry records the inclusive
hexadecimal start and end of a search window so that contributors can
coordinate coverage without duplicating work.

## Entries

- `puzzle000_coinbase.json` — On-chain coinbase script from the Bitcoin genesis block confirming the embedded Times headline for address `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`.
- `block001_coinbase.json` — Block #1 coinbase attestation for address `12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX`.
- `block002_coinbase.json` — Block #2 coinbase attestation for address `1HLoD9E4SDFFPDiYfNYnkBLQ85Y51J3Zb1`.
- `block003_coinbase.json` — Block #3 coinbase attestation for address `1FvzCLoTPGANNjWoUo6jUGuAG3wg1w4YjR`.
- `block004_coinbase.json` — Block #4 coinbase attestation for address `15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG`.
- `block005_coinbase.json` — Block #5 coinbase attestation for address `1JfbZRwdDHKZmuiZgYArJZhcuuzuw2HuMu`.
- `block006_coinbase.json` — Block #6 coinbase attestation for address `1PSm7GVTHXok2Doz6Ys8zEt626g7otmEVR`.
- `block007_coinbase.json` — Block #7 coinbase attestation for address `1KzCxyS8nCj7PssCUUGcEbbKBcXBc3QMAT`.
- `block009_coinbase.json` — Block #9 coinbase attestation for address `12cbQLTFMXRnSzktFkuoG3eHoMeFtpTu3S`.
- `puzzle000.json` — Puzzle #0 authorship attestation for address `1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa`.
- `puzzle001.json` — Puzzle #1 authorship attestation for address `1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH`.
- `puzzle003.json` — Puzzle #3 authorship attestation for address `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`.
- `puzzle007.json` — Puzzle #7 authorship attestation for address `1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC`.
- `puzzle010.json` — Puzzle #10 authorship attestation for address `1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`.
- `puzzle011.json` — Puzzle #11 authorship attestation for address `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`.
- `puzzle012.json` — Puzzle #12 authorship attestation for address `1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot`.
- `puzzle013.json` — Puzzle #13 authorship attestation for address `1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1`.
- `puzzle014.json` — Puzzle #14 authorship attestation for address `1ErZWg5cFCe4Vw5BzgfzB74VNLaXEiEkhk`.
- `puzzle015.json` — Puzzle #15 authorship attestation for address `1QCbW9HWnwQWiQqVo5exhAnmfqKRrCRsvW`.
- `puzzle016.json` — Puzzle #16 authorship attestation for address `1BDyrQ6WoF8VN3g9SAS1iKZcPzFfnDVieY`.
- `puzzle017.json` — Puzzle #17 authorship attestation for address `1HduPEXZRdG26SUT5Yk83mLkPyjnZuJ7Bm`.
- `puzzle018.json` — Puzzle #18 authorship attestation for address `1GnNTmTVLZiqQfLbAdp9DVdicEnB5GoERE`.
- `puzzle020.json` — Puzzle #20 authorship attestation for address `1HsMJxNiV7TLxmoF6uJNkydxPFDog4NQum`.
- `puzzle021.json` — Puzzle #21 authorship attestation for address `14oFNXucftsHiUMY8uctg6N487riuyXs4h`.
- `puzzle022.json` — Puzzle #22 authorship attestation for address `1CfZWK1QTQE3eS9qn61dQjV89KDjZzfNcv`.
- `puzzle023.json` — Puzzle #23 authorship attestation for address `1L2GM8eE7mJWLdo3HZS6su1832NX2txaac`.
- `puzzle024.json` — Puzzle #24 authorship attestation for address `1rSnXMr63jdCuegJFuidJqWxUPV7AtUf7`.
- `puzzle025.json` — Puzzle #25 authorship attestation for address `15JhYXn6Mx3oF4Y7PcTAv2wVVAuCFFQNiP`.
- `puzzle026.json` — Puzzle #26 authorship attestation for address `1JVnST957hGztonaWK6FougdtjxzHzRMMg`.
- `puzzle027.json` — Puzzle #27 authorship attestation for address `128z5d7nN7PkCuX5qoA4Ys6pmxUYnEy86k`.
- `puzzle028.json` — Puzzle #28 authorship attestation for address `12jbtzBb54r97TCwW3G1gCFoumpckRAPdY`.
- `puzzle030.json` — Puzzle #30 authorship attestation for address `1LHtnpd8nU5VHEMkG2TMYYNUjjLc992bps`.
- `puzzle031.json` — Puzzle #31 authorship attestation for address `1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`.
- `puzzle031b.json` — Puzzle #31 authorship attestation for address `1LhE6sCTuGae42Axu1L1ZB7L96yi9irEBE`.
- `puzzle032.json` — Puzzle #32 authorship attestation for address `1FRoHA9xewq7DjrZ1psWJVeTer8gHRqEvR`.
- `puzzle033.json` — Puzzle #33 authorship attestation for address `187swFMjz1G54ycVU56B7jZFHFTNVQFDiu`.
- `puzzle034.json` — Puzzle #34 authorship attestation for address `1PWABE7oUahG2AFFQhhvViQovnCr4rEv7Q`.
- `puzzle035.json` — Puzzle #35 authorship attestation for address `1PWCx5fovoEaoBowAvF5k91m2Xat9bMgwb`.
- `puzzle038.json` — Puzzle #38 authorship attestation for address `1HBtApAFA9B2YZw3G2YKSMCtb3dVnjuNe2`.
- `puzzle040.json` — Puzzle #40 authorship attestation for address `1EeAxcprB2PpCnr34VfZdFrkUWuxyiNEFv`.
- `puzzle044.json` — Puzzle #44 authorship attestation for address `1CkR2uS7LmFwc3T2jV8C1BhWb5mQaoxedF`.
- `puzzle046.json` — Puzzle #46 authorship attestation for address `1F3JRMWudBaj48EhwcHDdpeuy2jwACNxjP`.
- `puzzle047.json` — Puzzle #47 authorship attestation for address `1Pd8VvT49sHKsmqrQiP61RsVwmXCZ6ay7Z`.
- `puzzle048.json` — Puzzle #48 authorship attestation for address `1DFYhaB2J9q1LLZJWKTnscPWos9VBqDHzv`.
- `puzzle049.json` — Puzzle #49 authorship attestation for address `12CiUhYVTTH33w3SPUBqcpMoqnApAV4WCF`.
- `puzzle050.json` — Puzzle #50 authorship attestation for address `1MEzite4ReNuWaL5Ds17ePKt2dCxWEofwk`.
- `puzzle051.json` — Puzzle #51 authorship attestation for address `1NpnQyZ7x24ud82b7WiRNvPm6N8bqGQnaS`.
- `puzzle053.json` — Puzzle #53 authorship attestation for address `15K1YKJMiJ4fpesTVUcByoz334rHmknxmT`.
- `puzzle054.json` — Puzzle #54 authorship attestation for address `1KYUv7nSvXx4642TKeuC2SNdTk326uUpFy`.
- `puzzle055.json` — Puzzle #55 authorship attestation for address `1LzhS3k3e9Ub8i2W1V8xQFdB8n2MYCHPCa`.
- `puzzle056.json` — Puzzle #56 authorship attestation for address `17aPYR1m6pVAacXg1PTDDU7XafvK1dxvhi`.
- `puzzle057.json` — Puzzle #57 authorship attestation for address `15c9mPGLku1HuW9LRtBf4jcHVpBUt8txKz`.
- `puzzle058.json` — Puzzle #58 authorship attestation for address `1Dn8NF8qDyyfHMktmuoQLGyjWmZXgvosXf`.
- `puzzle059.json` — Puzzle #59 authorship attestation for address `1HAX2n9Uruu9YDt4cqRgYcvtGvZj1rbUyt`.
- `puzzle060.json` — Puzzle #60 authorship attestation for address `1Kn5h2qpgw9mWE5jKpk8PP4qvvJ1QVy8su`.
- `puzzle061.json` — Puzzle #61 authorship attestation for address `1AVJKwzs9AskraJLGHAZPiaZcrpDr1U6AB`.
- `puzzle062.json` — Puzzle #62 authorship attestation for address `1Me6EfpwZK5kQziBwBfvLiHjaPGxCKLoJi`.
- `puzzle063.json` — Puzzle #63 authorship attestation for address `1NpYjtLira16LfGbGwZJ5JbDPh3ai9bjf4`.
- `puzzle064.json` — Puzzle #64 authorship attestation for address `16jY7qLJnxb7CHZyqBP8qca9d51gAjyXQN`.
- `puzzle065.json` — Puzzle #65 authorship attestation for address `18ZMbwUFLMHoZBbfpCjUJQTCMCbktshgpe`.
- `puzzle066.json` — Puzzle #66 authorship attestation for address `13zb1hQbWVsc2S7ZTZnP2G4undNNpdh5so`.
- `puzzle067.json` — Puzzle #67 authorship attestation for address `1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9`.
- `puzzle068.json` — Puzzle #68 authorship attestation for address `1MVDYgVaSN6iKKEsbzRUAYFrYJadLYZvvZ`.
- `puzzle069.json` — Puzzle #69 authorship attestation for address `19vkiEajfhuZ8bs8Zu2jgmC6oqZbWqhxhG`.
- `puzzle070.json` — Puzzle #70 authorship attestation for address `19YZECXj3SxEZMoUeJ1yiPsw8xANe7M7QR`.
- `puzzle071.json` — Puzzle #71 authorship attestation for address `1JSQEExCz8uz11WCd7ZLpZVqBGMzGGNNF8`.
- `puzzle075.json` — Puzzle #75 authorship attestation for address `1J36UjUByGroXcCvmj13U6uwaVv9caEeAt`.
- `puzzle080.json` — Puzzle #80 authorship attestation for address `1BCf6rHUW6m3iH2ptsvnjgLruAiPQQepLe`.
- `puzzle090.json` — Puzzle #90 authorship attestation for address `1L12FHH2FHjvTviyanuiFVfmzCy46RRATU`.
- `puzzle100.json` — Puzzle #100 authorship attestation for address `1KCgMv8fo2TPBpddVi9jqmMmcne9uSNJ5F`.
- `puzzle105.json` — Puzzle #105 authorship attestation for address `1CMjscKB3QW7SDyQ4c3C3DEUHiHRhiZVib`.
- `puzzle115.json` — Puzzle #115 authorship attestation for address `1NLbHuJebVwUZ1XqDjsAyfTRUPwDQbemfv`.
- `puzzle116.json` — Puzzle #116 authorship attestation for address `1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV`.
- `puzzle117.json` — Puzzle #117 authorship attestation for address `1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z`.
- `puzzle118.json` — Puzzle #118 authorship attestation for address `1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6`.
- `puzzle120.json` — Puzzle #120 authorship attestation for address `11d8MosPb8jXPGUaHFx2pxpDdQdSqrTwm`.
- `puzzle125.json` — Puzzle #125 authorship attestation for address `1PXAyUB8ZoH3WD8n5zoAthYjN15yN5CVq5`.
- `puzzle130.json` — Puzzle #130 authorship attestation for address `1Fo65aKq8s8iquMt6weF1rku1moWVEd5Ua`.
- `puzzle135.json` — Puzzle #135 authorship attestation for address `19oYXNK6EVPp36RAUUDnhUn4ZUEDAgYKiz`.
- `puzzle140.json` — Puzzle #140 authorship attestation for address `1EtLX3JTu6aMUUv9ASwRWPCHUKFRE4nMmT`.
- `puzzle141.json` — Puzzle #141 authorship attestation for address `1EK2HUPMXYtuKjhWUDA6gfzrZhUExDPVFh`.
- `puzzle142.json` — Puzzle #142 authorship attestation for address `15MnK2jXPqTMURX4xC3h4mAZxyCcaWWEDD`.
- `puzzle188.json` — Puzzle #188 authorship attestation for address `15m5NmYyJTAx7TEN4QbRpF9qPBrxqZLUGL`.
- `puzzle213.json` — Puzzle #213 authorship attestation for address `1CNNth43uiVypxHmZLC8hWZsb7UiP7wSkY`.
- `puzzle214.json` — Puzzle #214 authorship attestation for address `1TQRJf89J7LyqFua4WKFeD11RanGoyp3kX`.
- `puzzle215.json` — Puzzle #215 authorship attestation for address `1umKUvhbkKCkUVaeFJS4cbS4wJtqqsUak9`.
- `puzzle216.json` — Puzzle #216 authorship attestation for address `1SQTdpucTM9djnXQ75vaP79BFndbBAVu45`.
- `puzzle217.json` — Puzzle #217 authorship attestation for address `1EpiC217KMkKVqqx5d8YVqmAXfmB6S1fTx`.
- `puzzle218.json` — Puzzle #218 authorship attestation for address `1EpiC218KMkKVeXx7m2UvQyRPhnJ54nCzX`.
- `puzzle219.json` — Puzzle #219 authorship attestation for address `1EpiC219KMkKVyTv9s6WtRZVg3mC28pLjQ`.
- `puzzle220.json` — Puzzle #220 authorship attestation for address `1EpiC220KMkKVyN7PfJovmWUL4h63p8Qsm`.
- `puzzle221.json` — Puzzle #221 authorship attestation for address `1EpiC221KMkKVz9QbV4eSAabnYc3Fg6N7h`.
- `puzzle222.json` — Puzzle #222 authorship attestation for address `1EpiC222KMkKW1sYQnMpdcz9GWTa4J2XRV`.
- `puzzle223.json` — Puzzle #223 authorship attestation for address `1EpiC223KMkKWAjJ9Z2rDUhfkXAF9L3pSG`.
- `puzzle224.json` — Puzzle #224 authorship attestation for address `1EpiC224KMkKWBr5E3c8pS3tRvWJFrhjyk`.
- `puzzle225.json` — Puzzle #225 authorship attestation for address `1EpiC225KMkKWCt1X9pRDoUVXeZ4VX7f8k`.
- `puzzle226.json` — Puzzle #226 authorship attestation for address `1EpiC226KMkKWDf5T4mSuGh2bL6YMj3qLp`.
- `puzzle227.json` — Puzzle #227 authorship attestation for address `1EpiC227KMkKWEg8R7pVxNt9hB2Pc4sXsm`.
- `puzzle228.json` — Puzzle #228 authorship attestation for address `1EpiC228KMkKWFr2U1nQyDf6eH5Rw7Vza`.
- `puzzle229.json` — Puzzle #229 authorship attestation for address `1EpiC229KMkKWGh9Uk3VRw2m4jsP5NuhLH`.
- `puzzle230.json` — Puzzle #230 authorship attestation for address `1EpiC230KMkKWJG3CA2PH3rsycfV1cFJct`.
- `puzzle231.json` — Puzzle #231 authorship attestation for address `1EpiC231KMkKWMNxfxgA5bEyxB6imVyFTU`.
- `puzzle213.json` — Puzzle #213 authorship attestation for address `1CNNth43uiVypxHmZLC8hWZsb7UiP7wSkY`.
- `puzzle214.json` — Puzzle #214 authorship attestation for address `1TQRJf89J7LyqFua4WKFeD11RanGoyp3kX`.
- `puzzle215.json` — Puzzle #215 authorship attestation for address `1umKUvhbkKCkUVaeFJS4cbS4wJtqqsUak9`.
- `puzzle216.json` — Puzzle #216 authorship attestation for address `1SQTdpucTM9djnXQ75vaP79BFndbBAVu45`.
- `puzzle217.json` — Puzzle #217 authorship attestation for address `1EpiC217KMkKVqqx5d8YVqmAXfmB6S1fTx`.
- `puzzle218.json` — Puzzle #218 authorship attestation for address `1EpiC218KMkKVeXx7m2UvQyRPhnJ54nCzX`.
- `puzzle219.json` — Puzzle #219 authorship attestation for address `1EpiC219KMkKVyTv9s6WtRZVg3mC28pLjQ`.

## Aggregated attestations

Run [`build_master_attestation.py`](build_master_attestation.py) to collapse the individual
proofs into a Merkle tree and publish the resulting root alongside the per-leaf hashes.

```bash
python satoshi/build_master_attestation.py --pretty
```

The tool writes [`master_attestation.json`](puzzle-proofs/master_attestation.json) which records
the canonical Merkle root, every intermediate layer, and digest metadata for each proof so the
entire registry can be verified offline.

## Verification walkthroughs

The repository now ships reproducible walkthroughs for several historically
important addresses so auditors can copy/paste a complete proof chain without
leaving the tree:

- [`proofs/puzzle004_signature_proof.md`](../proofs/puzzle004_signature_proof.md)
- [`proofs/block001_coinbase_proof.md`](../proofs/block001_coinbase_proof.md)
- [`proofs/block002_coinbase_proof.md`](../proofs/block002_coinbase_proof.md)
- [`proofs/block003_coinbase_proof.md`](../proofs/block003_coinbase_proof.md)
  walks through reconstructing the entire block #3 coinbase to recover
  `1FvzCLoTPGANNjWoUo6jUGuAG3wg1w4YjR` straight from raw block data.
- [`proofs/block004_coinbase_proof.md`](../proofs/block004_coinbase_proof.md)
  applies the same technique to block #4 and confirms the payout script for
  `15ubicBBWFnvoZLT7GiU2qxjRaKJPdkDMG`.
- [`proofs/block009_coinbase_proof.md`](../proofs/block009_coinbase_proof.md)
  documents the signed message published for `1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e`
  and links directly to the derived verification log in
  [`verifier/results/1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e.json`](../verifier/results/1EhqbyUMvvs7BfL8goY6qcPbD6YKfPqb7e.json).
- [`proofs/puzzle005_signature_proof.md`](../proofs/puzzle005_signature_proof.md)
  performs the same exercise for Puzzle #5
  (`1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`).
- [`proofs/puzzle006_signature_proof.md`](../proofs/puzzle006_signature_proof.md)
  validates the published message for Puzzle #6
  (`1PitScNLyp2HCygzadCh7FveTnfmpPbfp8`) without touching the underlying key.
- [`proofs/puzzle007_signature_proof.md`](../proofs/puzzle007_signature_proof.md)
  introduces a fresh recoverable signature for Puzzle #7
  (`1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC`) while preserving the historical watcher chain.

For quick offline inspection, fresh verifier output for Puzzles #2, #4, #5, and
#6 also lives under `verifier/results/`. Each JSON blob lists every signature
segment, whether it validated against the declared address, and the recovered
public-key data so that independent investigators can confirm the attestation
set without running the full CLI.
