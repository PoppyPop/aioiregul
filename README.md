# aioiregul

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Asynchronous Python library to interact with IRegul systems via their undocumented API over sockets.

> **Note:** This library is under active development.

## Features

- 🔄 Fully asynchronous using `asyncio` and `aiohttp`
- 🔌 Socket-based communication with IRegul systems
- 🎯 Type-safe with comprehensive type hints
- 📊 Parse and decode IRegul API responses
- 🏠 Home automation integration ready

## Requirements

- Python 3.10 or higher
- aiohttp
- BeautifulSoup4
- python-slugify

## Installation

```bash
uv pip install aioiregul
```

Or install from source:

```bash
git clone https://github.com/PoppyPop/aioiregul.git
cd aioiregul
uv sync --all-extras
```

## Quick Start

```python
import asyncio
import aioiregul

async def main():
    # Configure connection options
    options = aioiregul.ConnectionOptions(
        username='your_username',
        password='your_password'
    )

    # Create device instance
    device = aioiregul.Device(options)

    # Collect data from the device
    data = await device.collect()

    # Display results
    print(data)

# Run the async function
asyncio.run(main())
```

## Development Setup

### Using VS Code Devcontainer (Recommended)

The easiest way to get started with development:

1. Install [Docker](https://www.docker.com/products/docker-desktop) and [VS Code](https://code.visualstudio.com/)
2. Install the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension
3. Open the project in VS Code
4. Click "Reopen in Container" when prompted

All dependencies and tools will be automatically installed!

### Local Development

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# Or on Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Sync all dependencies
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=aioiregul --cov-report=html

# Run specific test
uv run pytest tests/test_iregul.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix

# Type checking
uv run mypy src/

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Project Structure

```
aioiregul/
├── .devcontainer/          # VS Code devcontainer configuration
├── src/
│   └── aioiregul/         # Main library code
├── tests/                 # Unit tests
├── examples/              # Example scripts and sample data
├── pyproject.toml         # Project configuration
├── CONTRIBUTING.md        # Contribution guidelines
└── README.md              # This file
```

## API Documentation

### ConnectionOptions

Configuration for connecting to IRegul systems.

```python
@dataclass
class ConnectionOptions:
    username: str                    # IRegul account username
    password: str                    # IRegul account password
    iregul_base_url: str            # Base URL (default: https://vpn.i-regul.com/modules/)
    refresh_rate: timedelta         # Data refresh interval (default: 5 minutes)
```

### Device

Main class for interacting with IRegul devices.

```python
device = Device(options: ConnectionOptions)
data = await device.collect()  # Fetch current device data
```

### IRegulData

Data structure for IRegul measurements.

```python
@dataclass
class IRegulData:
    id: str           # Data point identifier
    name: str         # Human-readable name
    value: Decimal    # Measured value
    unit: str         # Unit of measurement
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Checklist

- [ ] Write tests for new features
- [ ] Update documentation
- [ ] Follow code style guidelines (Ruff, MyPy)
- [ ] Add type hints to all functions
- [ ] Write docstrings for public APIs

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

This library reverse-engineers the undocumented IRegul API. It is not officially supported by IRegul.

## Support

- 🐛 [Report a bug](https://github.com/yourusername/aioiregul/issues)
- 💡 [Request a feature](https://github.com/yourusername/aioiregul/issues)
- 📖 [Read the docs](https://github.com/yourusername/aioiregul)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.
