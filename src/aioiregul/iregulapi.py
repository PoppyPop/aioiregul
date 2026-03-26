"""
Docstring for aioiregul.iregulapi
"""

from typing import Protocol
from urllib.parse import urlsplit

from .models import MappedFrame


def split_host_port(host: str, port: int | None = None) -> tuple[str, int | None]:
    """Split and validate host string that may contain an embedded port.

    Parses a host string that optionally includes a port (e.g. ``example.com:2000``
    or ``[::1]:8080`` for IPv6), extracts the hostname and port, and validates
    that the port number is in the valid range 1–65535.

    If an explicit ``port`` argument is also provided alongside an embedded port
    in the host, the embedded port takes precedence.

    Args:
        host: Hostname, IP address, or host:port string to parse.
        port: Optional fallback port when none is embedded in *host*.

    Returns:
        A ``(hostname, port)`` tuple where *hostname* never contains a port
        suffix and *port* is ``None`` when no port is found.

    Raises:
        ValueError: If the embedded port is not a valid integer or is outside
            the range 1–65535.

    Example:
        >>> split_host_port("example.com:2000")
        ('example.com', 2000)
        >>> split_host_port("[::1]:8080")
        ('::1', 8080)
        >>> split_host_port("example.com", 443)
        ('example.com', 443)
    """
    parsed = urlsplit(f"//{host}")
    if parsed.hostname is None:
        return host, port
    embedded_port = parsed.port
    if embedded_port is not None:
        if not (1 <= embedded_port <= 65535):
            raise ValueError(f"Port {embedded_port} is out of the valid range 1–65535.")
        return parsed.hostname, embedded_port
    return parsed.hostname, port


class IRegulApiInterface(Protocol):
    """Interface for IRegul device operations.

    Defines the contract for device client implementations (v1 and v2).
    Both methods handle authentication and device communication internally.
    """

    async def get_data(self) -> MappedFrame | None:
        """Retrieve device data as a MappedFrame.

        Returns:
            MappedFrame with device data or None if refresh failed.

        Raises:
            CannotConnect: If unable to connect to the device.
            InvalidAuth: If authentication fails.
        """
        ...

    async def defrost(self) -> bool:
        """Trigger defrost operation on the device.

        Returns:
            True if defrost was triggered successfully, False otherwise.

        Raises:
            CannotConnect: If unable to connect to the device.
            InvalidAuth: If authentication fails.
        """
        ...

    async def check_auth(self) -> bool:
        """Check if credentials are valid.

        Performs minimal authentication check to verify credentials.

        Returns:
            True if authentication is successful, False otherwise.

        Raises:
            CannotConnect: If unable to connect to the device.
            InvalidAuth: If authentication fails.
        """
        ...
