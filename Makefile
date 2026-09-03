.PHONY: install env test integration lint audit up hybrid down

install:
	python -m pip install -e ".[dev]"

env:
	python scripts/create_env.py

test:
	python -m pytest -m "not integration"

integration:
	python -m pytest -m integration --no-cov

lint:
	python -m ruff check .

audit:
	python -m pip check
	python -m pip_audit . --progress-spinner off

up:
	docker compose up --build

hybrid:
	docker compose --env-file .env.hybrid -f compose.hybrid.yaml up --build

down:
	docker compose down
