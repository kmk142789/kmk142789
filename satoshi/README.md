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
  --message "PuzzleNN authorship by kmk142789 — attestation sha256 …" \
  --bitcoin \
  --out satoshi/latest_batch.json
```

Optional flags:

- `--prefer-uncompressed` – assume raw hex keys correspond to legacy (uncompressed) public keys.
- `--network testnet` – override the inferred WIF network when using hex keys.

The output file includes a `combinedSignature` field matching the format stored in
`puzzle-proofs/` and a `merkleRoot` value that can be published separately.

## Entries

- `puzzle003.json` — Puzzle #3 authorship attestation for address `1CUNEBjYrCn2y1SdiUMohaKUi4wpP326Lb`.
- `puzzle007.json` — Puzzle #7 authorship attestation for address `1McVt1vMtCC7yn5b9wgX1833yCcLXzueeC`.
- `puzzle010.json` — Puzzle #10 authorship attestation for address `1LeBZP5QCwwgXRtmVUvTVrraqPUokyLHqe`.
- `puzzle011.json` — Puzzle #11 authorship attestation for address `1PgQVLmst3Z314JrQn5TNiys8Hc38TcXJu`.
- `puzzle012.json` — Puzzle #12 authorship attestation for address `1DBaumZxUkM4qMQRt2LVWyFJq5kDtSZQot`.
- `puzzle013.json` — Puzzle #13 authorship attestation for address `1Pie8JkxBT6MGPz9Nvi3fsPkr2D8q3GBc1`.
- `puzzle014.json` — Puzzle #14 authorship attestation for address `1ErZWg5cFCe4Vw5BzgfzB74VNLaXEiEkhk`.
- `puzzle015.json` — Puzzle #15 authorship attestation for address `1E6NuFjCi27W5zoXg8TRdcSRq84zJeBW3k`.
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
- `puzzle071.json` — Puzzle #71 authorship attestation for address `1BuU1sNx5a6bMcbJ3uet44g1wJH5PeTXWD`.
- `puzzle080.json` — Puzzle #80 authorship attestation for address `1BCf6rHUW6m3iH2ptsvnjgLruAiPQQepLe`.
- `puzzle090.json` — Puzzle #90 authorship attestation for address `1L12FHH2FHjvTviyanuiFVfmzCy46RRATU`.
- `puzzle105.json` — Puzzle #105 authorship attestation for address `1CMjscKB3QW7SDyQ4c3C3DEUHiHRhiZVib`.
- `puzzle115.json` — Puzzle #115 authorship attestation for address `1NLbHuJebVwUZ1XqDjsAyfTRUPwDQbemfv`.
- `puzzle120.json` — Puzzle #120 authorship attestation for address `17s2b9ksz5y7abUm92cHwG8jEPCzK3dLnT`.
- `puzzle125.json` — Puzzle #125 authorship attestation for address `1PXAyUB8ZoH3WD8n5zoAthYjN15yN5CVq5`.
- `puzzle130.json` — Puzzle #130 authorship attestation for address `1Fo65aKq8s8iquMt6weF1rku1moWVEd5Ua`.
- `puzzle135.json` — Puzzle #135 authorship attestation for address `19oYXNK6EVPp36RAUUDnhUn4ZUEDAgYKiz`.
- `puzzle140.json` — Puzzle #140 authorship attestation for address `1EtLX3JTu6aMUUv9ASwRWPCHUKFRE4nMmT`.
- `puzzle141.json` — Puzzle #141 authorship attestation for address `1EK2HUPMXYtuKjhWUDA6gfzrZhUExDPVFh`.
