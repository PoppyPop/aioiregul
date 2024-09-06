#!/usr/bin/env python3
"""Example: Decode and map IRegul protocol frames.

This demonstrates the basic usage of the decoder and mappers to
parse IRegul protocol data into strongly-typed Python objects.
"""

import asyncio
from pathlib import Path

from aioiregul import decode_file, map_frame


async def main() -> None:
    """Decode sample files and display typed data."""
    examples_dir = Path("examples")

    print("=" * 70)
    print("IRegul Protocol Decoder - Example Usage")
    print("=" * 70)

    # Decode 501-NEW (basic telemetry)
    print("\n1. Decoding 501-NEW.txt (basic telemetry)")
    print("-" * 70)
    frame_501 = await decode_file(str(examples_dir / "501-NEW.txt"))
    mapped_501 = map_frame(frame_501)

    print(f"Type: {'OLD' if mapped_501.is_old else 'NEW'}")
    print(f"Timestamp: {mapped_501.timestamp}")
    print(f"Zones: {len(mapped_501.zones)}")
    print(f"Measurements: {len(mapped_501.measurements)}")
    print(f"Analog Sensors: {len(mapped_501.analog_sensors)}")

    # Show active zones
    print("\nActive Zones:")
    for zone in mapped_501.zones[:3]:
        print(
            f"  Zone {zone.index}: "
            f"Normal={zone.consigne_normal}°, "
            f"Reduit={zone.consigne_reduit}°, "
            f"Mode={zone.mode}"
        )

    # Decode 502-NEW (with parameters and labels)
    print("\n2. Decoding 502-NEW.txt (with parameters and labels)")
    print("-" * 70)
    frame_502 = await decode_file(str(examples_dir / "502-NEW.txt"))
    mapped_502 = map_frame(frame_502)

    print(f"Type: {'OLD' if mapped_502.is_old else 'NEW'}")
    print(f"Timestamp: {mapped_502.timestamp}")
    print(f"Parameters: {len(mapped_502.parameters)}")
    print(f"Labels: {len(mapped_502.labels)}")

    # Show some parameters
    print("\nSample Parameters:")
    for param in mapped_502.parameters[:5]:
        print(
            f"  P{param.index} ({param.nom}): "
            f"value={param.valeur}, "
            f"range=[{param.min}, {param.max}], "
            f"step={param.pas}"
        )

    # Show measurements with units
    print("\nKey Measurements:")
    power_measure = next(
        (m for m in mapped_502.measurements if "Puissance absorbée" in m.alias),
        None,
    )
    if power_measure:
        print(f"  {power_measure.alias}: {power_measure.valeur} {power_measure.unit}")

    cop_measure = next(
        (m for m in mapped_502.measurements if m.alias == "COP"),
        None,
    )
    if cop_measure:
        print(f"  {cop_measure.alias}: {cop_measure.valeur}")

    # Show sensor data
    print("\nAnalog Sensors:")
    for sensor in mapped_502.analog_sensors[:3]:
        print(f"  A{sensor.index} ({sensor.alias}): {sensor.valeur} {sensor.unit}")

    # Show system memory state
    if mapped_502.memory:
        print("\nSystem State:")
        print(f"  État: {mapped_502.memory.state.get('etat', 'N/A')}")
        print(f"  Sous-état: {mapped_502.memory.state.get('sous_etat', 'N/A')}")
        print(f"  Alarme: {mapped_502.memory.state.get('alarme', 'N/A')}")
        print(f"  Journal: {mapped_502.memory.state.get('journal', 'N/A')}")

    print("\n" + "=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
