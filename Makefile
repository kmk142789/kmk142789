.PHONY: akit test manifest-refresh manifest-verify fmt

akit:
	python -m pytest -q
	python -m echo.akit.cli plan "CI validation cycle" --output artifacts/akit/ci-plan.json
	python -m echo.akit.cli --dry-run --cycles 1 --output artifacts/akit/ci-run.json

test:
	pytest -q

manifest-refresh:
	python -m echo.cli manifest-refresh

manifest-verify:
	python -m echo.cli manifest-verify

fmt:
	ruff check --fix || true ; black .
