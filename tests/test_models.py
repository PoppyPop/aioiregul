import json
from datetime import datetime

import pytest

from aioiregul.models import (
    Input,
    MappedFrame,
    Measurement,
    Output,
    Zone,
)


def test_mapped_frame_as_json_roundtrip() -> None:
    """MappedFrame.as_json should produce a parseable JSON string."""
    timestamp = datetime(2024, 1, 1, 12, 0, 0)
    frame = MappedFrame(
        is_old=False,
        timestamp=timestamp,
        count=1,
        zones={
            1: Zone(
                index=1,
                consigne_normal=21.5,
                consigne_reduit=18.0,
                consigne_horsgel=10.0,
                mode_select=1,
                mode=2,
            )
        },
        inputs={1: Input(index=1, valeur=1)},
        outputs={1: Output(index=1, valeur=0)},
        measurements={1: Measurement(index=1, valeur=2.5, unit="kW", alias="Power")},
        parameters={},
        labels={},
        modbus_registers={},
        analog_sensors={},
        configuration=None,
        memory=None,
    )

    json_str = frame.as_json(indent=2)
    parsed = json.loads(json_str)

    assert parsed["timestamp"] == timestamp.isoformat()
    assert parsed["zones"]["1"]["consigne_normal"] == pytest.approx(21.5)
    assert parsed["measurements"]["1"]["alias"] == "Power"
    assert "inputs" in parsed and "outputs" in parsed
