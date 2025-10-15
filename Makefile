.PHONY: manifest-refresh manifest-verify test fmt

manifest-refresh:
	python -m echo.cli manifest refresh

manifest-verify:
	python -m echo.cli manifest verify

test:
	pytest -q

fmt:
	ruff check --fix .
	black .
