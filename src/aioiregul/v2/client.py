"""Async socket client for IRegul device communication.

This client supports two data retrieval modes:
- 502: Full configuration + values (heavy on the server).
- 501: Values-only (lighter), when a configuration skeleton is provided.

End-users can optionally supply a configuration dictionary skeleton (keys only,
no values) to the constructor. When present, the client will issue the faster
501 command and merge the returned values into the provided skeleton before
mapping to typed models.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from dotenv import load_dotenv

from ..iregulapi import IRegulApiInterface
from .decoder import DecodedFrame, ValueType, decode_text
from .mappers import MappedFrame, map_frame

# Load environment variables from .env file
load_dotenv()

LOGGER = logging.getLogger(__name__)


def _get_env(key: str, default: str | None = None) -> str:
    """Get environment variable with optional default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


class IRegulClient(IRegulApiInterface):
    """Async socket client for IRegul device communication."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        device_id: str | None = None,
        password: str | None = None,
        timeout: float = 60.0,
        config_skeleton: dict[str, dict[int, dict[str, ValueType]]] | None = None,
    ):
        """
        Initialize IRegul socket client.

        Configuration is loaded from environment variables if not provided as arguments:
        - IREGUL_HOST (default: i-regul.fr)
        - IREGUL_PORT (default: 443)
        - IREGUL_DEVICE_ID (required if not provided)
        - IREGUL_PASSWORD_V2 (required if not provided)

        Optionally, provide a configuration skeleton (keys only, no values).
        When supplied, the client will fetch values via command 501 and merge
        them into the skeleton to produce a complete mapped frame.

        Args:
            host: Hostname or IP address of the IRegul device
            port: Port number for the socket connection
            device_id: Device identifier for the IRegul device
            password: Device password for authentication
            timeout: Default timeout for socket operations in seconds
            config_skeleton: Configuration dictionary without values, structured
                as {group: {index: {field_name: ""}}}

        Raises:
            ValueError: If required environment variables are missing
        """
        self.host = host or os.getenv("IREGUL_HOST", "i-regul.fr")
        self.port = port or int(os.getenv("IREGUL_PORT", "443"))
        self.device_id = device_id or _get_env("IREGUL_DEVICE_ID")
        self.password = password or _get_env("IREGUL_PASSWORD_V2")
        self.timeout = timeout
        self.config_skeleton: dict[str, dict[int, dict[str, ValueType]]] | None = config_skeleton

    async def _send_command(
        self, command: str
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Open connection and send command to device.

        Args:
            command: Command code to send (e.g., "501", "502", "203")

        Returns:
            Tuple of (reader, writer) for further communication

        Raises:
            TimeoutError: If connection timeout occurs
            ConnectionError: If unable to connect to device
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, limit=100000),
                timeout=self.timeout,
            )
        except TimeoutError as e:
            raise TimeoutError(f"Connection timeout to {self.host}:{self.port}") from e
        except (ConnectionRefusedError, OSError) as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}: {e}") from e

        message = f"cdraminfo{self.device_id}{self.password}{{{command}#}}"
        LOGGER.debug(f"Sending command {command} to device {self.device_id}")
        writer.write(message.encode("utf-8"))
        await writer.drain()

        return reader, writer

    async def defrost(self) -> bool:
        """
        Trigger defrost operation on the device.

        Sends the defrost command to the IRegul device via socket.

        Returns:
            True if defrost was triggered successfully, False otherwise.

        Raises:
            asyncio.TimeoutError: If unable to connect or respond in time
            ConnectionError: If unable to connect to device
            ValueError: If response format is invalid
        """
        reader, writer = await self._send_command("203")

        try:
            # Read response
            response = await asyncio.wait_for(reader.readuntil(b"}"), timeout=self.timeout)
            response_text = response.decode("utf-8")
            LOGGER.debug(f"Received defrost response: {response_text}")

            # Check for success indication in response
            return "defrost_ok" in response_text.lower()
        finally:
            writer.close()
            await writer.wait_closed()

    async def get_data(self) -> MappedFrame:
        """
        Retrieve device data using 502 (full) or 501 (values-only).

        Behavior:
        - If `config_skeleton` is not provided: issues 502 (full data) and maps.
        - If `config_skeleton` is provided: issues 501 (values-only), merges the
          returned values into the skeleton, then maps.

        The device_id is set during client initialization via IREGUL_DEVICE_ID env var.

        Args:
            timeout: Maximum time in seconds to wait for response (default: 60)

        Returns:
            MappedFrame containing the typed device data.

        Raises:
            asyncio.TimeoutError: If response not received within timeout period
            ConnectionError: If unable to connect to device
            ValueError: If response format is invalid
        """
        # Choose command based on presence of a config skeleton
        cmd = "501" if self.config_skeleton is not None else "502"
        reader, writer = await self._send_command(cmd)

        try:
            # Read responses until we get the NEW format (skip OLD)
            new_response = await self._read_new_response(reader, timeout=self.timeout)
            LOGGER.debug(f"Received NEW response: {len(new_response)} bytes")

            # Decode the response
            decoded = await decode_text(new_response)
            LOGGER.debug(f"Decoded frame with timestamp: {decoded.timestamp}")

            # Initialize skeleton if not present
            if self.config_skeleton is None:
                self.config_skeleton = {}

            # Merge values into skeleton (handles both initial creation and updates)
            merged_groups = self._merge_values_into_skeleton(self.config_skeleton, decoded.groups)
            merged_frame = DecodedFrame(
                is_old=decoded.is_old,
                timestamp=decoded.timestamp,
                count=decoded.count,
                groups=merged_groups,
            )
            return map_frame(merged_frame)
        finally:
            writer.close()
            await writer.wait_closed()

    async def check_auth(self) -> bool:
        """Check if credentials are valid.

        Performs minimal authentication check to verify credentials
        by issuing a 501 command and checking for an OLD frame response.

        Returns:
            True if authentication is successful, False otherwise.

        Raises:
            asyncio.TimeoutError: If response not received within timeout period
            ConnectionError: If unable to connect to device
        """
        reader, writer = await self._send_command("501")

        try:
            # Read first response - should be OLD frame if auth is valid
            try:
                frame = await asyncio.wait_for(
                    reader.readuntil(b"}"),
                    timeout=self.timeout,
                )
            except asyncio.IncompleteReadError as e:
                LOGGER.error(f"Incomplete response during auth check: {e}")
                return False
            except asyncio.LimitOverrunError as e:
                LOGGER.error(f"Response too large during auth check: {e}")
                return False

            if not frame:
                LOGGER.error("Empty response during auth check")
                return False

            response_text = frame.decode("utf-8")
            LOGGER.debug(f"Received auth check response: {response_text[:50]}...")

            # Check if this is an OLD format response (indicates successful auth)
            if response_text.startswith("OLD"):
                LOGGER.debug("Auth check successful (OLD frame received)")
                return True

            LOGGER.warning("Auth check failed (no OLD frame received)")
            return False
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
                raise TimeoutError("Timeout waiting for NEW response")

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

    def _merge_values_into_skeleton(
        self,
        skeleton: dict[str, dict[int, dict[str, ValueType]]],
        values: dict[str, dict[int, dict[str, ValueType]]],
    ) -> dict[str, dict[int, dict[str, ValueType]]]:
        """Merge values from a response into a configuration skeleton.

        The skeleton acts as a cache of last-known values (from an initial 502
        or previous 501 merges). The values mapping comes from decoding a frame.
        This function produces a combined groups dictionary suitable for mapping,
        preserving cached values for fields not present in the response.

        Dynamic fields (valeur, resultat, etat, mode, mode_select) are included
        in the merged result but not cached in the skeleton. Groups 'mem', 'P',
        and 'J' are not cached.

        Args:
            skeleton: Cached configuration dict {group: {index: {field: cached_value}}}.
            values: Decoded groups from a response {group: {index: {field: value}}}.

        Returns:
            A merged groups dict {group: {index: {field: value}}} where fields
            present in the response override the cached values in the skeleton.
            Fields not present in the response keep their cached value.
        """
        # Dynamic fields that should not be cached
        dynamic_fields = {"valeur", "resultat", "etat", "mode", "mode_select"}
        # Groups that should not be cached
        excluded_groups = {"mem", "P", "J"}

        merged: dict[str, dict[int, dict[str, ValueType]]] = {}

        # Start from skeleton values (cache of last-known values)
        for group, indexes in skeleton.items():
            merged[group] = {}
            for idx, fields in indexes.items():
                merged[group][idx] = {}
                for name, cached_val in fields.items():
                    merged[group][idx][name] = cached_val

        # Overlay values from the response and update skeleton cache
        for group, indexes in values.items():
            if group not in merged:
                merged[group] = {}
            if group not in skeleton and group not in excluded_groups:
                skeleton[group] = {}
            for idx, fields in indexes.items():
                if idx not in merged[group]:
                    merged[group][idx] = {}
                if group not in excluded_groups and idx not in skeleton[group]:
                    skeleton[group][idx] = {}
                for name, val in fields.items():
                    # Always include in merged result
                    merged[group][idx][name] = val
                    # Cache only non-dynamic fields in non-excluded groups
                    if group not in excluded_groups and name not in dynamic_fields:
                        skeleton[group][idx][name] = val

        return merged

    def save_skeleton(self) -> str:
        """Serialize the current configuration skeleton to a JSON string.

        The skeleton is serialized with proper handling of integer keys,
        which are converted to strings during JSON serialization.

        Returns:
            JSON string representation of the config_skeleton.

        Raises:
            ValueError: If no skeleton is available to save.
        """
        if self.config_skeleton is None:
            raise ValueError("No skeleton available to save")
        return json.dumps(self.config_skeleton)

    def load_skeleton_from(self, skeleton_json: str) -> None:
        """Deserialize a configuration skeleton from a JSON string.

        Restores the skeleton with proper conversion of string keys back to integers,
        as JSON serialization converts dict keys to strings.

        Args:
            skeleton_json: JSON string representation of a skeleton.

        Raises:
            ValueError: If the JSON is invalid or has incorrect structure.
        """
        try:
            deserialized = json.loads(skeleton_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}") from e

        # Convert string keys back to integers for group indices
        # JSON converts dict keys to strings, so we need to convert them back
        skeleton: dict[str, dict[int, dict[str, ValueType]]] = {}
        for group_key, group_data in deserialized.items():
            if isinstance(group_data, dict):
                skeleton[group_key] = {int(k): v for k, v in group_data.items()}  # type: ignore[typeddict-item]
            else:
                skeleton[group_key] = group_data  # type: ignore[typeddict-item]

        self.config_skeleton = skeleton
