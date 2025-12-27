"""Mappers to convert raw decoded groups into typed dataclass instances.

These functions transform the nested dictionaries returned by the decoder
into strongly-typed model objects for easier consumption by API clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .decoder import DecodedFrame
from .models import (
    AnalogSensor,
    Configuration,
    Input,
    Label,
    Measurement,
    Memory,
    ModbusRegister,
    Output,
    Parameter,
    Zone,
)


def _extract_typed_fields(
    data: dict[str, Any], typed_fields: set[str]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Split data dict into typed fields and extra fields.

    Args:
        data: Raw field dictionary.
        typed_fields: Set of field names that have typed attributes.

    Returns:
        Tuple of (typed_dict, extra_dict).
    """
    typed = {}
    extra = {}
    for k, v in data.items():
        if k in typed_fields:
            typed[k] = v
        else:
            extra[k] = v
    return typed, extra


def map_zones(groups: dict[str, dict[int, dict[str, Any]]]) -> list[Zone]:
    """Map group Z to a list of Zone dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of Zone objects.
    """
    zones = []
    if "Z" not in groups:
        return zones

    typed_fields = {
        "consigne_normal",
        "consigne_reduit",
        "consigne_horsgel",
        "mode_select",
        "mode",
        "zone_nom",
        "temperature_max",
        "temperature_min",
        "zone_active",
    }

    for idx, fields in groups["Z"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        zones.append(Zone(index=idx, extra=extra, **typed))

    return zones


def map_inputs(groups: dict[str, dict[int, dict[str, Any]]]) -> list[Input]:
    """Map group I to a list of Input dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of Input objects.
    """
    inputs = []
    if "I" not in groups:
        return inputs

    typed_fields = {
        "valeur",
        "alias",
        "id",
        "flag",
        "adr",
        "type",
        "esclave",
        "min",
        "max",
    }

    for idx, fields in groups["I"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        inputs.append(Input(index=idx, extra=extra, **typed))

    return inputs


def map_outputs(groups: dict[str, dict[int, dict[str, Any]]]) -> list[Output]:
    """Map group O to a list of Output dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of Output objects.
    """
    outputs = []
    if "O" not in groups:
        return outputs

    typed_fields = {
        "valeur",
        "alias",
        "id",
        "flag",
        "adr",
        "type",
        "esclave",
        "min",
        "max",
    }

    for idx, fields in groups["O"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        outputs.append(Output(index=idx, extra=extra, **typed))

    return outputs


def map_measurements(groups: dict[str, dict[int, dict[str, Any]]]) -> list[Measurement]:
    """Map group M to a list of Measurement dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of Measurement objects.
    """
    measurements = []
    if "M" not in groups:
        return measurements

    typed_fields = {"valeur", "unit", "alias", "id", "flag", "type"}

    for idx, fields in groups["M"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        measurements.append(Measurement(index=idx, extra=extra, **typed))

    return measurements


def map_parameters(groups: dict[str, dict[int, dict[str, Any]]]) -> list[Parameter]:
    """Map group P to a list of Parameter dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of Parameter objects.
    """
    parameters = []
    if "P" not in groups:
        return parameters

    typed_fields = {"nom", "valeur", "min", "max", "pas", "id"}

    for idx, fields in groups["P"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        parameters.append(Parameter(index=idx, extra=extra, **typed))

    return parameters


def map_labels(groups: dict[str, dict[int, dict[str, Any]]]) -> list[Label]:
    """Map group J to a list of Label dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of Label objects.
    """
    labels = []
    if "J" not in groups:
        return labels

    for idx, fields in groups["J"].items():
        labels.append(Label(index=idx, labels=dict(fields)))

    return labels


def map_modbus_registers(groups: dict[str, dict[int, dict[str, Any]]]) -> list[ModbusRegister]:
    """Map group B to a list of ModbusRegister dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of ModbusRegister objects.
    """
    registers = []
    if "B" not in groups:
        return registers

    typed_fields = {
        "resultat",
        "etat",
        "nom_registre",
        "nom_esclave",
        "esclave",
        "fonction",
        "adresse",
        "valeur",
        "id",
        "flag",
    }

    for idx, fields in groups["B"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        registers.append(ModbusRegister(index=idx, extra=extra, **typed))

    return registers


def map_analog_sensors(groups: dict[str, dict[int, dict[str, Any]]]) -> list[AnalogSensor]:
    """Map group A to a list of AnalogSensor dataclasses.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        List of AnalogSensor objects.
    """
    sensors = []
    if "A" not in groups:
        return sensors

    typed_fields = {
        "valeur",
        "unit",
        "alias",
        "id",
        "flag",
        "adr",
        "type",
        "min",
        "max",
        "esclave",
        "etat",
    }

    for idx, fields in groups["A"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        sensors.append(AnalogSensor(index=idx, extra=extra, **typed))

    return sensors


def map_configuration(groups: dict[str, dict[int, dict[str, Any]]]) -> Configuration | None:
    """Map group C to a Configuration dataclass.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Configuration object or None if not present.
    """
    if "C" not in groups:
        return None

    # Typically there's only one config entry at index 0
    for idx, fields in groups["C"].items():
        return Configuration(index=idx, settings=dict(fields))

    return None


def map_memory(groups: dict[str, dict[int, dict[str, Any]]]) -> Memory | None:
    """Map group mem to a Memory dataclass.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Memory object or None if not present.
    """
    if "mem" not in groups:
        return None

    # Typically there's only one memory entry at index 0
    for idx, fields in groups["mem"].items():
        return Memory(index=idx, state=dict(fields))

    return None


@dataclass
class MappedFrame:
    """Complete mapped frame with all typed group data.

    Attributes:
        is_old: Whether this is old data (from OLD prefix).
        timestamp: Frame timestamp.
        count: Optional token count.
        zones: List of zone configurations.
        inputs: List of digital inputs.
        outputs: List of outputs.
        measurements: List of measurements.
        parameters: List of configuration parameters.
        labels: List of label groups.
        modbus_registers: List of Modbus register data.
        analog_sensors: List of analog sensor data.
        configuration: System configuration.
        memory: System memory/state.
    """

    is_old: bool
    timestamp: datetime
    count: int | None
    zones: list[Zone]
    inputs: list[Input]
    outputs: list[Output]
    measurements: list[Measurement]
    parameters: list[Parameter]
    labels: list[Label]
    modbus_registers: list[ModbusRegister]
    analog_sensors: list[AnalogSensor]
    configuration: Configuration | None
    memory: Memory | None


def map_frame(frame: DecodedFrame) -> MappedFrame:
    """Map a decoded frame to a fully typed MappedFrame.

    Args:
        frame: Decoded frame from decoder.decode_text or decoder.decode_file.

    Returns:
        MappedFrame with all typed group data.
    """
    return MappedFrame(
        is_old=frame.is_old,
        timestamp=frame.timestamp,
        count=frame.count,
        zones=map_zones(frame.groups),
        inputs=map_inputs(frame.groups),
        outputs=map_outputs(frame.groups),
        measurements=map_measurements(frame.groups),
        parameters=map_parameters(frame.groups),
        labels=map_labels(frame.groups),
        modbus_registers=map_modbus_registers(frame.groups),
        analog_sensors=map_analog_sensors(frame.groups),
        configuration=map_configuration(frame.groups),
        memory=map_memory(frame.groups),
    )
