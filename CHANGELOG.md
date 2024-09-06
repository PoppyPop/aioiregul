# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Modern Python development setup with devcontainer support
- Comprehensive project structure following modern library standards
- Pre-commit hooks for code quality (Ruff, MyPy)
- Full type hints and strict type checking
- Comprehensive testing setup with pytest
- Documentation (README, CONTRIBUTING)
- Example scripts demonstrating API usage
- **uv package manager as the exclusive package manager**

### Changed

- Migrated to PEP 621 compliant `pyproject.toml`
- Reorganized project structure with proper src layout
- Moved example/debug scripts to `examples/` directory
- Updated dependencies to modern versions
- **Fully migrated to uv** - removed all pip backward compatibility
- Consolidated all configuration into `pyproject.toml`

### Removed

- Legacy `requirements.txt` and `requirements-dev.txt` files
- `setup.cfg` configuration file (replaced by `pyproject.toml`)
- `pytest.ini` (merged into `pyproject.toml`)
- All pip-based installation instructions

### Development

- Added VS Code devcontainer configuration with uv pre-installed
- Added Ruff for linting and formatting
- Added MyPy for static type checking
- Added pytest with async support
- Added coverage reporting
- Configured uv for fast dependency resolution and installation

## [0.1.0] - TBD

### Added

- Initial release
- Basic IRegul API connection support
- Asynchronous data collection from IRegul devices
- Socket-based communication
- Response parsing and data models

[unreleased]: https://github.com/yourusername/aioiregul/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/aioiregul/releases/tag/v0.1.0
