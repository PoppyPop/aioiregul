"""IRegul v1 API - Legacy HTTP-based API client.

This module provides HTTP-based communication with IRegul devices through
the web interface using BeautifulSoup for HTML parsing.

Key Components:
- IRegulDeviceInterface: Protocol defining device operations (get_data, defrost).
- Device: Main HTTP client for device communication
- ConnectionOptions: Configuration for device connection
- IRegulData: Data container for measured values
- Exceptions: CannotConnect, InvalidAuth
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from urllib import parse
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from slugify import slugify

from ..iregulapi import IRegulApiInterface
from ..models import AnalogSensor, Input, MappedFrame, Measurement, Output

LOGGER = logging.getLogger(__name__)
load_dotenv()


def _get_env(key: str, default: str | None = None) -> str:
    """Get environment variable with optional default."""

    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


@dataclass
class IRegulData:
    """IRegul data."""

    id: str
    name: str
    value: Decimal
    unit: str


class Device(IRegulApiInterface):
    """IRegul device representation.

    Implements IRegulApiInterface with HTTP-based communication.
    The HTTP session is managed by the device instance for the lifetime
    of the device object.
    """

    login_url: str
    iregulApiBaseUrl: str
    lastupdate: datetime | None = None
    _http_session: aiohttp.ClientSession

    def __init__(
        self,
        http_session: aiohttp.ClientSession,
        host: str | None = None,
        port: int | None = None,
        device_id: str | None = None,
        password: str | None = None,
        refresh_rate: timedelta = timedelta(minutes=5),
    ):
        """Initialize Device with connection options and HTTP session.

        Args:
            options: Connection configuration.
            http_session: Shared aiohttp ClientSession for requests.
        """
        self.host = host or os.getenv("IREGUL_HOST", "vpn.i-regul.com")
        self.port = port or int(os.getenv("IREGUL_PORT", "443"))
        self.device_id = device_id or _get_env("IREGUL_DEVICE_ID")
        self.password = password or _get_env("IREGUL_PASSWORD_V1")

        self.base_url = f"https://{self.host}:{self.port}/modules/"

        self._http_session = http_session
        self.refresh_rate = refresh_rate

        self.main_url = urljoin(self.base_url, "login/main.php")
        self.login_url = urljoin(self.base_url, "login/process.php")
        self.iregulApiBaseUrl = urljoin(self.base_url, "i-regul/")

    async def __isauth(self) -> bool:
        try:
            async with self._http_session.get(self.main_url) as resp:
                result_text = await resp.text()
                soup_login = BeautifulSoup(result_text, "html.parser")
                table_login = soup_login.find("div", attrs={"id": "btn_i-regul"})
                if table_login is not None:
                    LOGGER.debug("Login Ok")
                    return True

                LOGGER.debug("Not Auth")
                return False
        except aiohttp.ClientConnectionError as e:
            raise CannotConnect() from e

    async def __connect(self, throwException: bool) -> bool:
        payload = {
            "sublogin": "1",
            "user": self.device_id,
            "pass": self.password,
        }

        try:
            async with self._http_session.post(self.login_url, data=payload) as resp:
                result_text = await resp.text()
                soup_login = BeautifulSoup(result_text, "html.parser")
                table_login = soup_login.find("div", attrs={"id": "btn_i-regul"})
                if table_login is not None:
                    LOGGER.debug("Login Ok")
                    return True

                LOGGER.error("Login Ko")
                if throwException:
                    raise InvalidAuth()
                return False
        except aiohttp.ClientConnectionError as e:
            raise CannotConnect() from e

    async def __refresh(self, refreshMandatory: bool) -> bool:
        payload = {"SNiregul": self.device_id, "Update": "etat", "EtatSel": "1"}

        # Refresh rate limit
        if self.lastupdate is None:
            # First pass
            self.lastupdate = datetime.now()
            return True

        if datetime.now() - self.lastupdate < self.refresh_rate:
            LOGGER.info("Too short, refresh not required")
            return True

        LOGGER.info("Last refresh: %s", self.lastupdate)
        self.lastupdate = datetime.now()

        try:
            async with self._http_session.post(
                urljoin(self.iregulApiBaseUrl, "includes/processform.php"),
                data=payload,
            ) as resp:
                return await self.__checkreturn(refreshMandatory, str(resp.url))

        except aiohttp.ClientConnectionError as e:
            raise CannotConnect() from e

    async def __checkreturn(self, refreshMandatory: bool, url: str) -> bool:
        data_upd_dict = dict(parse.parse_qsl(parse.urlsplit(str(url)).query))
        data_upd_cmd = data_upd_dict.get("CMD")

        if data_upd_cmd is None or data_upd_cmd != "Success":
            if refreshMandatory:
                LOGGER.error("Update Ko")
                return False
            # We don't care if it has worked or not
            LOGGER.debug("Update Ko")
            return True

        LOGGER.debug("Update Ok")
        return True

    async def __collect(self, type_: str) -> dict[str, IRegulData]:
        """Collect data from device."""
        try:
            async with self._http_session.get(
                urljoin(self.iregulApiBaseUrl, "index-Etat.php?Etat=" + type_)
            ) as resp:
                soup_collect = BeautifulSoup(await resp.text(), "html.parser")
                table_collect = soup_collect.find("table", attrs={"id": "tbl_etat"})
                if table_collect is None:
                    LOGGER.warning("No data table found for %s", type_)
                    return {}

                if not isinstance(table_collect, Tag):
                    LOGGER.warning("Unexpected data table type for %s", type_)
                    return {}

                results_collect = table_collect.find_all("tr")
                LOGGER.debug("%s -> Number of results: %d", type_, len(results_collect))
                result: dict[str, IRegulData] = {}

                for row in results_collect:
                    alias_cell = row.find("td", attrs={"id": "ali_td_tbl_etat"})
                    value_cell = row.find("td", attrs={"id": "val_td_tbl_etat"})
                    unit_cell = row.find("td", attrs={"id": "unit_td_tbl_etat"})

                    if alias_cell is None or value_cell is None or unit_cell is None:
                        LOGGER.debug("Skipping incomplete row for %s", type_)
                        continue

                    alias = alias_cell.get_text(strip=True)
                    identifier = slugify(alias)

                    value = Decimal(value_cell.get_text(strip=True))
                    unit = unit_cell.get_text(strip=True)

                    if unit == "MWh":
                        unit = "KWh"
                        value = value * Decimal(1000)

                    if identifier in result:
                        result[identifier].value = result[identifier].value + value
                    else:
                        result[identifier] = IRegulData(identifier, alias, value, unit)

                return result
        except aiohttp.ClientConnectionError as e:
            raise CannotConnect() from e

    async def defrost(self) -> bool:
        """Trigger defrost operation.

        Returns:
            True if defrost was triggered successfully, False otherwise.

        Raises:
            CannotConnect: If unable to connect to the device.
            InvalidAuth: If authentication fails.
        """
        if not await self.__isauth():
            self._http_session.cookie_jar.clear()
            await self.__connect(True)

        payload = {"SNiregul": self.device_id, "Update": "203"}

        async with self._http_session.post(
            urljoin(self.iregulApiBaseUrl, "includes/processform.php"), data=payload
        ) as resp:
            return await self.__checkreturn(True, str(resp.url))

    async def get_data(self) -> MappedFrame | None:
        """Collect all data from device.

        The legacy HTML tables are parsed and converted into a :class:`MappedFrame`
        so that the return type matches the v2 socket client's
        :meth:`aioiregul.v2.client.IRegulClient.get_data` method.

        Only a subset of fields is available in v1, so the mapped frame
        contains:

        - ``outputs``: Parsed as :class:`Output` instances.
        - ``inputs``: Parsed as :class:`Input` instances.
        - ``analog_sensors``: Parsed from the ``sondes`` page.
        - ``measurements``: Parsed from the ``mesures`` page.

        All other groups (zones, parameters, labels, configuration,
        memory, bus registers) are left empty or ``None``.

        Args:
            refreshMandatory: Whether to enforce refresh rate limits.

        Returns:
            MappedFrame with device data or None if refresh failed.

        Raises:
            CannotConnect: If unable to connect to the device.
            InvalidAuth: If authentication fails.
        """
        if not await self.__isauth():
            self._http_session.cookie_jar.clear()
            await self.__connect(True)

        # First Login and Refresh Datas
        if not await self.__refresh(True):
            return None

        # Collect legacy HTML data
        outputs_raw = await self.__collect("sorties")
        sensors_raw = await self.__collect("sondes")
        inputs_raw = await self.__collect("entrees")
        measures_raw = await self.__collect("mesures")

        # Map to shared typed models
        outputs = {
            i: Output(index=i, valeur=int(data.value), alias=data.name)
            for i, data in enumerate(outputs_raw.values(), start=1)
        }

        inputs = {
            i: Input(index=i, valeur=int(data.value), alias=data.name)
            for i, data in enumerate(inputs_raw.values(), start=1)
        }

        analog_sensors = {
            i: AnalogSensor(index=i, valeur=float(data.value), unit=data.unit, alias=data.name)
            for i, data in enumerate(sensors_raw.values(), start=1)
        }

        measurements = {
            i: Measurement(index=i, valeur=float(data.value), unit=data.unit, alias=data.name)
            for i, data in enumerate(measures_raw.values(), start=1)
        }

        # Build a minimal mapped frame compatible with v2
        return MappedFrame(
            is_old=False,
            timestamp=datetime.now(),
            count=None,
            zones={},
            inputs=inputs,
            outputs=outputs,
            measurements=measurements,
            parameters={},
            labels={},
            modbus_registers={},
            analog_sensors=analog_sensors,
            configuration=None,
            memory=None,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
