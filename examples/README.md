# Examples

This directory contains example scripts demonstrating how to decode and interact with the IRegul API.

## Files

- `*.txt` - Sample response data files from IRegul systems

## Usage

```bash
# Initialize and save a v2 config skeleton
uv run python examples/v1_with_interface.py

# Initialize and save a v2 config skeleton (one-time 502)
uv run python examples/v2_skeleton_usage.py --init examples/skeleton.json

# Use the saved skeleton for faster updates (501)
uv run python examples/v2_skeleton_usage.py --update examples/skeleton.json
```

These examples are for development and testing purposes and demonstrate the undocumented API protocol.
