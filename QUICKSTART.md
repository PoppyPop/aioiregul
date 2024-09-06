# Quick Reference - IRegul Decoder

## Installation

```bash
pip install -e .
```

## Basic Usage

```python
import asyncio
from aioiregul import decode_file, map_frame

async def main():
    # Decode frame
    frame = await decode_file("examples/502-NEW.txt")

    # Map to typed models
    mapped = map_frame(frame)

    # Access data
    print(f"Zones: {len(mapped.zones)}")
    print(f"Power: {mapped.measurements[16].valeur} kWh")

asyncio.run(main())
```

## CLI Commands

```bash
# Decode and summarize
python -m aioiregul.cli examples/501-NEW.txt

# With typed mapping
python -m aioiregul.cli examples/502-NEW.txt --mapped

# JSON output
python -m aioiregul.cli examples/501-OLD.txt --json

# Full JSON with types
python -m aioiregul.cli examples/502-NEW.txt --mapped --json > output.json
```

## Data Access Patterns

```python
# Zones
for zone in mapped.zones:
    print(f"Zone {zone.index}: {zone.consigne_normal}°")

# Measurements
power = next(m for m in mapped.measurements if "Puissance" in m.alias)
print(f"{power.alias}: {power.valeur} {power.unit}")

# Sensors
for sensor in mapped.analog_sensors:
    print(f"{sensor.alias}: {sensor.valeur} {sensor.unit}")

# Parameters
param = mapped.parameters[0]
print(f"{param.nom}: {param.valeur} [{param.min}-{param.max}]")

# System state
if mapped.memory:
    print(f"State: {mapped.memory.state['etat']}")
    print(f"Alarm: {mapped.memory.state.get('alarme', 0)}")

# Configuration
if mapped.configuration:
    print(f"Heating: {mapped.configuration.settings['autorisation_chauffage']}")
```

## Protocol Groups

| Group | Type    | Example Fields                         |
| ----- | ------- | -------------------------------------- |
| Z     | Zone    | consigne_normal, consigne_reduit, mode |
| I     | Input   | valeur (0/1), alias                    |
| O     | Output  | valeur, alias                          |
| A     | Analog  | valeur, unit, alias                    |
| M     | Measure | valeur, unit, alias                    |
| P     | Param   | nom, valeur, min, max, pas             |
| J     | Label   | UI strings                             |
| B     | Modbus  | resultat, etat, nom_registre           |
| C     | Config  | settings dict                          |
| mem   | Memory  | state dict                             |

## Running Tests

```bash
# All decoder tests
pytest tests/test_decoder.py tests/test_mappers.py -v

# Single test
pytest tests/test_decoder.py::test_decode_501_new_basic -v

# With coverage
pytest tests/test_decoder.py tests/test_mappers.py --cov=aioiregul
```

## Examples

```bash
# Run usage example
python examples/decoder_usage.py

# Run example decoder (if exists)
python examples/decode_example.py
```

## Key Files

- `src/aioiregul/decoder.py` - Core decoder
- `src/aioiregul/models.py` - Typed dataclasses
- `src/aioiregul/mappers.py` - Type mappers
- `src/aioiregul/cli.py` - CLI tool
- `docs/DECODER.md` - Full documentation
- `examples/decoder_usage.py` - Usage example

## Error Handling

```python
from aioiregul import decode_text

try:
    frame = await decode_text(raw_data)
except ValueError as e:
    print(f"Parse error: {e}")
```

## Type Hints

```python
from aioiregul import DecodedFrame, MappedFrame
from aioiregul.models import Zone, Measurement

frame: DecodedFrame = await decode_file("...")
mapped: MappedFrame = map_frame(frame)
zones: list[Zone] = mapped.zones
measures: list[Measurement] = mapped.measurements
```
