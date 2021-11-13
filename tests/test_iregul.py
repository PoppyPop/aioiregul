"""Tests for the `automateddl` module."""
import asyncio
from datetime import timedelta
from decimal import Decimal

import aiohttp
import pytest
import src.aioiregul


@pytest.mark.asyncio
async def test_auth():
    opt = src.aioiregul.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url="http://localhost:8779/modules/",
    )

    dev = src.aioiregul.Device(opt)

    async with aiohttp.ClientSession() as session:
        assert await dev.authenticate(session)


@pytest.mark.asyncio
async def test_isauth():
    opt = src.aioiregul.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url="http://localhost:8779/modules/",
    )

    dev = src.aioiregul.Device(opt)

    async with aiohttp.ClientSession() as session:
        assert await dev.isauth(session)


@pytest.mark.asyncio
async def test_notisauth():
    opt = src.aioiregul.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url="http://localhost:8779/fail/",
    )

    dev = src.aioiregul.Device(opt)

    async with aiohttp.ClientSession() as session:
        assert not await dev.isauth(session)


@pytest.mark.asyncio
async def test_collect():
    opt = src.aioiregul.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url="http://localhost:8779/modules/",
    )

    dev = src.aioiregul.Device(opt)

    async with aiohttp.ClientSession() as session:
        res = await dev.collect(session)

        assert res is not None
        assert len(res) == 4
        assert len(res["outputs"]) == 18
        assert len(res["sensors"]) == 15
        assert len(res["inputs"]) == 9
        assert len(res["measures"]) == 57
        assert res["measures"]["puissance-absorbee"].value == Decimal("2283.6")


@pytest.mark.asyncio
async def test_update():
    opt = src.aioiregul.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url="http://localhost:8779/modules/",
        refresh_rate=timedelta(seconds=1),
    )

    dev = src.aioiregul.Device(opt)

    async with aiohttp.ClientSession() as session:
        res = await dev.collect(session)

        await asyncio.sleep(2)

        res = await dev.collect(session)

        assert res is not None
        assert len(res) == 4
        assert len(res["outputs"]) == 18
        assert len(res["sensors"]) == 15
        assert len(res["inputs"]) == 9
        assert len(res["measures"]) == 57
        assert res["measures"]["puissance-absorbee"].value == Decimal("2283.6")
