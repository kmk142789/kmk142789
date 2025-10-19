.PHONY: akit plan wish cycle test

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
