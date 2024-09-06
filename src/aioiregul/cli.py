#!/usr/bin/env python3
"""CLI tool to decode IRegul protocol frames from files.

Usage:
    python -m aioiregul.cli examples/501-NEW.txt
    python -m aioiregul.cli examples/502-OLD.txt --mapped
    python -m aioiregul.cli examples/501-NEW.txt --json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any


def _serialize_value(value: Any) -> Any:
    """Convert value to JSON-serializable format."""
    from datetime import datetime

    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (int | float | str | bool | type(None))):
        return value
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_serialize_value(v) for v in value]
    # Dataclass or object with __dict__
    if hasattr(value, "__dict__"):
        return {k: _serialize_value(v) for k, v in value.__dict__.items()}
    return str(value)


async def decode_command(args: argparse.Namespace) -> int:
    """Execute the decode command.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    from .decoder import decode_file
    from .mappers import map_frame

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    try:
        frame = await decode_file(str(file_path))
    except Exception as e:
        print(f"Error decoding file: {e}", file=sys.stderr)
        return 1

    if args.mapped:
        # Map to typed dataclasses
        mapped = map_frame(frame)
        data = _serialize_value(mapped)
    else:
        # Raw decoded frame
        data = _serialize_value(frame)

    if args.json:
        # JSON output
        print(json.dumps(data, indent=2))
    else:
        # Human-readable summary
        print(f"File: {file_path}")
        print(f"Type: {'OLD' if frame.is_old else 'NEW'}")
        print(f"Timestamp: {frame.timestamp}")
        print(f"Token Count: {frame.count}")
        print(f"\nGroups found: {', '.join(sorted(frame.groups.keys()))}")

        if args.mapped:
            mapped = map_frame(frame)
            print("\nMapped Data Summary:")
            print(f"  Zones: {len(mapped.zones)}")
            print(f"  Inputs: {len(mapped.inputs)}")
            print(f"  Outputs: {len(mapped.outputs)}")
            print(f"  Measurements: {len(mapped.measurements)}")
            print(f"  Parameters: {len(mapped.parameters)}")
            print(f"  Labels: {len(mapped.labels)}")
            print(f"  Modbus Registers: {len(mapped.modbus_registers)}")
            print(f"  Analog Sensors: {len(mapped.analog_sensors)}")
            print(f"  Configuration: {'Yes' if mapped.configuration else 'No'}")
            print(f"  Memory: {'Yes' if mapped.memory else 'No'}")

            # Show sample zones
            if mapped.zones:
                print("\nSample Zones (first 3):")
                for zone in mapped.zones[:3]:
                    print(
                        f"  Zone {zone.index} ({zone.zone_nom}): "
                        f"normal={zone.consigne_normal}°, "
                        f"reduit={zone.consigne_reduit}°, "
                        f"mode={zone.mode}"
                    )

            # Show sample measurements
            if mapped.measurements:
                print("\nSample Measurements (first 5):")
                for measure in mapped.measurements[:5]:
                    print(f"  M{measure.index} ({measure.alias}): {measure.valeur} {measure.unit}")
        else:
            print("\nGroup details:")
            for group_name in sorted(frame.groups.keys()):
                count = len(frame.groups[group_name])
                indices = sorted(frame.groups[group_name].keys())
                print(
                    f"  {group_name}: {count} items (indices: {indices[:10]}{'...' if len(indices) > 10 else ''})"
                )

    return 0


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Decode IRegul protocol frames from files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        help="Path to file containing IRegul frame data",
    )
    parser.add_argument(
        "--mapped",
        action="store_true",
        help="Map decoded data to typed dataclasses",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of human-readable summary",
    )

    args = parser.parse_args()
    return asyncio.run(decode_command(args))


if __name__ == "__main__":
    sys.exit(main())
