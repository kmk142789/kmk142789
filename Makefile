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

.PHONY: run up dash e2e

run:
	python -m atlas.core.runtime

up:
	docker compose -f deploy/docker-compose.yml up --build

dash:
	npm --prefix dashboard run dev

e2e:
	bash scripts/test_all.sh

lineage:
	python scripts/generate_lineage.py

FED_INJSON := build/index/federated_raw.json
FED_OUTJSON := build/index/federated_colossus_index.json
FED_OUTMD := docs/federated_colossus_index.md

.PHONY: federated-index
federated-index:
	@PYTHONPATH=. python scripts/generate_federated_colossus.py \
	  --in $(FED_INJSON) \
	  --json-out $(FED_OUTJSON) \
	  --md-out $(FED_OUTMD) \
	  --feed-out docs/feed/federated-colossus.xml

.PHONY: proof-pack
proof-pack:
	@PYTHONPATH=. python scripts/generate_federated_colossus.py \
	  --in $(FED_INJSON) \
	  --json-out $(FED_OUTJSON) \
	  --md-out $(FED_OUTMD) \
	  --feed-out docs/feed/federated-colossus.xml
	@echo "Proof pack written → $(FED_OUTMD) and $(FED_OUTJSON)"

.PHONY: search
search:
        @python -m atlas.search --in $(FED_INJSON) --q "$(Q)" --dedupe-latest

META_CAUSAL_PACKAGE := dist/meta_causal_engine/package.json

.PHONY: package-meta-causal-engine
package-meta-causal-engine:
        @PYTHONPATH=. python scripts/package_meta_causal_engine.py --output $(META_CAUSAL_PACKAGE)

.PHONY: deploy-meta-causal-engine
deploy-meta-causal-engine: package-meta-causal-engine
        @PYTHONPATH=. python -m echo_cli.main deploy meta-causal-engine --status enabled --channel production --max-parallel 3 --apply
