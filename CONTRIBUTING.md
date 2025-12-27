# Contributing to aioiregul

Thank you for your interest in contributing to aioiregul! This document provides guidelines and instructions for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git
- Docker (optional, for devcontainer)

### Getting Started

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/aioiregul.git
   cd aioiregul
   ```

2. **Choose your development environment**

   **Option A: Using VS Code Devcontainer (Recommended)**

   - Open the project in VS Code
   - Click "Reopen in Container" when prompted
   - All dependencies will be installed automatically

   **Option B: Local development**

   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
   # Or on Windows:
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

   # Sync all dependencies including dev extras
   uv sync --all-extras
   ```

3. **Install pre-commit hooks**
   ```bash
   uv run pre-commit install
   ```

## Development Workflow

### Code Style

This project uses modern Python tooling:

- **Ruff** - Fast linter and formatter
- **MyPy** - Static type checking
- **Pre-commit** - Automated checks before commits

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=aioiregul --cov-report=html

# Run specific test file
uv run pytest tests/test_iregul.py

# Run in parallel
uv run pytest -n auto
```

### Code Formatting and Linting

```bash
# Format code with Ruff
uv run ruff format .

# Lint and auto-fix issues
uv run ruff check . --fix

# Type checking with MyPy
uv run mypy src/
```

### Pre-commit Hooks

Pre-commit hooks will automatically run on every commit. To run manually:

```bash
# Run all hooks
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files
```

## Code Standards

### Python Style Guidelines

- Follow PEP 8 style guide
- Use type hints for all functions and methods
- Write docstrings following PEP 257 conventions
- Use `snake_case` for functions and variables
- Use `PascalCase` for class names
- Prefer modern Python syntax (Python 3.10+ features)

### Documentation

- Add docstrings to all public functions, classes, and modules
- Include parameter descriptions, return values, and exceptions
- Provide usage examples where applicable

Example:

```python
async def fetch_data(device_id: str, timeout: int = 30) -> dict[str, Any]:
    """
    Fetch data from an IRegul device.

    Args:
        device_id: The unique identifier of the device.
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing device data.

    Raises:
        DeviceNotFoundError: If the device doesn't exist.
        TimeoutError: If the request times out.

    Example:
        >>> data = await fetch_data("device123")
        >>> print(data["temperature"])
        22.5
    """
```

### Testing

- Write unit tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for test setup
- Test both success and error cases
- Use async tests for async code

### Asynchronous Code

This library is fully asynchronous:

- Use `async`/`await` keywords appropriately
- Avoid blocking operations
- Use `aiohttp` for HTTP requests
- Use `asyncio` for concurrent operations

## Submitting Changes

1. **Create a new branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**

   - Write code following the style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Ensure all tests pass**

   ```bash
   uv run pytest
   uv run mypy src/
   uv run ruff check .
   ```

4. **Commit your changes**

   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

   Pre-commit hooks will run automatically.

5. **Push to your fork and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Pull Request Guidelines

- Provide a clear description of the changes
- Link to any related issues
- Ensure all tests pass
- Update documentation if needed
- Keep commits focused and atomic
- Follow conventional commit messages

## Project Structure

```
aioiregul/
├── .devcontainer/          # VS Code devcontainer configuration
├── src/
│   └── aioiregul/         # Main package source code
│       ├── __init__.py
│       └── apiv2.py
├── tests/                 # Test files
├── examples/              # Example scripts and sample data
├── pyproject.toml         # Project configuration
├── README.md              # Project documentation
└── CONTRIBUTING.md        # This file
```

## Questions or Issues?

If you have questions or encounter issues:

- Check existing issues on GitHub
- Create a new issue with a clear description
- Include code examples and error messages if applicable

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
