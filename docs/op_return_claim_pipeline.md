# OP_RETURN Claim Validation Pipeline

This guide documents the end-to-end tooling that now powers OP_RETURN claim
reviews.  The workflow converts raw transaction material into an actionable
report that highlights the claim status, issuing party, and next recommended
step for the operations team.

## 1. Parsing mined transactions

Use :func:`opreturn.claims.parse_claim_records` to ingest either raw
transaction hex (`hex`) or a decoded ``vout`` structure.  The parser extracts
any OP_RETURN outputs and emits structured records with:

- ``txid`` – transaction hash containing the OP_RETURN output.
- ``vout`` – output index associated with the payload.
- ``block_time`` – normalised to UTC (ISO-8601) for downstream comparisons.
- ``op_return_hex`` – original script payload preserved verbatim.
- ``op_return_text`` – human-readable rendering with common headers removed
  (``OP_RETURN:``, ``payload =>``, ``claim -`` etc.).

Example fixture: ``tests/data/opreturn/sample_transactions.json`` paired with
``tests/data/opreturn/expected_parsed_records.json`` exercises both raw-hex and
pre-decoded transaction inputs.  The dataset now ships with 1,200 transactions
generated via ``fixtures/opreturn/generate.py`` so downstream analytics can
stress-test pagination, batching, and reporting logic without bespoke setup.

## 2. 90-day inactivity window validation

:func:`opreturn.claims.validate_claim_windows` enriches parsed records with the
standard 90-day inactivity window rule.  Each entry receives:

- ``claim_status`` – ``valid`` when the deadline has not elapsed, otherwise
  ``expired``.
- ``reason`` – human-readable explanation including the remaining/elapsed days
  and the computed deadline.
- ``deadline`` – canonical ISO timestamp derived from ``block_time + 90 days``.

The validator accepts an ``as_of`` clock for deterministic testing.  Tests in
``tests/test_op_return_claims_pipeline.py`` cover boundary conditions at
``89``/``90``/``91`` days.

## 3. Issuer classification

Issuer detection happens automatically during validation.  The classifier scans
``op_return_text`` for common tags:

- ``Solomon bros`` → ``issuer_tag = "solomon_bros"`` (confidence ``0.9``)
- ``owner of wallet`` → ``issuer_tag = "self_attested_owner"``
- ``legal representative`` → ``issuer_tag = "legal_representative"``

Records that do not match a known marker fall back to ``issuer_tag =
"kmk142789"`` with a conservative confidence score.

## 4. Actionable report generation

Feed validated claims into :func:`opreturn.claims.write_actionable_report` to
emit both JSON and CSV artefacts.  Each output row includes:

``txid``, ``block_time``, ``op_return_text``, ``claim_status``, ``issuer_tag``,
``next_step_suggestion``.

``next_step_suggestion`` is derived from the status and issuer confidence:

- High-confidence valid claims → ``"evidence verified"``
- Valid claims lacking strong markers → ``"action (not expired)"``
- Expired claims → ``"escalate for allocation"``

The integration test ``test_write_actionable_report_generates_json_and_csv``
confirms the CSV schema and file emission.

## 5. Regression fixtures

Real-world OP_RETURN excerpts (sanitised) live in
``tests/data/opreturn/regression_transactions.json`` with the canonical output
stored in ``tests/data/opreturn/expected_regression_validated.json``.  These
fixtures shield the pipeline against regressions in decoding, classification,
or reporting logic.  ``test_regression_fixture_remains_stable`` executes the
full parse → validate → report chain and ensures the JSON artefact stays
stable.

## 6. Running the CLI

A lightweight CLI is bundled for analysts.  Point it at a JSON payload of
transactions (list or single object) and request JSON/CSV outputs:

```bash
python -m opreturn tests/data/opreturn/sample_transactions.json \
  --json-output /tmp/opreturn-report.json \
  --csv-output /tmp/opreturn-report.csv
```

Example JSON output (truncated for brevity):

```json
[
  {
    "txid": "1111…",
    "op_return_text": "Claim from Solomon bros // owner of wallet",
    "claim_status": "valid",
    "issuer_tag": "solomon_bros",
    "next_step_suggestion": "evidence verified"
  }
]
```

## 7. Running the tests

Execute the focused test suite to validate the entire pipeline:

```bash
pytest tests/test_op_return_claims_pipeline.py tests/test_op_return_reporting.py
```

The existing ``tests/test_op_return_reporting.py`` coverage continues to ensure
the historical reporting helpers operate as expected alongside the new parser
and validator stack.
