PYTHON ?= python3.11
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
REQUIREMENTS_HASH_FILE := requirements.lock.hash
TREE_HASH_FILE := tree.lock.hash

.PHONY: dev api test reproducible clean install migrate pytest

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	@if [ -f requirements.lock ]; then \
		$(PIP) install -r requirements.lock || true; \
	fi
	$(PIP) install -e .[dev]

install: $(VENV)

migrate:
	$(PY) -c "from vault.db import run_migrations; run_migrations()"

dev: install migrate

api: install
	$(PY) -m uvicorn vault.api.main:app --host 0.0.0.0 --port 8080

pytest:
	$(PY) -m pytest

test: install pytest

reproducible: install
	$(PY) - <<'PY2'
	from pathlib import Path
	from blake3 import blake3
	import subprocess

	req_hash_path = Path("$(REQUIREMENTS_HASH_FILE)")
	expected_req = req_hash_path.read_text().strip()
	actual_req = blake3(Path("requirements.lock").read_bytes()).hexdigest()
	if actual_req != expected_req:
	    raise SystemExit(f"requirements.lock hash mismatch: {actual_req} != {expected_req}")

	tree_expected = Path("$(TREE_HASH_FILE)").read_text().strip()
	cmd = "git ls-files | sort"
	files = subprocess.check_output(cmd, shell=True).decode().splitlines()
	hasher = blake3()
	for name in files:
	    if name.startswith(".git"):
	        continue
	    hasher.update(Path(name).read_bytes())
	actual_tree = hasher.hexdigest()
	if actual_tree != tree_expected:
	    raise SystemExit(f"tree hash mismatch: {actual_tree} != {tree_expected}")
	print("Reproducibility checks passed.")
	PY2
clean:
	rm -rf $(VENV)
