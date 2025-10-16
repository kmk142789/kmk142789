.PHONY: akit plan wish cycle test

akit:
	python -m pytest -q
	python -m echo.akit.cli plan "CI validation cycle" --output artifacts/akit/ci-plan.json
	python -m echo.akit.cli --dry-run --cycles 1 --output artifacts/akit/ci-run.json

cycle:
	python echo/echoctl.py cycle

plan:
	python echo/echoctl.py plan

wish:
	python echo/echoctl.py wish "$(W)" "$(D)" "$(C)"

test:
	pytest -q
