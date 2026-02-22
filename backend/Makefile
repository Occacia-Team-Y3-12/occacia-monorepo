.PHONY: install lock update run test lint audit tools-upgrade clean-venv

install: lock
	poetry install --sync --no-root

lock:
	poetry lock

update:
	poetry update
	poetry lock

run:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest

lint:
	poetry run ruff check .

tools-upgrade:
	poetry run python -m pip install -U pip setuptools wheel

audit: install tools-upgrade
	poetry run pip-audit -l

clean-venv:
	rm -rf .venv
