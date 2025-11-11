# Version Overview

## Current Release
- **Tag:** v0.1.0 (Release R1)
- **Package:** `echo-evolver` 0.1.0

## Installation Steps
1. Ensure Python 3.11 is available in your environment.
2. Upgrade packaging tools: `python -m pip install --upgrade pip`.
3. Install project dependencies and developer extras: `pip install -r requirements.txt` followed by `pip install -e .[dev]`.
4. (Optional) Install MkDocs material theme if you plan to generate documentation locally: `pip install mkdocs mkdocs-material`.

## Operational Commands
- Run the complete release validation pipeline: `make release-r1`.
- Execute the compliance Atlas job independently: `make compliance-job`.
- Generate static documentation site: `make docs-site`.
- Run focused identity layer e2e verification: `make e2e`.

Artifacts from these commands are written under `reports/`, including the Atlas compliance report and documentation site.
