# uv - The Fast Python Package Manager

This project exclusively uses [uv](https://github.com/astral-sh/uv) as the package manager for faster dependency resolution and installation.

## Why uv?

- ⚡ **10-100x faster** than pip for dependency resolution
- 🔒 **Lockfile support** for reproducible builds
- 🎯 **Unified tool** - replaces pip, pip-tools, virtualenv, and more
- 🦀 **Written in Rust** for maximum performance
- 🚀 **Zero configuration** - works out of the box

## Installation

### Linux/Mac

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)

```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Quick Start

```bash
# Sync all dependencies (creates .venv automatically)
uv sync --all-extras

# Run commands in the virtual environment
uv run pytest
uv run ruff check .
uv run mypy src/

# Add a new dependency
uv add aiohttp

# Add a dev dependency
uv add --dev pytest

# Update dependencies
uv sync --upgrade
```

## Common Commands

| Task                     | Command                     |
| ------------------------ | --------------------------- |
| Install all dependencies | `uv sync --all-extras`      |
| Run tests                | `uv run pytest`             |
| Format code              | `uv run ruff format .`      |
| Lint code                | `uv run ruff check . --fix` |
| Type check               | `uv run mypy src/`          |
| Add dependency           | `uv add package-name`       |
| Add dev dependency       | `uv add --dev package-name` |
| Update lockfile          | `uv lock`                   |
| Update dependencies      | `uv sync --upgrade`         |

## Virtual Environment

uv automatically creates and manages a `.venv` directory. You can also activate it manually:

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

## More Information

- [uv Documentation](https://github.com/astral-sh/uv)
- [uv Guide](https://docs.astral.sh/uv/)
- [Migration from pip](https://docs.astral.sh/uv/pip/)
