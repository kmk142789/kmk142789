.PHONY: akit plan wish cycle test all lineage

akit:
	python -m pytest -q
	python -m echo.akit.cli plan "CI validation cycle" --output artifacts/akit/ci-plan.json
	python -m echo.akit.cli --dry-run --cycles 1 --output artifacts/akit/ci-run.json

cycle:
	python -m echo.echoctl cycle

plan:
	python -m echo.echoctl plan

wish:
	python -m echo.echoctl wish "$(W)" "$(D)" "$(C)"

test:
	pytest -q

all: test

lineage:
	python scripts/generate_lineage.py

FED_INJSON := build/index/federated_raw.json
FED_OUTJSON := build/index/federated_colossus_index.json
FED_OUTMD := docs/federated_colossus_index.md

.PHONY: federated-index
federated-index:
	@python scripts/generate_federated_colossus.py \
	  --in $(FED_INJSON) \
	  --json-out $(FED_OUTJSON) \
	  --md-out $(FED_OUTMD)

.PHONY: search
search:
	@python -m atlas.search --in $(FED_INJSON) --q "$(Q)" --dedupe-latest
