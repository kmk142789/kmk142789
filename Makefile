.PHONY: akit plan wish cycle test all lineage bootstrap expand serve verify pack

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

# Colossus convenience targets -------------------------------------------------

bootstrap:
	python scripts/colossus_make.py bootstrap

expand:
	@echo "Colossus expand orchestrator will arrive in a future PR."

serve:
	@echo "Colossus explorer will arrive in a future PR."

verify:
	@echo "Colossus verification suite will arrive in a future PR."

pack:
	@echo "Colossus release pack tooling will arrive in a future PR."
