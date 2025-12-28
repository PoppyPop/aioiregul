"""Async decoder for the undocumented IRegul text protocol.

This module parses frames returned by the legacy socket/RPC API using the
observed grammar from samples in the examples directory. A frame looks like:

    OLD15/01/2025 23:34:47{10#mem@0&etat[10]#...}

Structure:
- Optional "OLD" literal prefix to indicate previous snapshot.
- Timestamp in format DD/MM/YYYY HH:MM:SS.
- Curly-braced payload with tokens separated by '#'. The first payload element
  is typically a numeric count of following tokens.
- Each token matches: <Group>@<Index>&<Field>[<Value>]

The decoder produces a strongly-typed `DecodedFrame` containing the timestamp,
an `is_old` flag, the optional token count, and a nested mapping of groups.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime

# Value type supported by the protocol
ValueType = int | float | bool | str


@dataclass
class DecodedFrame:
    """Container for a single decoded IRegul frame.

    Attributes:
        is_old: Whether the frame was marked with the "OLD" prefix.
        timestamp: The frame timestamp parsed from the header.
        count: Optional token count extracted from the payload first element.
        groups: Nested mapping of groups -> index -> field -> parsed value.
    """

    is_old: bool
    timestamp: datetime
    count: int | None
    groups: dict[str, dict[int, dict[str, ValueType]]]


_TOKEN_RE = re.compile(r"^(?P<group>[A-Za-z]+)@(?P<index>\d+)&(?P<name>[^\[]+)\[(?P<value>.*)\]$")


def _parse_value(raw: str) -> ValueType:
    """Parse a raw string value into int, float, bool or str.

    The protocol stores numbers as text; this function casts to a sensible type:
    - "True"/"False" (case-insensitive) -> bool
    - Integer (e.g., "42", "-7") -> int
    - Float (e.g., "3.14", "-0.001") -> float
    - Otherwise remains a string.
    """

    s = raw.strip()
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False

    # Try int
    if re.fullmatch(r"[-+]?\d+", s):
        try:
            return int(s)
        except ValueError:
            pass

    # Try float
    if re.fullmatch(r"[-+]?\d*\.\d+", s) or re.fullmatch(r"[-+]?\d+\.\d*", s):
        try:
            return float(s)
        except ValueError:
            pass

    return s


def _parse_header(text: str) -> tuple[bool, datetime, int]:
    """Extract `(is_old, timestamp, data_start_index)` from the frame header.

    Args:
        text: Raw frame string.

    Returns:
        A tuple `(is_old, timestamp, brace_index)` where `brace_index` is the
        index of the opening '{'.

    Raises:
        ValueError: If the header is malformed or timestamp cannot be parsed.
    """

    if not text:
        raise ValueError("Empty frame")

    # Find payload start
    brace_index = text.find("{")
    if brace_index < 0:
        raise ValueError("Missing payload '{' in frame")

    header = text[:brace_index].strip()
    is_old = False
    if header.startswith("OLD"):
        is_old = True
        header = header[3:].strip()

    try:
        ts = datetime.strptime(header, "%d/%m/%Y %H:%M:%S")
    except ValueError as exc:
        raise ValueError(f"Invalid timestamp header: {header}") from exc

    return is_old, ts, brace_index


def _parse_payload(payload: str) -> tuple[int | None, dict[str, dict[int, dict[str, ValueType]]]]:
    """Parse payload inside braces to `(count, groups)` mapping.

    Args:
        payload: String between '{' and '}'.

    Returns:
        The optional `count` and decoded `groups` mapping.
    """

    parts = [p for p in payload.split("#") if p]
    if not parts:
        return None, {}

    count: int | None = None
    # First part is often a numeric count
    if re.fullmatch(r"\d+", parts[0]):
        try:
            count = int(parts.pop(0))
        except ValueError:
            count = None

    groups: dict[str, dict[int, dict[str, ValueType]]] = {}

    for tok in parts:
        m = _TOKEN_RE.match(tok)
        if not m:
            # Skip unknown token shapes to be robust with undocumented protocol
            continue

        gd = m.groupdict()
        group = gd["group"]
        index = int(gd["index"])  # safe: regex ensures digits
        name = gd["name"].strip()
        value = _parse_value(gd["value"])  # typed cast

        if group not in groups:
            groups[group] = {}
        if index not in groups[group]:
            groups[group][index] = {}
        groups[group][index][name] = value

    return count, groups


async def decode_text(text: str) -> DecodedFrame:
    """Asynchronously decode a raw IRegul frame string.

    Args:
        text: Raw text of the frame (with optional leading whitespace).

    Returns:
        DecodedFrame with timestamp, old/new flag, token count, and groups.

    Raises:
        ValueError: If the frame format is invalid.
    """

    # Be tolerant of stray leading/trailing whitespace
    raw = text.strip()
    is_old, ts, brace_index = _parse_header(raw)

    end_brace_index = raw.rfind("}")
    if end_brace_index < 0 or end_brace_index <= brace_index:
        raise ValueError("Missing closing '}' in frame")

    payload = raw[brace_index + 1 : end_brace_index]
    count, groups = _parse_payload(payload)

    return DecodedFrame(is_old=is_old, timestamp=ts, count=count, groups=groups)


async def decode_file(path: str) -> DecodedFrame:
    """Decode a frame from a file path asynchronously.

    This uses `asyncio.to_thread` to keep the API fully async without adding
    external dependencies.

    Args:
        path: Path to the file containing a single frame.

    Returns:
        DecodedFrame for the file contents.
    """

    def _read_file(p: str) -> str:
        with open(p, encoding="utf-8") as f:
            return f.read()

    content = await asyncio.to_thread(_read_file, path)
    return await decode_text(content)
