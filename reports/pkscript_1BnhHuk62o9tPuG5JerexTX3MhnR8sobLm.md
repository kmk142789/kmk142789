# PKScript Analysis: 1BnhHuk62o9tPuG5JerexTX3MhnR8sobLm

## Summary
The record is a pay-to-public-key script from the original treasure puzzles. Replacing the hyphenated gap turns `1BnhHuk62-hnR8sobLm` into the full address `1BnhHuk62o9tPuG5JerexTX3MhnR8sobLm`.

```
1BnhHuk62-hnR8sobLm
Pkscript
04a48c81c934bd903ab347c7fb03d624c75305cf1e78e66c09f334e1617b52484ea130bceaae53ffd13804b5d188d4f590a469d1e878ad151e1f4fa6e07aeac505
OP_CHECKSIG
```

## Details
- **Public key:** `04a48c81c934bd903ab347c7fb03d624c75305cf1e78e66c09f334e1617b52484ea130bceaae53ffd13804b5d188d4f590a469d1e878ad151e1f4fa6e07aeac505`
- **Script hex:** `4104a48c81c934bd903ab347c7fb03d624c75305cf1e78e66c09f334e1617b52484ea130bceaae53ffd13804b5d188d4f590a469d1e878ad151e1f4fa6e07aeac505ac`
- **Derived P2PKH address:** Hashing the key and encoding yields `1BnhHuk62o9tPuG5JerexTX3MhnR8sobLm`.
- **Missing segment:** The suppressed substring is `o9tPuG5JerexTX3M`.

## Reproduction
The helper confirms the reconstruction:

```
python tools/pkscript_to_address.py <<'EOF'
1BnhHuk62-hnR8sobLm
Pkscript
04a48c81c934bd903ab347c7fb03d624c75305cf1e78e66c09f334e1617b52484ea130bceaae53ffd13804b5d188d4f590a469d1e878ad151e1f4fa6e07aeac505
OP_CHECKSIG
EOF
```

The output `1BnhHuk62o9tPuG5JerexTX3MhnR8sobLm` validates the restored address.
