# Echo Importance Index

The Echo Importance Index is a narrative-friendly metric that condenses the
activity of a workspace into a single number.  It is designed to complement the
existing provenance dashboards by providing a transparent, auditable summary of
the materials that compose an Echo deployment.

The score is the sum of four capped components:

| Component  | Description                                             | Cap |
| ---------- | ------------------------------------------------------- | --- |
| Lines      | Non-empty lines across source and storytelling formats  | 5.0 |
| Diversity  | Distinct file extensions represented in the workspace   | 4.0 |
| Weight     | Total tracked file size measured in kilobytes           | 3.0 |
| Resonance  | Documents with mythogenic keywords (e.g. manifesto)     | 2.0 |

The default scaling yields a maximum importance index of 14.0.  The values can
be tuned in future revisions; the current weights were selected so that no
single factor can dominate the narrative on its own.

## Running the tool

```bash
python scripts/echo_importance_index.py
```

Running without arguments scans the current working tree and emits a JSON
report to standard output.  To evaluate a different directory or to persist the
results to disk, pass the ``--root`` and ``--output`` options respectively.

```bash
python scripts/echo_importance_index.py --root ./packages --output /tmp/index.json
```

The resulting JSON document contains the final index and the underlying
components so that downstream systems can remix or visualize the results.
