.PHONY: akit

akit:
	python -m pytest -q
	python -m echo.akit.cli plan "CI validation cycle" --output artifacts/akit/ci-plan.json
	python -m echo.akit.cli --dry-run --cycles 1 --output artifacts/akit/ci-run.json
