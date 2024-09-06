import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

LOGGER = logging.getLogger(__package__)


@dataclass
class ConnectionOptionsv2:
    """IRegul options for connection."""

    username: str
    password: str
    iregul_base_url: str = "i-regul.fr"
    refresh_rate: timedelta = timedelta(minutes=5)


class apiv2:
    def __init__(
        self,
        options: ConnectionOptionsv2,
    ):
        """Device init."""
        self.options = options

    async def collect(self, callback: Callable[[], dict]):
        """Collect datas from api"""
