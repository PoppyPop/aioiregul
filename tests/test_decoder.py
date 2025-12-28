from datetime import datetime

import pytest
from src.aioiregul.v2.decoder import decode_file


@pytest.mark.asyncio
async def test_decode_501_new_basic():
    frame = await decode_file("tests/data/v2messages/501-NEW.txt")

    assert not frame.is_old
    assert frame.timestamp == datetime(2025, 1, 15, 23, 38, 51)
    assert frame.count is not None and frame.count > 0

    # Basic groups existence
    assert "mem" in frame.groups
    assert "Z" in frame.groups
    assert "I" in frame.groups
    assert "O" in frame.groups
    assert "A" in frame.groups
    assert "M" in frame.groups
    assert "B" in frame.groups

    # Spot-check a few values
    assert frame.groups["Z"][11]["consigne_normal"] == pytest.approx(20.1)
    assert frame.groups["A"][6]["valeur"] == pytest.approx(6.9)
    assert frame.groups["mem"][0]["alarme_flag"] is False


@pytest.mark.asyncio
async def test_decode_501_old_flag():
    frame = await decode_file("tests/data/v2messages/501-OLD.txt")

    assert frame.is_old
    assert frame.timestamp == datetime(2025, 1, 15, 23, 34, 47)
    assert frame.count is not None and frame.count > 0


@pytest.mark.asyncio
async def test_decode_502_new_rich_groups():
    frame = await decode_file("tests/data/v2messages/502-NEW.txt")

    assert not frame.is_old
    assert frame.timestamp == datetime(2025, 1, 15, 23, 37, 46)
    assert frame.count is not None and frame.count >= 200

    # Rich groups P and J should be present
    assert "P" in frame.groups
    assert "J" in frame.groups

    # Spot-check parameters and labels
    assert frame.groups["P"][0]["nom"] == "degivrage delta (°)"
    assert frame.groups["P"][0]["valeur"] == 3

    # Check a measure with alias
    assert frame.groups["M"][16]["alias"] == "Puissance absorbée"
    assert frame.groups["M"][16]["valeur"] == pytest.approx(488.6)

    # Check a bus register status
    assert frame.groups["B"][14]["etat"] == "ok L"


@pytest.mark.asyncio
async def test_decode_502_old_flag():
    frame = await decode_file("tests/data/v2messages/502-OLD.txt")

    assert frame.is_old
    assert frame.timestamp == datetime(2025, 1, 15, 23, 37, 3)
    assert frame.count is not None and frame.count > 0
