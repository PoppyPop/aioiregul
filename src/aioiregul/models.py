"""Shared typed dataclasses for IRegul protocol groups.

This module defines strongly-typed representations for the main data groups
returned by the IRegul API: zones (Z), inputs (I), outputs (O), measurements (M),
parameters (P), labels (J), and other supporting structures, plus MappedFrame
and the IRegulDeviceInterface protocol for device operations.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


def _empty_str_str_dict() -> dict[str, str]:
    """Return an empty dict with str keys and str values for dataclass defaults."""

    return {}


@dataclass
class Zone:
    """Zone configuration and status (group Z).

    Attributes:
        index: Zone index/ID.
        consigne_normal: Normal setpoint temperature.
        consigne_reduit: Reduced setpoint temperature.
        consigne_horsgel: Frost protection temperature.
        mode_select: Selected operating mode.
        mode: Current operating mode.
        zone_nom: Zone name/description.
        temperature_max: Maximum temperature limit.
        temperature_min: Minimum temperature limit.
        zone_active: Whether zone is active.
        extra: Additional fields not covered by typed attributes.
    """

    index: int
    consigne_normal: float
    consigne_reduit: float
    consigne_horsgel: float
    mode_select: int
    mode: int
    zone_nom: str = ""
    temperature_max: float | None = None
    temperature_min: float | None = None
    zone_active: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Input:
    """Digital input status (group I).

    Attributes:
        index: Input index/ID.
        valeur: Current input value (0 or 1).
        alias: Human-readable name/description.
        id: Internal ID.
        flag: Configuration flag.
        adr: Hardware address.
        type: Input type code.
        esclave: Slave device ID.
        extra: Additional fields.
    """

    index: int
    valeur: int
    alias: str = ""
    id: int | None = None
    flag: int | None = None
    adr: int | None = None
    type: int | None = None
    esclave: int | None = None
    min: int | None = None
    max: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Output:
    """Output control status (group O).

    Attributes:
        index: Output index/ID.
        valeur: Current output value.
        alias: Human-readable name/description.
        id: Internal ID.
        flag: Configuration flag.
        adr: Hardware address.
        type: Output type code.
        esclave: Slave device ID.
        extra: Additional fields.
    """

    index: int
    valeur: int
    alias: str = ""
    id: int | None = None
    flag: int | None = None
    adr: int | None = None
    type: int | None = None
    esclave: int | None = None
    min: int | None = None
    max: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Measurement:
    """Measurement/sensor data (group M).

    Attributes:
        index: Measurement index/ID.
        valeur: Current measured value.
        unit: Unit of measurement (°, kW, kWh, h, etc.).
        alias: Human-readable name/description.
        id: Internal ID.
        flag: Configuration flag.
        type: Measurement type code.
        extra: Additional fields.
    """

    index: int
    valeur: float
    unit: str = ""
    alias: str = ""
    id: int | None = None
    flag: int | None = None
    type: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Parameter:
    """Configuration parameter (group P).

    Attributes:
        index: Parameter index/ID.
        nom: Parameter name/description.
        valeur: Current parameter value.
        min: Minimum allowed value.
        max: Maximum allowed value.
        pas: Step/increment for adjustments.
        id: Internal ID.
        extra: Additional fields.
    """

    index: int
    nom: str
    valeur: float
    min: float
    max: float
    pas: float
    id: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Label:
    """Localized text labels (group J).

    This group contains human-readable strings for UI elements and options.
    Since the structure is highly variable (many different key-value pairs),
    we store all fields as a flexible dict.

    Attributes:
        index: Label group index.
        labels: Mapping of label keys to localized strings.
    """

    index: int
    labels: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class ModbusRegister:
    """Modbus/Bus register data (group B).

    Attributes:
        index: Register index/ID.
        resultat: Register result/value.
        etat: Register state/status string.
        nom_registre: Register name/description.
        nom_esclave: Slave device name.
        esclave: Slave device ID.
        fonction: Modbus function code.
        adresse: Register address.
        valeur: Written/expected value.
        extra: Additional fields.
    """

    index: int
    resultat: int | None = None
    etat: str = ""
    nom_registre: str = ""
    nom_esclave: str = ""
    esclave: int | None = None
    fonction: int | None = None
    adresse: int | None = None
    valeur: int | None = None
    id: int | None = None
    flag: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Configuration:
    """System configuration (group C).

    This group contains many boolean flags and settings. We use a flexible
    dict to accommodate the wide variety of fields.

    Attributes:
        index: Configuration index (typically 0).
        settings: Mapping of setting keys to values.
    """

    index: int
    settings: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class AnalogSensor:
    """Analog sensor data (group A).

    Attributes:
        index: Sensor index/ID.
        valeur: Current sensor value.
        unit: Unit of measurement.
        alias: Human-readable name/description.
        id: Internal ID.
        flag: Configuration flag.
        adr: Hardware address.
        type: Sensor type code.
        min: Minimum valid value.
        max: Maximum valid value.
        esclave: Slave device ID.
        etat: Sensor state/status.
        extra: Additional fields.
    """

    index: int
    valeur: float
    unit: str = ""
    alias: str = ""
    id: int | None = None
    flag: int | None = None
    adr: int | None = None
    type: str = ""
    min: int | None = None
    max: int | None = None
    esclave: int | None = None
    etat: int | None = None
    extra: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class Memory:
    """System memory/state variables (group mem).

    This group contains various system state flags and values stored as
    a flexible dict due to the variety of fields.

    Attributes:
        index: Memory index (typically 0).
        state: Mapping of state variable names to values.
    """

    index: int
    state: dict[str, str] = field(default_factory=_empty_str_str_dict)


@dataclass
class MappedFrame:
    """Complete mapped frame with all typed group data.

    Attributes:
        is_old: Whether this is old data (from OLD prefix).
        timestamp: Frame timestamp.
        count: Optional token count.
        zones: Dictionary of zone configurations indexed by zone ID.
        inputs: Dictionary of digital inputs indexed by input ID.
        outputs: Dictionary of outputs indexed by output ID.
        measurements: Dictionary of measurements indexed by measurement ID.
        parameters: Dictionary of configuration parameters indexed by parameter ID.
        labels: Dictionary of label groups indexed by label ID.
        modbus_registers: Dictionary of Modbus register data indexed by register ID.
        analog_sensors: Dictionary of analog sensor data indexed by sensor ID.
        configuration: System configuration.
        memory: System memory/state.
    """

    is_old: bool
    timestamp: datetime
    count: int | None
    zones: dict[int, Zone]
    inputs: dict[int, Input]
    outputs: dict[int, Output]
    measurements: dict[int, Measurement]
    parameters: dict[int, Parameter]
    labels: dict[int, Label]
    modbus_registers: dict[int, ModbusRegister]
    analog_sensors: dict[int, AnalogSensor]
    configuration: Configuration | None
    memory: Memory | None

    def as_json(self, indent: int | None = None, ensure_ascii: bool = False) -> str:
        """Serialize the mapped frame to a JSON string.

        Args:
            indent: Indentation level for pretty-printing. Use None for a compact string.
            ensure_ascii: Whether to escape non-ASCII characters.

        Returns:
            JSON string representation of the mapped frame.
        """
        payload: dict[str, Any] = asdict(self)
        # Ensure timestamp is ISO-formatted string for JSON serialization
        payload["timestamp"] = self.timestamp.isoformat()
        return json.dumps(payload, indent=indent, ensure_ascii=ensure_ascii)
