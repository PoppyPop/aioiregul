"""Mappers to convert raw decoded groups into typed dataclass instances.

These functions transform the nested dictionaries returned by the decoder
into strongly-typed model objects for easier consumption by API clients.
"""

from __future__ import annotations

from typing import Any

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
from .decoder import DecodedFrame


def _extract_typed_fields(
    data: dict[str, Any], typed_fields: set[str]
) -> tuple[dict[str, Any], dict[str, str]]:
    """Split data dict into typed fields and extra fields.

    Args:
        data: Raw field dictionary.
        typed_fields: Set of field names that have typed attributes.

    Returns:
        Tuple of (typed_dict, extra_dict) where extra values are stringified.
    """
    typed: dict[str, Any] = {}
    extra: dict[str, str] = {}
    for k, v in data.items():
        if k in typed_fields:
            typed[k] = v
        else:
            extra[k] = str(v)
    return typed, extra


def map_zones(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, Zone]:
    """Map group Z to a dict of Zone dataclasses indexed by zone ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of Zone objects indexed by zone ID.
    """
    zones: dict[int, Zone] = {}
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
        zones[idx] = Zone(index=idx, extra=extra, **typed)

    return zones


def map_inputs(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, Input]:
    """Map group I to a dict of Input dataclasses indexed by input ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of Input objects indexed by input ID.
    """
    inputs: dict[int, Input] = {}
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
        inputs[idx] = Input(index=idx, extra=extra, **typed)

    return inputs


def map_outputs(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, Output]:
    """Map group O to a dict of Output dataclasses indexed by output ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of Output objects indexed by output ID.
    """
    outputs: dict[int, Output] = {}
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
        outputs[idx] = Output(index=idx, extra=extra, **typed)

    return outputs


def map_measurements(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, Measurement]:
    """Map group M to a dict of Measurement dataclasses indexed by measurement ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of Measurement objects indexed by measurement ID.
    """
    measurements: dict[int, Measurement] = {}
    if "M" not in groups:
        return measurements

    typed_fields = {"valeur", "unit", "alias", "id", "flag", "type"}

    for idx, fields in groups["M"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        measurements[idx] = Measurement(index=idx, extra=extra, **typed)

    return measurements


def map_parameters(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, Parameter]:
    """Map group P to a dict of Parameter dataclasses indexed by parameter ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of Parameter objects indexed by parameter ID.
    """
    parameters: dict[int, Parameter] = {}
    if "P" not in groups:
        return parameters

    typed_fields = {"nom", "valeur", "min", "max", "pas", "id"}

    for idx, fields in groups["P"].items():
        typed, extra = _extract_typed_fields(fields, typed_fields)
        parameters[idx] = Parameter(index=idx, extra=extra, **typed)

    return parameters


def map_labels(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, Label]:
    """Map group J to a dict of Label dataclasses indexed by label ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of Label objects indexed by label ID.
    """
    labels: dict[int, Label] = {}
    if "J" not in groups:
        return labels

    for idx, fields in groups["J"].items():
        labels[idx] = Label(index=idx, labels={k: str(v) for k, v in fields.items()})

    return labels


def map_modbus_registers(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, ModbusRegister]:
    """Map group B to a dict of ModbusRegister dataclasses indexed by register ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of ModbusRegister objects indexed by register ID.
    """
    registers: dict[int, ModbusRegister] = {}
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
        registers[idx] = ModbusRegister(index=idx, extra=extra, **typed)

    return registers


def map_analog_sensors(groups: dict[str, dict[int, dict[str, Any]]]) -> dict[int, AnalogSensor]:
    """Map group A to a dict of AnalogSensor dataclasses indexed by sensor ID.

    Args:
        groups: Decoded groups from DecodedFrame.

    Returns:
        Dict of AnalogSensor objects indexed by sensor ID.
    """
    sensors: dict[int, AnalogSensor] = {}
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
        sensors[idx] = AnalogSensor(index=idx, extra=extra, **typed)

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
        return Configuration(index=idx, settings={k: str(v) for k, v in fields.items()})

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
        return Memory(index=idx, state={k: str(v) for k, v in fields.items()})

    return None


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
