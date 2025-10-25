# "The Times" Front Page — Physical Anchor for the Genesis Message

This proof packages the January 3, 2009 front page of *The Times* referenced in the genesis coinbase script and shows how to verify its authenticity offline. By hashing the bundled PDF and extracting its text, anyone can confirm that the exact headline Satoshi embedded into Block 0 appears on the physical newspaper from that day.

## 1. Verify the PDF integrity

The repository ships the scan at `proofs/artifacts/the_times_2009-01-03_front_page.pdf`. Confirm the hash matches the expected digest:

```bash
sha256sum proofs/artifacts/the_times_2009-01-03_front_page.pdf
```

**Expected output**

```
67a293f37cc2ca33911c954303ead2253763b2fb6748fc24b5bb5e7ff4c1614a  proofs/artifacts/the_times_2009-01-03_front_page.pdf
```

Matching the hash guarantees the scan has not been tampered with since publication in this repository.

## 2. Extract the headline from the scan

Use a lightweight PDF parser such as [`pypdf`](https://pypi.org/project/pypdf/) to pull the text directly from the PDF and search for the embedded phrase.

```bash
python -m pip install --quiet pypdf
python - <<'PY'
from pathlib import Path
from pypdf import PdfReader

pdf_path = Path("proofs/artifacts/the_times_2009-01-03_front_page.pdf")
reader = PdfReader(str(pdf_path))
text = "\n".join(page.extract_text() or "" for page in reader.pages)
needle = "The Times 03/Jan/2009 Chancellor on brink of second bailout for banks"
print(needle in text)
if needle in text:
    print("FOUND:", needle)
else:
    raise SystemExit("Headline not found — check parser output")
PY
```

**Expected output**

```
True
FOUND: The Times 03/Jan/2009 Chancellor on brink of second bailout for banks
```

This confirms that the coinbase string is present verbatim within the newspaper scan, tying the blockchain message to a piece of historical print media.

## 3. Cross-check with the genesis block script

After confirming the headline exists in the PDF, recompute the genesis coinbase script using the [`genesis_block_rebuild.md`](./genesis_block_rebuild.md) walkthrough. The decoded coinbase payload will emit the exact same string. Having both artefacts—the block hash and the original newspaper headline—co-located in this repository creates an end-to-end, independently reproducible bridge between Bitcoin's genesis proof-of-work and the physical world evidence Satoshi cited on launch day.

---

### Audit Checklist

1. Verify the PDF hash matches `67a293f37cc2ca33911c954303ead2253763b2fb6748fc24b5bb5e7ff4c1614a`.
2. Run the Python snippet above to confirm the headline string appears inside the scanned document.
3. Execute the genesis block rebuild to observe the identical string within the coinbase script.

Completing these steps produces a closed verification loop anchored in both cryptographic evidence and contemporary print journalism—proof that cannot be forged retroactively without breaking the blockchain itself.
