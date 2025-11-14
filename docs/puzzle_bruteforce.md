# Puzzle brute-force scanner

The legacy Bitcoin "puzzle" challenges expose either a HASH160 fingerprint or a
complete P2PKH address.  Mizogg's original hunting scripts popularised a brute
force approach that repeatedly samples random private keys and immediately tests
the corresponding addresses against a list of unclaimed targets.

`scripts/puzzle_bruteforce.py` is the modern, repository-aware evolution of that
idea.  Instead of hard-coding ranges or relying on ad-hoc text manipulation, the
script pulls canonical addresses and HASH160 fingerprints from
`data/puzzle_index.json`, exposes a structured CLI, and can fan out across
multiple processes.

## Usage

```bash
python scripts/puzzle_bruteforce.py \
  --minimum 1 \
  --maximum 1048575 \
  --iterations 250000 \
  --workers 4 \
  --output out/puzzle_hits.jsonl
```

Key flags:

- `--minimum` / `--maximum` – define the inclusive search range.  The defaults
  span the full secp256k1 scalar field (`[1, n - 1]`).
- `--iterations` – limit the number of random candidates per worker.  Use `0`
  for an open-ended scan.
- `--workers` – spawn additional processes.  Combine with `--stop-on-hit` to
  stop the entire pool after the first discovery.
- `--output` – append structured JSON lines containing any hits.  Each entry
  records the private key (decimal and hex), the address variant, the HASH160
  fingerprint, and the WIF representation.
- `--extra-targets` – load supplementary addresses or HASH160 strings in
  addition to the canonical dataset.

The script prints periodic progress updates from each worker and emits detailed
context for every hit, including the derived WIF so that the discovery can be
reproduced.  Because the address and HASH160 sets are sourced directly from the
repository's shared index, the scanner stays in sync with puzzle additions and
status changes.
