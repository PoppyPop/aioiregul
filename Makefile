# Makefile for aioiregul development

.PHONY: help sync install-dev test test-cov lint format type-check clean pre-commit rebase-master

help:
	@echo "Available commands:"
	@echo "  make sync         - Sync dependencies with uv"
	@echo "  make install-dev  - Install package with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linter (Ruff)"
	@echo "  make format       - Format code (Ruff)"
	@echo "  make type-check   - Run type checker (MyPy)"
	@echo "  make pre-commit   - Run all pre-commit hooks"
	@echo "  make rebase-master- Fetch and rebase current branch onto master"
	@echo "  make clean        - Clean up build artifacts"

sync:
	uv sync --all-extras

install-dev:
	uv sync --all-extras
	pre-commit install

test:
	uv run pytest

test-cov:
	uv run pytest --cov=aioiregul --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check . --fix

type-check:
	uv run pyright

pre-commit:
	uv run pre-commit run --all-files

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Fetch latest remote changes and rebase current branch onto origin/master
rebase-master:
	git fetch --all --prune
	git rebase origin/master
