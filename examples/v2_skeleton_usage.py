"""Example: Fetch, persist, and reuse the v2 configuration skeleton.

This example demonstrates how to:
- Discover the configuration dictionary (keys-only) via a one-time 502 call
- Persist it to a JSON file
- Reuse the skeleton in the client constructor to issue faster 501 calls

Prerequisites:
1. Create a .env file with your device credentials:
   - IREGUL_DEVICE_ID
   - IREGUL_DEVICE_KEY
   - Optional: IREGUL_HOST, IREGUL_PORT
2. Ensure network connectivity to the IRegul server.

Usage:
  - Initialize and save a skeleton:
      uv run python examples/v2_skeleton_usage.py --init skeleton.json
  - Fetch data using a previously saved skeleton:
      uv run python examples/v2_skeleton_usage.py --update skeleton.json

"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from aioiregul.iregulapi import IRegulApiInterface
from aioiregul.v2 import IRegulClient


async def init_skeleton(path: str) -> dict[str, dict[int, dict[str, str]]] | None:
    """Fetch the configuration skeleton and save it to a JSON file.

    Args:
        path: Destination file path for the skeleton JSON.

    Returns:
        The configuration skeleton dictionary.

    Raises:
        TimeoutError: If the device does not respond in time.
        ConnectionError: If connection fails.
        ValueError: If response format is invalid.
    """
    client: IRegulApiInterface = IRegulClient()
    await client.get_data()

    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        json.dump(client.save_skeleton(), f, ensure_ascii=False, indent=2)

    print(f"✓ Skeleton saved to {dest}")
    return client.config_skeleton


async def update_with_skeleton(path: str) -> None:
    """Load a configuration skeleton and fetch data using the faster 501 command.

    Args:
        path: Path to the skeleton JSON file previously saved.

    Raises:
        FileNotFoundError: If the skeleton file does not exist.
        TimeoutError: If the device does not respond in time.
        ConnectionError: If connection fails.
        ValueError: If response format is invalid.
    """
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"Skeleton file not found: {src}")

    client: IRegulApiInterface = IRegulClient()

    with src.open("r", encoding="utf-8") as f:
        client.load_skeleton_from(f.read())

    data = await client.get_data()

    # Show a brief summary
    print("✓ Data fetched using provided skeleton (501)")
    print(f"Timestamp: {data.timestamp}")
    print(
        "Counts:",
        "zones=",
        len(data.zones),
        "inputs=",
        len(data.inputs),
        "outputs=",
        len(data.outputs),
        "measurements=",
        len(data.measurements),
        "parameters=",
        len(data.parameters),
        "labels=",
        len(data.labels),
        "analog_sensors=",
        len(data.analog_sensors),
        "modbus_registers=",
        len(data.modbus_registers),
    )

    # Display a couple of sample items for visual confirmation
    print("\nSample measurements (up to 3):")
    for m in list(data.measurements.values())[:3]:
        print(f"  - idx={m.index} valeur={m.valeur} unit={m.unit}")

    print("\nSample parameters (up to 3):")
    for p in list(data.parameters.values())[:3]:
        print(f"  - idx={p.index} nom={p.nom} valeur={p.valeur}")

    dest = Path("data-" + path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as f:
        f.write(data.as_json(indent=2))
    print(f"✓ Data saved to {dest}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for skeleton init/update operations."""
    parser = argparse.ArgumentParser(description="Fetch and reuse v2 config skeleton")
    parser.add_argument(
        "path", nargs="?", default="examples/skeleton.json", help="Skeleton JSON path"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--init", action="store_true", help="Fetch and save skeleton via 502")
    group.add_argument("--update", action="store_true", help="Use saved skeleton to fetch via 501")
    return parser.parse_args()


async def main() -> None:
    """Entry point: perform init or update based on CLI args."""
    args = parse_args()
    if args.init:
        await init_skeleton(args.path)
    elif args.update:
        await update_with_skeleton(args.path)


if __name__ == "__main__":
    asyncio.run(main())
