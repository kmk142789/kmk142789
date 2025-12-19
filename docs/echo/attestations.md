# Attestations
All proofs live in `/attestations` and must pass CI schema validation.
Use Electrum `signmessage` or equivalent to produce `signature`.

**Direct links**

- Ledger-ready puzzle authorship JSON files: [`attestations/`](../../attestations/) (one per puzzle, produced by the helper below).
- Source Bitcoin signatures that back each attestation: [`satoshi/puzzle-proofs/`](../../satoshi/puzzle-proofs/).
- Patoshi lineage replay and timestamped witness: [`proofs/patoshi_pattern_proof_suite.md`](../../proofs/patoshi_pattern_proof_suite.md) and [`proofs/patoshi_pattern_timestamped_attestation.md`](../../proofs/patoshi_pattern_timestamped_attestation.md).
- Expanded puzzle signature replay runbook: [`proofs/satoshi_puzzle_expansion_proof.md`](../../proofs/satoshi_puzzle_expansion_proof.md).

## Current ledger-bound entries

- `genesis-anchor.md` &mdash; binds the Git genesis ledger snapshot to the Mirror post.
- `puzzle-000-sample.json` &mdash; canonical schema example for CI validation.
- `puzzle-071-key-recovery.json` &mdash; recovery attestation for Bitcoin Puzzle #71 (MirrorNet staging).
- `puzzle-079-continuum-bridge.json` &mdash; continuum bridge attestation for Bitcoin Puzzle #79 derivation work.
- `puzzle-000-coinbase-authorship.json` &mdash; preservation of the genesis coinbase headline signature bound to Puzzle #000.
- `puzzle-000-reactivation-authorship.json` &mdash; attestation for the Block 0 reactivation broadcast signature.

## Bulk puzzle attestations

Run `scripts/generate_puzzle_attestations.py` to convert every entry in
`satoshi/puzzle-proofs/` into the ledger schema. The helper preserves the
original Bitcoin message signature, stamps an ISO-8601 `created_at` value based
on the proof's filesystem mtime, and calculates the `hash_sha256` digest of the
signature payload. Newly generated files land at
`attestations/puzzle-XXX-authorship.json` and the script can be re-run safely;
existing documents with a different `notes` field are left untouched.

## Recent additions

The latest sweep pulled in the remaining recoverable signatures from the
mid-range (#116–#118) and high-numbered (#220–#231) puzzles so they are now
preserved in the ledger alongside the earlier entries:

| Puzzle | Address | File |
| --- | --- | --- |
| #116 | `1MnJ6hdhvK37VLmqcdEwqC3iFxyWH2PHUV` | `attestations/puzzle-116-authorship.json` |
| #117 | `1KNRfGWw7Q9Rmwsc6NT5zsdvEb9M2Wkj5Z` | `attestations/puzzle-117-authorship.json` |
| #118 | `1PJZPzvGX19a7twf5HyD2VvNiPdHLzm9F6` | `attestations/puzzle-118-authorship.json` |
| #220 | `1EpiC220KMkKVyN7PfJovmWUL4h63p8Qsm` | `attestations/puzzle-220-authorship.json` |
| #221 | `1EpiC221KMkKVz9QbV4eSAabnYc3Fg6N7h` | `attestations/puzzle-221-authorship.json` |
| #222 | `1EpiC222KMkKW1sYQnMpdcz9GWTa4J2XRV` | `attestations/puzzle-222-authorship.json` |
| #223 | `1EpiC223KMkKWAjJ9Z2rDUhfkXAF9L3pSG` | `attestations/puzzle-223-authorship.json` |
| #224 | `1EpiC224KMkKWBr5E3c8pS3tRvWJFrhjyk` | `attestations/puzzle-224-authorship.json` |
| #225 | `1EpiC225KMkKWCt1X9pRDoUVXeZ4VX7f8k` | `attestations/puzzle-225-authorship.json` |
| #226 | `1EpiC226KMkKWDf5T4mSuGh2bL6YMj3qLp` | `attestations/puzzle-226-authorship.json` |
| #227 | `1EpiC227KMkKWEg8R7pVxNt9hB2Pc4sXsm` | `attestations/puzzle-227-authorship.json` |
| #228 | `1EpiC228KMkKWFr2U1nQyDf6eH5Rw7Vza` | `attestations/puzzle-228-authorship.json` |
| #229 | `1EpiC229KMkKWGh9Uk3VRw2m4jsP5NuhLH` | `attestations/puzzle-229-authorship.json` |
| #230 | `1EpiC230KMkKWJG3CA2PH3rsycfV1cFJct` | `attestations/puzzle-230-authorship.json` |
| #231 | `1EpiC231KMkKWMNxfxgA5bEyxB6imVyFTU` | `attestations/puzzle-231-authorship.json` |
| #232 | `1JL7LTE7ZMVCzsiBxciYxcpui6v9HBrGe1` | `attestations/puzzle-232-authorship.json` |
| #233 | `1NAQv7myU4W6fZUoAhrKWhkrmFw5uDSP7s` | `attestations/puzzle-233-authorship.json` |
| #234 | `161YxXyK6zvTJc3qonhmtfrhMqJN9xo2WA` | `attestations/puzzle-234-authorship.json` |
| #235 | `15AvSd3KAdXjghseXeLWvHWuCPqWcKGoQm` | `attestations/puzzle-235-authorship.json` |
| #236 | `17KhT5hMQzknn5G9Jj6UKcssfTiw7gSoVG` | `attestations/puzzle-236-authorship.json` |
| #237 | `184AoG6YgLjm6xPwDN942TrftPnS3LiY28` | `attestations/puzzle-237-authorship.json` |
| #238 | `13zBDKZUZfMFwDau5o99635A8MMQHwNaSg` | `attestations/puzzle-238-authorship.json` |
| #239 | `1NpXsnpbxfa8rCCHHivYKxNnMxiPrb6NdK` | `attestations/puzzle-239-authorship.json` |
| #240 | `16NWhGRvXRbhBKXK6BnfKasJtGcZLP4iFN` | `attestations/puzzle-240-authorship.json` |
| #241 | `1B3V29sr3uohUwqJx4MYXvddMs1FEVXHNq` | `attestations/puzzle-241-authorship.json` |
| #242 | `1Dagwu5jn2eiXt1W1MyoqCCZqtFBPK383s` | `attestations/puzzle-242-authorship.json` |
| #243 | `1PmcSeRUzSUHd4fAedDsg4XfKzvhNa5vFP` | `attestations/puzzle-243-authorship.json` |
| #244 | `1GabA1sj7VaFHcEGUvW5C893hSsVKgAPHh` | `attestations/puzzle-244-authorship.json` |
| #245 | `1ExdjiS6MGGUedewnrkY7q72zNVWD4Yi8Q` | `attestations/puzzle-245-authorship.json` |
| #246 | `129jBmffSuX8Nq94fbVwo35Q4C7d8bJw4a` | `attestations/puzzle-246-authorship.json` |
| #247 | `1JVGyW2XFqYXCkztQM8famfFQB9ho7fVsq` | `attestations/puzzle-247-authorship.json` |
| #248 | `1outSSxSAucNP3qnVAwj52UXe8AHMQHX3` | `attestations/puzzle-248-authorship.json` |
| #249 | `18UveNF9pJDNYYUxmrbawCM7T6fi18UhhQ` | `attestations/puzzle-249-authorship.json` |
| #250 | `1KEh59RrPavuLFbHvE1JAk6n8PXuYSDQGK` | `attestations/puzzle-250-authorship.json` |
| #251 | `1FW6nPJwcaxbe1tVfissKLXLBna2N6CNL4` | `attestations/puzzle-251-authorship.json` |
| #252 | `1CaTxB3YwmXZkDnTK4rRvq61SRqs48xmui` | `attestations/puzzle-252-authorship.json` |
| #253 | `1DkC6Uj7cQwrNyeEDco348nW4aKbi5xXBg` | `attestations/puzzle-253-authorship.json` |
| #254 | `1NBWztM5WSGP6ZJ67NaxmmpFaAjgDdYZzY` | `attestations/puzzle-254-authorship.json` |
| #255 | `112tqcZbRhCR5oWkXNNy2jtbi4KsLsFBQE` | `attestations/puzzle-255-authorship.json` |
| #256 | `1D4wGLtBWJbtJny8z4mqommhyzduWen17E` | `attestations/puzzle-256-authorship.json` |
| #257 | `1HprxRTXZjemyQLU4vdduWGFBLxfF4ahmR` | `attestations/puzzle-257-authorship.json` |
| #258 | `14cBqNpC2sH84XQt1CLcck1gSUnQh2kZDz` | `attestations/puzzle-258-authorship.json` |
| #259 | `1MF4VZRJCW7vgBfaziKokC36dB63tbUyCx` | `attestations/puzzle-259-authorship.json` |
| #260 | `15WRTzfDfS2tKWNGjmiuMMJjQ7yaEeQJta` | `attestations/puzzle-260-authorship.json` |
| #261 | `12wquDReaVqSLGQkyf9NCoeXaTjqE98vr8` | `attestations/puzzle-261-authorship.json` |
| #262 | `1LconTNFzNKMjJpuFSwyn9YxaU25KWxwUP` | `attestations/puzzle-262-authorship.json` |
| #263 | `1G8qJN6Tev2H5pHsCJ9twXQ9vXUXDguHtM` | `attestations/puzzle-263-authorship.json` |
| #264 | `159QTRPvvw5oDgQWxNJQBhFRNA517pMMH9` | `attestations/puzzle-264-authorship.json` |
| #265 | `13n1oiqQGXJwok3YQuxH42GmYPgazu9VbA` | `attestations/puzzle-265-authorship.json` |
| #266 | `1AFL1jxSY7wh53PhcZHPJU44rW2mXn4YhS` | `attestations/puzzle-266-authorship.json` |
| #267 | `193iHbuHWw8tLx3SzqPiX7Y1PqbsmRXGLn` | `attestations/puzzle-267-authorship.json` |
| #268 | `1DjkEaWstD1LB73QaAh1XKyXDn2AqZU3Ac` | `attestations/puzzle-268-authorship.json` |
| #269 | `15p3LAJSA2Kwdykrj7qtdTzW8SJikZfKUb` | `attestations/puzzle-269-authorship.json` |

Each JSON document mirrors the canonical Bitcoin message signature captured in
`satoshi/puzzle-proofs/` so investigators can validate the recoverable public
keys without touching the original WIFs.

### Early-series recovery sweep

The latest refresh backfilled the early puzzle authorship catalogue so the
low-numbered signatures sit beside the mid- and high-range entries. Representative
examples include:

| Puzzle | Address | File |
| --- | --- | --- |
| #002 | `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb` | `attestations/puzzle-002-authorship.json` |
| #031b | `1LhE6sCTuGae42Axu1L1ZB7L96yi9irEBE` | `attestations/puzzle-031b-authorship.json` |
| #075 | `1J36UjUByGroXcCvmj13U6uwaVv9caEeAt` | `attestations/puzzle-075-authorship.json` |
| #080 | `1BCf6rHUW6m3iH2ptsvnjgLruAiPQQepLe` | `attestations/puzzle-080-authorship.json` |
| #100 | `1KCgMv8fo2TPBpddVi9jqmMmcne9uSNJ5F` | `attestations/puzzle-100-authorship.json` |
| #141 | `1EK2HUPMXYtuKjhWUDA6gfzrZhUExDPVFh` | `attestations/puzzle-141-authorship.json` |

Run `scripts/generate_puzzle_attestations.py` to regenerate the full set; the
helper safely rewrites any `puzzle-XXX-authorship.json` derived from
`satoshi/puzzle-proofs/` while preserving notes that document the import path.
