.PHONY: install check lint format-check typecheck test fix clean

PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

install:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"
	@if git rev-parse --git-dir >/dev/null 2>&1; then $(BIN)/pre-commit install; \
	else echo "Not a git repo yet: skipping pre-commit hook install (re-run after git init)."; fi

# Same steps, same order as .github/workflows/ci.yml
check: lint format-check typecheck test

lint:
	$(BIN)/ruff check .

format-check:
	$(BIN)/ruff format --check .

typecheck:
	$(BIN)/mypy

test:
	$(BIN)/pytest

fix:
	$(BIN)/ruff check --fix .
	$(BIN)/ruff format .

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build
