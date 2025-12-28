from datetime import timedelta

import aiohttp
import pytest
import src.aioiregul.v1 as v1
from aiohttp import web


def _html_no_table() -> str:
    return """
    <html><body>
        <div id="content">
            <h1>No table here</h1>
        </div>
    </body></html>
    """


@pytest.fixture
async def mock_server():
    """Normal server matching tests/test_v1.py behavior."""

    async def login_main(request):
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def login_process(request):
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def etat_page(request):
        etat = request.query.get("Etat", "").lower()
        # Provide minimal but valid table
        content = f"<table id='tbl_etat'><tr><td id='ali_td_tbl_etat'>{etat}</td><td id='val_td_tbl_etat'>1</td><td id='unit_td_tbl_etat'>unit</td></tr></table>"
        return web.Response(text=content, content_type="text/html")

    async def processform(request):
        return web.Response(
            status=302, headers={"Location": "/modules/i-regul/index-Etat.php?CMD=Success"}
        )

    app = web.Application()
    app.router.add_get("/modules/login/main.php", login_main)
    app.router.add_post("/modules/login/process.php", login_process)
    app.router.add_get("/modules/i-regul/index-Etat.php", etat_page)
    app.router.add_post("/modules/i-regul/includes/processform.php", processform)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8780)
    await site.start()

    yield "http://localhost:8780"

    await runner.cleanup()


@pytest.fixture
async def server_bad_update():
    """Server that returns non-success update redirect for processform."""

    async def login_main(request):
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def login_process(request):
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def etat_page(request):
        # Return minimal table to avoid heavy parsing
        etat = request.query.get("Etat", "").lower()
        content = f"<table id='tbl_etat'><tr><td id='ali_td_tbl_etat'>{etat}</td><td id='val_td_tbl_etat'>0</td><td id='unit_td_tbl_etat'>unit</td></tr></table>"
        return web.Response(text=content, content_type="text/html")

    async def processform(request):
        # Non-success redirect
        return web.Response(
            status=302, headers={"Location": "/modules/i-regul/index-Etat.php?CMD=Fail"}
        )

    app = web.Application()
    app.router.add_get("/modules/login/main.php", login_main)
    app.router.add_post("/modules/login/process.php", login_process)
    app.router.add_get("/modules/i-regul/index-Etat.php", etat_page)
    app.router.add_post("/modules/i-regul/includes/processform.php", processform)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8781)
    await site.start()

    yield "http://localhost:8781"

    await runner.cleanup()


@pytest.fixture
async def server_no_table_entrees():
    """Server that serves pages with missing table for 'entrees'."""

    async def login_main(request):
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def login_process(request):
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def etat_page(request):
        etat = request.query.get("Etat", "").lower()
        if etat == "entrees":
            return web.Response(text=_html_no_table(), content_type="text/html")
        # Provide normal single-row table for others
        content = f"<table id='tbl_etat'><tr><td id='ali_td_tbl_etat'>{etat}</td><td id='val_td_tbl_etat'>1</td><td id='unit_td_tbl_etat'>unit</td></tr></table>"
        return web.Response(text=content, content_type="text/html")

    async def processform(request):
        return web.Response(
            status=302, headers={"Location": "/modules/i-regul/index-Etat.php?CMD=Success"}
        )

    app = web.Application()
    app.router.add_get("/modules/login/main.php", login_main)
    app.router.add_post("/modules/login/process.php", login_process)
    app.router.add_get("/modules/i-regul/index-Etat.php", etat_page)
    app.router.add_post("/modules/i-regul/includes/processform.php", processform)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8782)
    await site.start()

    yield "http://localhost:8782"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_refresh_fail_returns_none(server_bad_update):
    opt = v1.ConnectionOptions(
        username="user",
        password="pass",
        iregul_base_url=f"{server_bad_update}/modules/",
        refresh_rate=timedelta(seconds=0),
    )

    async with aiohttp.ClientSession() as session:
        dev = v1.Device(opt, session)
        # First call sets lastupdate and skips posting
        _ = await dev.get_data()
        # Second call triggers processform with non-success CMD
        res2 = await dev.get_data()
        assert res2 is None


@pytest.fixture
async def server_auth_flow():
    """Server where __isauth fails but __connect succeeds."""

    async def login_main(request):
        # No btn_i-regul -> not authenticated
        return web.Response(text="<div id='login'></div>", content_type="text/html")

    async def login_process(request):
        # After login, authenticated page
        return web.Response(text="<div id='btn_i-regul'></div>", content_type="text/html")

    async def etat_page(request):
        etat = request.query.get("Etat", "").lower()
        content = f"<table id='tbl_etat'><tr><td id='ali_td_tbl_etat'>{etat}</td><td id='val_td_tbl_etat'>1</td><td id='unit_td_tbl_etat'>unit</td></tr></table>"
        return web.Response(text=content, content_type="text/html")

    async def processform(request):
        return web.Response(
            status=302, headers={"Location": "/modules/i-regul/index-Etat.php?CMD=Success"}
        )

    app = web.Application()
    app.router.add_get("/modules/login/main.php", login_main)
    app.router.add_post("/modules/login/process.php", login_process)
    app.router.add_get("/modules/i-regul/index-Etat.php", etat_page)
    app.router.add_post("/modules/i-regul/includes/processform.php", processform)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8784)
    await site.start()

    yield "http://localhost:8784"

    await runner.cleanup()


@pytest.mark.asyncio
async def test_connect_success_when_not_authenticated(server_auth_flow):
    opt = v1.ConnectionOptions(
        username="user",
        password="pass",
        iregul_base_url=f"{server_auth_flow}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = v1.Device(opt, session)
        res = await dev.get_data()
        assert res is not None


@pytest.mark.asyncio
async def test_collect_no_table_entrees(server_no_table_entrees):
    opt = v1.ConnectionOptions(
        username="user",
        password="pass",
        iregul_base_url=f"{server_no_table_entrees}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = v1.Device(opt, session)
        res = await dev.get_data()
        assert res is not None
        # 'entrees' page had no table, so inputs should be empty
        assert len(res.inputs) == 0
        # Others have a single row
        assert len(res.outputs) == 1
        assert len(res.analog_sensors) == 1
        assert len(res.measurements) == 1


@pytest.mark.asyncio
async def test_quick_refresh_skips_request(mock_server):
    """Call get_data twice quickly to hit 'Too short' branch."""
    opt = v1.ConnectionOptions(
        username="empty",
        password="bottle",
        iregul_base_url=f"{mock_server}/modules/",
        refresh_rate=timedelta(hours=1),
    )

    async with aiohttp.ClientSession() as session:
        dev = v1.Device(opt, session)
        res1 = await dev.get_data()
        res2 = await dev.get_data()
        assert res1 is not None and res2 is not None


@pytest.mark.asyncio
async def test_checkreturn_non_success_nonmandatory():
    """Directly test __checkreturn when refresh is not mandatory."""
    # Build a dummy device (session not used here)
    async with aiohttp.ClientSession() as session:
        dev = v1.Device(
            v1.ConnectionOptions(username="u", password="p", iregul_base_url="http://localhost/"),
            session,
        )
        # Non-success with non-mandatory should return True
        ok = await dev._Device__checkreturn(
            False, "http://localhost/modules/i-regul/index-Etat.php?CMD=Fail"
        )
        assert ok is True
        # Non-success with mandatory should return False
        ok2 = await dev._Device__checkreturn(
            True, "http://localhost/modules/i-regul/index-Etat.php?CMD=Fail"
        )
        assert ok2 is False


@pytest.mark.asyncio
async def test_isauth_connection_error(monkeypatch):
    def raise_conn_error(*args, **kwargs):
        raise aiohttp.ClientConnectionError()

    async with aiohttp.ClientSession() as session:
        dev = v1.Device(
            v1.ConnectionOptions(username="u", password="p", iregul_base_url="http://localhost/"),
            session,
        )
        monkeypatch.setattr(session, "get", raise_conn_error)
        with pytest.raises(v1.CannotConnect):
            await dev.get_data()


@pytest.mark.asyncio
async def test_connect_connection_error(monkeypatch):
    def raise_conn_error(*args, **kwargs):
        raise aiohttp.ClientConnectionError()

    # Use server where __isauth fails to force __connect
    async def fail_login_main(request):
        return web.Response(text="<div id='login'></div>", content_type="text/html")

    app = web.Application()
    app.router.add_get("/fail/login/main.php", fail_login_main)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8783)
    await site.start()

    base = "http://localhost:8783/fail/"

    try:
        async with aiohttp.ClientSession() as session:
            dev = v1.Device(
                v1.ConnectionOptions(username="u", password="p", iregul_base_url=base),
                session,
            )
            monkeypatch.setattr(session, "post", raise_conn_error)
            with pytest.raises(v1.CannotConnect):
                await dev.get_data()
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_defrost_non_success(server_bad_update):
    opt = v1.ConnectionOptions(
        username="user",
        password="pass",
        iregul_base_url=f"{server_bad_update}/modules/",
    )

    async with aiohttp.ClientSession() as session:
        dev = v1.Device(opt, session)
        res = await dev.defrost()
        assert res is False
