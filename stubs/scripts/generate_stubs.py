"""Generate `.pyi` stubs for `aioiregul` with Pyright and sync inline.

This script invokes `pyright --createstub aioiregul`, which emits stubs under the
repository `typings/aioiregul/` directory. It then copies these `.pyi` files next to
their corresponding modules under `src/aioiregul` and ensures the `py.typed` marker exists.

Usage:
    uv run python stubs/scripts/generate_stubs.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "src"
PACKAGE_NAME = "aioiregul"
TYPINGS_DIR = ROOT / "typings"
SRC_PACKAGE_DIR = SRC_DIR / PACKAGE_NAME


def run(cmd: list[str]) -> None:
    print(f"[run] {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=ROOT)


def ensure_dirs() -> None:
    TYPINGS_DIR.mkdir(parents=True, exist_ok=True)


def _generated_root() -> Path:
    """Return the root where pyright places the `aioiregul` stubs."""
    return TYPINGS_DIR / PACKAGE_NAME


def generate_stubs() -> None:
    """Generate stubs using pyright's createstub.

    Pyright writes under `typings/<package>/`. Ensure PYTHONPATH includes `src`
    so the local package is discoverable.
    """
    # Clean previous generated stubs from typings/aioiregul
    pkg_typings = _generated_root()
    if pkg_typings.exists():
        shutil.rmtree(pkg_typings)

    env = os.environ.copy()
    current_py_path = env.get("UV_PYTHONPATH") or env.get("PYTHONPATH")
    paths = [str(SRC_DIR)]
    if current_py_path:
        paths.append(current_py_path)
    env["PYTHONPATH"] = os.pathsep.join(paths)

    # Run pyright createstub
    run(
        [
            "uv",
            "run",
            "pyright",
            "--createstub",
            PACKAGE_NAME,
        ]
    )


def sync_stubs_into_source() -> None:
    src_base = _generated_root()
    if not src_base.exists():
        print(f"No generated stubs found at {src_base}; skipping source sync.")
        return

    for root, _dirs, files in os.walk(src_base):
        rel = Path(root).relative_to(src_base)
        dest_dir = SRC_PACKAGE_DIR / rel
        dest_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            if f.endswith(".pyi"):
                shutil.copy2(Path(root) / f, dest_dir / f)

    # Ensure py.typed marker exists
    (SRC_PACKAGE_DIR / "py.typed").touch()

    # Format and fix stubs to satisfy pre-commit hooks
    run(["uv", "run", "ruff", "format", str(SRC_PACKAGE_DIR)])
    run(["uv", "run", "ruff", "check", str(SRC_PACKAGE_DIR), "--fix"])


def main() -> None:
    ensure_dirs()
    generate_stubs()
    sync_stubs_into_source()
    print("Stub generation complete.")


if __name__ == "__main__":
    main()
