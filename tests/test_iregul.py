"""Tests for the `automateddl` module."""

import pytest

from . import CONFIGS_DIR, STATIC_DIR

import src.iregul
import aiohttp
import asyncio


@pytest.mark.asyncio
async def test_collect():
    opt = src.iregul.ConnectionOptions(
        username='empty', password='bottle', iregul_base_url='http://localhost:8779/modules/')
    async with aiohttp.ClientSession() as session:
        dev = src.iregul.Device(session, opt)

        res = await dev.collect()
        
        assert res != None
        assert len(res) == 4
        assert len(res['outputs']) == 18
        assert len(res['sensors']) == 15
        assert len(res['inputs']) == 9
        assert len(res['measures']) == 58
