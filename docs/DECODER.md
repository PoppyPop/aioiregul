# IRegul Protocol Decoder

The decoder module provides async parsing and mapping for the undocumented IRegul text protocol.

## Features

- **Async decoder**: Parse raw protocol frames into structured data
- **Typed models**: Strongly-typed dataclasses for each group (Zone, Input, Output, Measurement, Parameter, etc.)
- **Flexible mappers**: Convert raw decoded data to typed Python objects
- **CLI tool**: Decode files from the command line

## Quick Start

### Basic Decoding

```python
import asyncio
from aioiregul import decode_file, map_frame

async def main():
    # Decode a frame file
    frame = await decode_file("examples/501-NEW.txt")

    # Access raw data
    print(f"Timestamp: {frame.timestamp}")
    print(f"Is OLD: {frame.is_old}")
    print(f"Groups: {list(frame.groups.keys())}")

    # Map to typed models
    mapped = map_frame(frame)

    # Access typed data
    for zone in mapped.zones:
        print(f"Zone {zone.index}: {zone.consigne_normal}°")

    for measure in mapped.measurements:
        print(f"{measure.alias}: {measure.valeur} {measure.unit}")

asyncio.run(main())
```

### Using the CLI

```bash
# Basic summary
python -m aioiregul.cli examples/501-NEW.txt

# Mapped output with typed models
python -m aioiregul.cli examples/502-NEW.txt --mapped

# JSON output
python -m aioiregul.cli examples/501-OLD.txt --json

# Mapped JSON
python -m aioiregul.cli examples/502-NEW.txt --mapped --json
```

## Protocol Format

The IRegul protocol uses a text-based format:

```
[OLD]DD/MM/YYYY HH:MM:SS{count#group@index&field[value]#...}
```

- **OLD prefix**: Optional, indicates previous snapshot
- **Timestamp**: DD/MM/YYYY HH:MM:SS format
- **Count**: Optional first payload element (numeric)
- **Tokens**: `group@index&field[value]` separated by `#`

### Example

```
15/01/2025 23:38:51{10#mem@0&etat[10]#Z@11&consigne_normal[20.1]#...}
```

## Groups

| Group | Description      | Key Fields                             |
| ----- | ---------------- | -------------------------------------- |
| `Z`   | Zones            | consigne_normal, consigne_reduit, mode |
| `I`   | Digital Inputs   | valeur, alias                          |
| `O`   | Outputs          | valeur, alias                          |
| `A`   | Analog Sensors   | valeur, unit, alias                    |
| `M`   | Measurements     | valeur, unit, alias                    |
| `P`   | Parameters       | nom, valeur, min, max, pas             |
| `J`   | Labels           | Localized UI strings                   |
| `B`   | Modbus Registers | resultat, etat, nom_registre           |
| `C`   | Configuration    | Various system settings                |
| `mem` | Memory State     | System state variables                 |

## API Reference

### Decoder

```python
from aioiregul.decoder import decode_text, decode_file, DecodedFrame

# Decode text
frame: DecodedFrame = await decode_text(raw_text)

# Decode file
frame: DecodedFrame = await decode_file("path/to/file.txt")
```

**DecodedFrame** attributes:

- `is_old: bool` - OLD prefix present
- `timestamp: datetime` - Frame timestamp
- `count: int | None` - Token count
- `groups: Dict[str, Dict[int, Dict[str, ValueType]]]` - Nested group data

### Mappers

```python
from aioiregul.mappers import map_frame, MappedFrame

mapped: MappedFrame = map_frame(frame)
```

**MappedFrame** attributes:

- `zones: List[Zone]`
- `inputs: List[Input]`
- `outputs: List[Output]`
- `measurements: List[Measurement]`
- `parameters: List[Parameter]`
- `labels: List[Label]`
- `modbus_registers: List[ModbusRegister]`
- `analog_sensors: List[AnalogSensor]`
- `configuration: Configuration | None`
- `memory: Memory | None`

### Models

All models are dataclasses with typed attributes and an `extra` dict for unknown fields.

```python
from aioiregul.models import Zone, Measurement, Parameter

# Zone example
zone = Zone(
    index=11,
    consigne_normal=20.1,
    consigne_reduit=16.0,
    mode=0,
    zone_nom="Radiateur"
)

# Measurement example
measure = Measurement(
    index=16,
    valeur=488.6,
    unit="kWh",
    alias="Puissance absorbée"
)
```

## Examples

See [examples/decoder_usage.py](../examples/decoder_usage.py) for a complete example.

## Testing

```bash
# Run decoder tests
pytest tests/test_decoder.py tests/test_mappers.py -v

# With coverage
pytest tests/test_decoder.py tests/test_mappers.py --cov=aioiregul.decoder --cov=aioiregul.mappers
```

## Command Differences

### Command 501

Basic telemetry without metadata:

- Groups: mem, C, Z, I, O, A, M, B
- No `alias`, `unit`, or descriptive names
- Smaller payload (~10 tokens)

### Command 502

Full data with metadata:

- All 501 groups PLUS P (parameters) and J (labels)
- Includes `alias`, `unit`, descriptive names
- Larger payload (~200+ tokens)
- Used for full system state with human-readable labels

## Type Safety

The decoder uses strict typing:

- Values are cast to `int`, `float`, `bool`, or `str`
- All models use type hints
- Optional fields default to `None`
- Unknown fields stored in `extra: Dict[str, Any]`

## Error Handling

```python
from aioiregul.decoder import decode_text

try:
    frame = await decode_text(raw_data)
except ValueError as e:
    print(f"Invalid frame format: {e}")
```

Common errors:

- Missing `{` or `}` braces
- Invalid timestamp format
- Malformed tokens (wrong separator or missing brackets)
