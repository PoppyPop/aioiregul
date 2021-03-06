"""Tests for the `automateddl` module."""

import pytest

from . import CONFIGS_DIR, STATIC_DIR

import src.aioiregul
from datetime import  timedelta
import asyncio

@pytest.mark.asyncio
async def test_auth():
    opt = src.aioiregul.ConnectionOptions(
        username='empty', password='bottle', iregul_base_url='http://localhost:8779/modules/')

    dev = src.aioiregul.Device(opt)

    assert await dev.authenticate() == True

@pytest.mark.asyncio
async def test_collect():
    opt = src.aioiregul.ConnectionOptions(
        username='empty', password='bottle', iregul_base_url='http://localhost:8779/modules/')

    dev = src.aioiregul.Device(opt)

    res = await dev.collect()
    
    assert res != None
    assert len(res) == 4
    assert len(res['outputs']) == 18
    assert len(res['sensors']) == 15
    assert len(res['inputs']) == 9
    assert len(res['measures']) == 58

@pytest.mark.asyncio
async def test_update():
    opt = src.aioiregul.ConnectionOptions(
        username='empty', password='bottle', iregul_base_url='http://localhost:8779/modules/', refresh_rate=timedelta(seconds=1))

    dev = src.aioiregul.Device(opt)

    res = await dev.collect()

    await asyncio.sleep(2)

    res = await dev.collect()
    
    assert res != None
    assert len(res) == 4
    assert len(res['outputs']) == 18
    assert len(res['sensors']) == 15
    assert len(res['inputs']) == 9
    assert len(res['measures']) == 58