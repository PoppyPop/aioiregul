"""IRegul v1 API - Legacy HTTP-based API client.

This module provides HTTP-based communication with IRegul devices through
the web interface using BeautifulSoup for HTML parsing.

Key Components:
- Device: Main HTTP client for device communication
- ConnectionOptions: Configuration for device connection
- IRegulData: Data container for measured values
- Exceptions: CannotConnect, InvalidAuth
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from urllib import parse
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup, Tag
from slugify import slugify

from ..models import AnalogSensor, Input, MappedFrame, Measurement, Output

LOGGER = logging.getLogger(__name__)


@dataclass
class ConnectionOptions:
    """IRegul options for connection."""

    username: str
    password: str
    iregul_base_url: str = "https://vpn.i-regul.com/modules/"
    refresh_rate: timedelta = timedelta(minutes=5)


@dataclass
class IRegulData:
    """IRegul data."""

    id: str
    name: str
    value: Decimal
    unit: str


class Device:
    """IRegul device representation."""

    options: ConnectionOptions
    login_url: str
    iregulApiBaseUrl: str
    lastupdate: datetime | None = None

    def __init__(
        self,
        options: ConnectionOptions,
    ):
        """Device init."""
        self.options = options

        self.main_url = urljoin(self.options.iregul_base_url, "login/main.php")
        self.login_url = urljoin(self.options.iregul_base_url, "login/process.php")
        self.iregulApiBaseUrl = urljoin(self.options.iregul_base_url, "i-regul/")

    async def __isauth(self, http_session: aiohttp.ClientSession) -> bool:
        try:
            async with http_session.get(self.main_url) as resp:
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

    async def __connect(self, http_session: aiohttp.ClientSession, throwException: bool) -> bool:
        payload = {
            "sublogin": "1",
            "user": self.options.username,
            "pass": self.options.password,
        }

        try:
            async with http_session.post(self.login_url, data=payload) as resp:
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

    async def __refresh(self, http_session: aiohttp.ClientSession, refreshMandatory: bool) -> bool:
        payload = {"SNiregul": self.options.username, "Update": "etat", "EtatSel": "1"}

        # Refresh rate limit
        if self.lastupdate is None:
            # First pass
            self.lastupdate = datetime.now()
            return True

        if datetime.now() - self.lastupdate < self.options.refresh_rate:
            LOGGER.info("Too short, refresh not required")
            return True

        LOGGER.info("Last refresh: %s", self.lastupdate)
        self.lastupdate = datetime.now()

        try:
            async with http_session.post(
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

    async def __collect(
        self, http_session: aiohttp.ClientSession, type_: str
    ) -> dict[str, IRegulData]:
        """Collect data from device."""
        try:
            async with http_session.get(
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

    async def isauth(self, http_session: aiohttp.ClientSession) -> bool:
        """Check if authenticated."""
        return await self.__isauth(http_session)

    async def authenticate(self, http_session: aiohttp.ClientSession) -> bool:
        """Authenticate with device."""
        return await self.__connect(http_session, False)

    async def defrost(self, http_session: aiohttp.ClientSession) -> bool:
        """Trigger defrost operation."""
        if not await self.__isauth(http_session):
            http_session.cookie_jar.clear()
            await self.__connect(http_session, True)

        payload = {"SNiregul": self.options.username, "Update": "203"}

        async with http_session.post(
            urljoin(self.iregulApiBaseUrl, "includes/processform.php"), data=payload
        ) as resp:
            return await self.__checkreturn(True, str(resp.url))

    async def collect(
        self, http_session: aiohttp.ClientSession, refreshMandatory: bool = True
    ) -> MappedFrame | None:
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
        """
        if not await self.__isauth(http_session):
            http_session.cookie_jar.clear()
            await self.__connect(http_session, True)

        # First Login and Refresh Datas
        if not await self.__refresh(http_session, refreshMandatory):
            return None

        # Collect legacy HTML data
        outputs_raw = await self.__collect(http_session, "sorties")
        sensors_raw = await self.__collect(http_session, "sondes")
        inputs_raw = await self.__collect(http_session, "entrees")
        measures_raw = await self.__collect(http_session, "mesures")

        # Map to shared typed models
        outputs = [
            Output(index=i, valeur=int(data.value), alias=data.name)
            for i, data in enumerate(outputs_raw.values(), start=1)
        ]

        inputs = [
            Input(index=i, valeur=int(data.value), alias=data.name)
            for i, data in enumerate(inputs_raw.values(), start=1)
        ]

        analog_sensors = [
            AnalogSensor(index=i, valeur=float(data.value), unit=data.unit, alias=data.name)
            for i, data in enumerate(sensors_raw.values(), start=1)
        ]

        measurements = [
            Measurement(index=i, valeur=float(data.value), unit=data.unit, alias=data.name)
            for i, data in enumerate(measures_raw.values(), start=1)
        ]

        # Build a minimal mapped frame compatible with v2
        return MappedFrame(
            is_old=False,
            timestamp=datetime.now(),
            count=None,
            zones=[],
            inputs=inputs,
            outputs=outputs,
            measurements=measurements,
            parameters=[],
            labels=[],
            modbus_registers=[],
            analog_sensors=analog_sensors,
            configuration=None,
            memory=None,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
