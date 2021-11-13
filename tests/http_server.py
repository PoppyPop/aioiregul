import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse

from . import STATIC_DIR


def translate_size(size):
    try:
        return int(size)
    except ValueError:
        pass
    size = size.lower()
    if size.endswith("k"):
        multiplier = 2 ** 10
    elif size.endswith("m"):
        multiplier = 2 ** 20
    elif size.endswith("g"):
        multiplier = 2 ** 30
    else:
        raise ValueError("size unit not supported:", size)
    return int(size.rstrip("kmg")) * multiplier


async def virtual_file(size, chunks=4096):
    while size > 0:
        yield b"1" * min(size, chunks)
        size -= chunks


app = FastAPI()


@app.get("/gen/{size}")
async def get(size):
    return StreamingResponse(
        virtual_file(translate_size(size)),
        media_type="application/octet-stream",
    )


@app.post("/modules/i-regul/includes/processform.php")
async def processform():
    return RedirectResponse(url="/modules/i-regul/index-Etat.php?CMD=Success")
    # return __returnfile("sondes.html")


@app.get("/modules/i-regul/index-Etat.php")
async def mesures(Etat: str = None):
    return __returnfile(Etat.lower() + ".html")


@app.post("/modules/login/process.php")
async def process():
    return __returnfile("login.html")


@app.get("/modules/login/main.php")
async def loginmainpage():
    return __returnfile("login.html")


def __returnfile(name: str):
    if os.path.isfile(STATIC_DIR / name):
        with open(STATIC_DIR / name, "r", encoding="utf-8") as file:
            html_content = file.read()
            return HTMLResponse(content=html_content, status_code=200)
    return StreamingResponse(
        virtual_file(translate_size(10)),
        media_type="application/octet-stream",
    )
