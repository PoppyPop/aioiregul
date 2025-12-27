"""Tests for the `automateddl` module."""

import asyncio
from datetime import timedelta
from pathlib import Path

import aiohttp
import pytest
import src.aioiregul.v1
from aiohttp import web

STATIC_DIR = Path(__file__).parent / "data" / "static"


def load_static_file(filename: str) -> str:
    """Load HTML file from static directory."""
    with open(STATIC_DIR / filename, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
async def mock_server():
    """Create a mock aiohttp server with test data."""

    async def login_main(request):
        return web.Response(text=load_static_file("main.html"), content_type="text/html")

    async def login_process(request):
        return web.Response(text=load_static_file("main.html"), content_type="text/html")

    async def fail_login_main(request):
        return web.Response(text=load_static_file("login.html"), content_type="text/html")

    async def etat_page(request):
        etat = request.query.get("Etat", "").lower()
        return web.Response(text=load_static_file(f"{etat}.html"), content_type="text/html")

    async def processform(request):
        return web.Response(
            status=302, headers={"Location": "/modules/i-regul/index-Etat.php?CMD=Success"}
        )

    app = web.Application()
    app.router.add_get("/modules/login/main.php", login_main)
    app.router.add_post("/modules/login/process.php", login_process)
    app.router.add_get("/fail/login/main.php", fail_login_main)
    app.router.add_get("/modules/i-regul/index-Etat.php", etat_page)
    app.router.add_post("/modules/i-regul/includes/processform.php", processform)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8779)
    await site.start()

    yield "http://localhost:8779"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_auth(mock_server):
    opt = src.aioiregul.v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = src.aioiregul.v1.Device(opt, session)
        assert await dev.get_data()


@pytest.mark.asyncio
async def test_isauth(mock_server):
    opt = src.aioiregul.v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = src.aioiregul.v1.Device(opt, session)
        assert await dev.get_data()


@pytest.mark.asyncio
async def test_defrost(mock_server):
    opt = src.aioiregul.v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = src.aioiregul.v1.Device(opt, session)
        assert await dev.defrost()


@pytest.mark.asyncio
async def test_notisauth(mock_server):
    opt = src.aioiregul.v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/fail/",
    )

    async with aiohttp.ClientSession() as session:
        dev = src.aioiregul.v1.Device(opt, session)
        with pytest.raises(src.aioiregul.v1.InvalidAuth):
            await dev.get_data()


@pytest.mark.asyncio
async def test_collect(mock_server):
    opt = src.aioiregul.v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = src.aioiregul.v1.Device(opt, session)
        res = await dev.get_data()

        assert res is not None
        assert len(res.outputs) == 18
        assert len(res.analog_sensors) == 15
        assert len(res.inputs) == 9
        assert len(res.measurements) == 57

        # Find the aggregated "Puissance absorbée" measurement
        puissance_abs = next(
            m for m in res.measurements.values() if m.alias == "Puissance absorbée"
        )
        assert puissance_abs.valeur == pytest.approx(2283.6)


@pytest.mark.asyncio
async def test_update(mock_server):
    opt = src.aioiregul.v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/modules/",
        refresh_rate=timedelta(seconds=1),
    )

    async with aiohttp.ClientSession() as session:
        dev = src.aioiregul.v1.Device(opt, session)
        res = await dev.get_data()

        await asyncio.sleep(2)

        res = await dev.get_data()

        assert res is not None
        assert len(res.outputs) == 18
        assert len(res.analog_sensors) == 15
        assert len(res.inputs) == 9
        assert len(res.measurements) == 57

        puissance_abs = next(
            m for m in res.measurements.values() if m.alias == "Puissance absorbée"
        )
        assert puissance_abs.valeur == pytest.approx(2283.6)
