"""
Docstring for aioiregul.iregulapi
"""

from typing import Protocol

from aioiregul.models import MappedFrame


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
