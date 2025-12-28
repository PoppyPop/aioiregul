"""IRegul v2 API - Socket-based client and protocol decoder.

This module provides async socket client communication with IRegul devices
via the undocumented TCP/IP protocol, along with full protocol decoding
and typed dataclass models.

Key Components:
- IRegulClient: Main socket client for device communication
- Decoder: Parses undocumented text protocol frames
- Mappers: Converts raw data to typed dataclasses
- Models: Strongly-typed dataclasses for protocol groups
"""

from ..models import (
    AnalogSensor,
    Configuration,
    Input,
    Label,
    MappedFrame,
    Measurement,
    Memory,
    ModbusRegister,
    Output,
    Parameter,
    Zone,
)
from .client import IRegulClient
from .decoder import DecodedFrame, decode_file, decode_text
from .mappers import map_frame

__all__ = [
    "IRegulClient",
    "DecodedFrame",
    "decode_file",
    "decode_text",
    "MappedFrame",
    "map_frame",
    "AnalogSensor",
    "Configuration",
    "Input",
    "Label",
    "Measurement",
    "Memory",
    "ModbusRegister",
    "Output",
    "Parameter",
    "Zone",
]
