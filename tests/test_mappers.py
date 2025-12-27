from datetime import datetime

import pytest
from src.aioiregul.v2.decoder import decode_file
from src.aioiregul.v2.mappers import map_frame


@pytest.mark.asyncio
async def test_map_501_new_basic():
    """Test mapping 501-NEW to typed models."""
    frame = await decode_file("examples/501-NEW.txt")
    mapped = map_frame(frame)

    assert not mapped.is_old
    assert mapped.timestamp == datetime(2025, 1, 15, 23, 38, 51)
    assert mapped.count is not None and mapped.count > 0

    # Check zones
    assert len(mapped.zones) > 0
    zone_11 = next((z for z in mapped.zones if z.index == 11), None)
    assert zone_11 is not None
    assert zone_11.consigne_normal == pytest.approx(20.1)
    assert zone_11.consigne_reduit == pytest.approx(16.0)
    # Note: zone_nom only in 502 data, not in 501

    # Check analog sensors
    assert len(mapped.analog_sensors) > 0
    sensor_6 = next((s for s in mapped.analog_sensors if s.index == 6), None)
    assert sensor_6 is not None
    assert sensor_6.valeur == pytest.approx(6.9)
    # Note: unit and alias only in 502 data

    # Check memory
    assert mapped.memory is not None
    assert mapped.memory.state["alarme_flag"] is False
    assert mapped.memory.state["journal"] == "initialisation"


@pytest.mark.asyncio
async def test_map_502_new_parameters():
    """Test mapping 502-NEW parameters and labels."""
    frame = await decode_file("examples/502-NEW.txt")
    mapped = map_frame(frame)

    assert not mapped.is_old

    # Check parameters
    assert len(mapped.parameters) > 0
    param_0 = next((p for p in mapped.parameters if p.index == 0), None)
    assert param_0 is not None
    assert param_0.nom == "degivrage delta (°)"
    assert param_0.valeur == 3
    assert param_0.min == -10
    assert param_0.max == 10
    assert param_0.pas == pytest.approx(0.5)

    # Check labels
    assert len(mapped.labels) > 0

    # Check measurements with units
    assert len(mapped.measurements) > 0
    measure_16 = next((m for m in mapped.measurements if m.index == 16), None)
    assert measure_16 is not None
    assert measure_16.alias == "Puissance absorbée"
    assert measure_16.valeur == pytest.approx(488.6)
    assert measure_16.unit == "kWh"

    # Check modbus registers
    assert len(mapped.modbus_registers) > 0
    reg_14 = next((r for r in mapped.modbus_registers if r.index == 14), None)
    assert reg_14 is not None
    assert reg_14.etat == "ok L"
    assert reg_14.nom_registre == "DC bus voltage"


@pytest.mark.asyncio
async def test_map_inputs_outputs():
    """Test input and output mapping from 502 data with full metadata."""
    frame = await decode_file("examples/502-NEW.txt")
    mapped = map_frame(frame)

    # Check inputs
    assert len(mapped.inputs) > 0
    input_9 = next((i for i in mapped.inputs if i.index == 9), None)
    assert input_9 is not None
    assert input_9.valeur == 1
    assert input_9.alias == "Sécurité chauffage"

    # Check outputs
    assert len(mapped.outputs) > 0
    output_4 = next((o for o in mapped.outputs if o.index == 4), None)
    assert output_4 is not None
    assert output_4.valeur == 1
    assert output_4.alias == "Détendeur"


@pytest.mark.asyncio
async def test_configuration_mapping():
    """Test configuration group mapping."""
    frame = await decode_file("examples/502-NEW.txt")
    mapped = map_frame(frame)

    assert mapped.configuration is not None
    assert mapped.configuration.index == 0
    assert "autorisation_chauffage" in mapped.configuration.settings
    assert mapped.configuration.settings["autorisation_chauffage"] == 1
    assert "option_inverter" in mapped.configuration.settings
