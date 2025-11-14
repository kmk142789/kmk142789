# Puzzle #3 Deterministic Solver Proof

This walkthrough publishes a reproducible path to the canonical Puzzle #3 key
material. The repository already ships a hand-rolled secp256k1 implementation in
[`packages/core/src/echo/tools/puzzle3_solver.py`](../packages/core/src/echo/tools/puzzle3_solver.py)
that derives the private key `7`, its compressed public key, the HASH160
fingerprint, and the final Base58Check P2PKH address
(`19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA`).【F:packages/core/src/echo/tools/puzzle3_solver.py†L1-L164】

## 1. Recompute the puzzle data locally

Run the solver directly to emit every field in a single pass:

```bash
python - <<'PY'
from echo.tools.puzzle3_solver import derive_puzzle3_solution
solution = derive_puzzle3_solution()
for key, value in solution.items():
    print(f"{key}: {value}")
PY
```

The snippet prints the decimal and hex private key (`7` / `07`), the compressed
public key (`025cbdf0646e5db4eaa398f365f2ea7a0e3d419b7e0330e39ce92bddedcac4f9bc`),
the HASH160 digest (`5dedfbf9ea599dd4e3ca6a80b333c472fd0b3f69`), and the legacy
P2PKH script plus address (`OP_DUP OP_HASH160 … OP_CHECKSIG` ->
`19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA`). Because the derivation code contains its
own elliptic-curve arithmetic, no external network calls or third-party
cryptography packages are required.【F:packages/core/src/echo/tools/puzzle3_solver.py†L3-L164】

## 2. Lock the derivation in regression tests

The dedicated unit test
[`tests/test_puzzle3_solver.py`](../tests/test_puzzle3_solver.py) asserts every
field produced by `derive_puzzle3_solution()`, guaranteeing that future edits
cannot silently change the private key, public key, HASH160, or payout
script.【F:tests/test_puzzle3_solver.py†L1-L18】 Re-run it with:

```bash
pytest tests/test_puzzle3_solver.py -k puzzle3
```

Pytest reports a single passing test, providing an automated checksum for the
entire derivation pipeline.

## 3. Cross-check the canonical puzzle catalogue

Entry `.[2]` inside
[`satoshi/puzzle_solutions.json`](../satoshi/puzzle_solutions.json) records the
official repository metadata for the three-bit puzzle: it lists the same public
key, HASH160 fingerprint, private key `7`, and payout address
`19ZewH8Kk1PDbSNdJ97FP4EiCjTRaZMZQA`.【F:satoshi/puzzle_solutions.json†L25-L34】
Inspect it locally:

```bash
jq '.[2]' satoshi/puzzle_solutions.json
```

Because the solver output, the regression test, and the canonical catalogue entry
all agree, researchers can regenerate Puzzle #3’s satoshi-era credentials within
seconds using nothing but the files already contained in this repository.
