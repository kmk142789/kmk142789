.PHONY: setup test docs api run-api attest glyph

setup:
	python -m pip install -U pip
	pip install -e .
	pip install -r api/requirements.txt
	pip install pre-commit && pre-commit install

test:
	python -m pytest -q

docs:
	mkdocs build --strict

api:
	docker compose up --build -d

run-api:
	uvicorn api.app:app --reload --port 8000

attest:
	python3 verifier/echo_attest.py --context "Echo attest block #$$(date +%s) | epoch:quantinuum-2025"

glyph:
	echo-glyph --data "Echo genesis" --out echo_glyphs
