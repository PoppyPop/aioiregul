"""Configuration for the pytest test suite."""

import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


@pytest.fixture(autouse=True)
def tests_logs(request):
    # put logs in tests/logs
    log_path = Path("tests") / "logs"

    # tidy logs in subdirectories based on test module and class names
    module = request.module
    class_ = request.cls
    name = request.node.name + ".log"

    if module:
        log_path /= module.__name__.replace("tests.", "")
    if class_:
        log_path /= class_.__name__

    log_path.mkdir(parents=True, exist_ok=True)

    # append last part of the name and enable logger
    log_path /= name
    if log_path.exists():
        log_path.unlink()


def spawn_and_wait_server(port=8779):
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "tests.http_server:app",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    while True:
        if process.returncode is not None and process.returncode != 0:
            raise Exception(process.returncode)
        try:
            requests.get(f"http://localhost:{port}/gen/1024")
        except Exception:
            time.sleep(0.1)
        else:
            break
    return process


@pytest.fixture(scope="session", autouse=True)
def http_server(tmp_path_factory, worker_id):
    if worker_id == "master":
        # single worker: just run the HTTP server
        process = spawn_and_wait_server()
        yield process
        process.kill()
        process.wait()
        return

    # get the temp directory shared by all workers
    root_tmp_dir = tmp_path_factory.getbasetemp().parent

    # try to get a lock
    lock = root_tmp_dir / "lock"
    try:
        lock.mkdir(exist_ok=False)
    except FileExistsError:
        yield  # failed, don't run the HTTP server
        return

    # got the lock, run the HTTP server
    process = spawn_and_wait_server()
    yield process
    process.kill()
    process.wait()
