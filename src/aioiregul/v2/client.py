"""Async socket client for IRegul device communication."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from dotenv import load_dotenv

from .decoder import decode_text
from .mappers import map_frame

# Load environment variables from .env file
load_dotenv()

LOGGER = logging.getLogger(__name__)


def _get_env(key: str, default: str | None = None) -> str:
    """Get environment variable with optional default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


class IRegulClient:
    """Async socket client for IRegul device communication."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        device_id: str | None = None,
        device_key: str | None = None,
    ):
        """
        Initialize IRegul socket client.

        Configuration is loaded from environment variables if not provided as arguments:
        - IREGUL_HOST (default: i-regul.fr)
        - IREGUL_PORT (default: 443)
        - IREGUL_DEVICE_ID (required if not provided)
        - IREGUL_DEVICE_KEY (required if not provided)

        Args:
            host: Hostname or IP address of the IRegul device
            port: Port number for the socket connection
            device_id: Device identifier for the IRegul device
            device_key: Device key/token for authentication

        Raises:
            ValueError: If required environment variables are missing
        """
        self.host = host or os.getenv("IREGUL_HOST", "i-regul.fr")
        self.port = port or int(os.getenv("IREGUL_PORT", "443"))
        self.device_id = device_id or _get_env("IREGUL_DEVICE_ID")
        self.device_key = device_key or _get_env("IREGUL_DEVICE_KEY")

    async def get_data(
        self,
        timeout: float = 60.0,
        mapped: bool = True,
    ) -> dict[str, Any]:
        """
        Connect to device and retrieve full data using command 502.

        Issues a 502 command (full data with parameters and labels), waits for
        the response, skips the OLD message format, and returns the NEW message.

        The device_id is set during client initialization via IREGUL_DEVICE_ID env var.

        Args:
            timeout: Maximum time in seconds to wait for response (default: 60)
            mapped: If True, return mapped typed data; if False, return raw decoder data

        Returns:
            Dictionary containing the decoded and optionally mapped device data.
            If mapped=True, returns MappedFrame as dict.
            If mapped=False, returns DecodedFrame as dict.

        Raises:
            asyncio.TimeoutError: If response not received within timeout period
            ConnectionError: If unable to connect to device
            ValueError: If response format is invalid
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, limit=100000),
                timeout=timeout,
            )
        except asyncio.TimeoutError as e:
            raise asyncio.TimeoutError(f"Connection timeout to {self.host}:{self.port}") from e
        except (ConnectionRefusedError, OSError) as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}") from e

        try:
            # Build and send the 502 command
            message = f"cdraminfo{self.device_id}{self.device_key}{{502#}}"
            LOGGER.debug(f"Sending command: {message}")
            writer.write(message.encode("utf-8"))
            await writer.drain()

            # Read responses until we get the NEW format (skip OLD)
            new_response = await self._read_new_response(reader, timeout=timeout)
            LOGGER.debug(f"Received NEW response: {len(new_response)} bytes")

            # Decode the response
            decoded = await decode_text(new_response)
            LOGGER.debug(f"Decoded frame with timestamp: {decoded.timestamp}")

            # Return mapped or raw data
            if mapped:
                mapped_frame = map_frame(decoded)
                return {
                    "timestamp": decoded.timestamp,
                    "zones": [z.__dict__ for z in mapped_frame.zones],
                    "inputs": [i.__dict__ for i in mapped_frame.inputs],
                    "outputs": [o.__dict__ for o in mapped_frame.outputs],
                    "measurements": [m.__dict__ for m in mapped_frame.measurements],
                    "parameters": [p.__dict__ for p in mapped_frame.parameters],
                    "labels": [label.__dict__ for label in mapped_frame.labels],
                    "analog_sensors": [a.__dict__ for a in mapped_frame.analog_sensors],
                    "modbus_registers": [r.__dict__ for r in mapped_frame.modbus_registers],
                    "configuration": (
                        mapped_frame.configuration.__dict__ if mapped_frame.configuration else None
                    ),
                    "memory": (mapped_frame.memory.__dict__ if mapped_frame.memory else None),
                }
            else:
                return {
                    "timestamp": decoded.timestamp,
                    "is_old_format": decoded.is_old,
                    "groups": decoded.groups,
                }
        finally:
            writer.close()
            await writer.wait_closed()

    async def _read_new_response(self, reader: asyncio.StreamReader, timeout: float = 60.0) -> str:
        """
        Read socket responses until NEW format is received.

        Reads complete frames (ending with '}') and skips OLD format responses.

        Args:
            reader: The asyncio stream reader
            timeout: Maximum time to wait for complete NEW response

        Returns:
            The NEW format response as a string

        Raises:
            asyncio.TimeoutError: If timeout expires
            ValueError: If invalid response format received
        """
        deadline = asyncio.get_event_loop().time() + timeout

        while True:
            remaining_time = deadline - asyncio.get_event_loop().time()
            if remaining_time <= 0:
                raise asyncio.TimeoutError("Timeout waiting for NEW response")

            try:
                # Read until end of frame marker
                frame = await asyncio.wait_for(
                    reader.readuntil(b"}"),
                    timeout=remaining_time,
                )
            except asyncio.IncompleteReadError as e:
                raise ValueError(f"Incomplete response from device: {e}") from e
            except asyncio.LimitOverrunError as e:
                raise ValueError(f"Response too large or invalid format: {e}") from e

            if not frame:
                raise ValueError("Empty response from device")

            response_text = frame.decode("utf-8")
            LOGGER.debug(f"Received frame: {response_text[:50]}...")

            # Check if this is the NEW format (not starting with OLD)
            if not response_text.startswith("OLD"):
                return response_text

            LOGGER.debug("Skipping OLD format response, waiting for NEW...")
