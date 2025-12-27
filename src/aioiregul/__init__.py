import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from urllib import parse
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from slugify import slugify

LOGGER = logging.getLogger(__package__)


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
    """IRegul device reppresentation."""

    options: ConnectionOptions
    login_url: str
    iregulApiBaseUrl: str
    lastupdate: datetime = None

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
        except aiohttp.ClientConnectionError:
            raise CannotConnect() from None

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
                else:
                    return False
        except aiohttp.ClientConnectionError:
            raise CannotConnect() from None

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
                urljoin(self.iregulApiBaseUrl, "includes/processform.php"), data=payload
            ) as resp:
                return await self.__checkreturn(refreshMandatory, resp.url)

        except aiohttp.ClientConnectionError:
            raise CannotConnect() from None

    async def __checkreturn(self, refreshMandatory: bool, url: str) -> bool:
        data_upd_dict = dict(parse.parse_qsl(parse.urlsplit(str(url)).query))
        data_upd_cmd = data_upd_dict.get("CMD")

        if data_upd_cmd is None or data_upd_cmd != "Success":
            if refreshMandatory:
                LOGGER.error("Update Ko")
                return False
            else:
                # We don't care if it has worked or not
                LOGGER.debug("Update Ko")
                return True

        LOGGER.debug("Update Ok")
        return True

    async def __collect(self, http_session: aiohttp.ClientSession, type: str):
        # Collect data
        try:
            async with http_session.get(
                urljoin(self.iregulApiBaseUrl, "index-Etat.php?Etat=" + type)
            ) as resp:
                soup_collect = BeautifulSoup(await resp.text(), "html.parser")
                table_collect = soup_collect.find("table", attrs={"id": "tbl_etat"})
                results_collect = table_collect.find_all("tr")
                LOGGER.debug(type, "-> Number of results", len(results_collect))
                result = {}

                for i in results_collect:
                    sAli = i.find("td", attrs={"id": "ali_td_tbl_etat"}).getText().strip()
                    sId = slugify(sAli)

                    # sId = i.find(
                    #    'td', attrs={'id': 'id_td_tbl_etat'}).getText().strip()
                    sVal = Decimal(i.find("td", attrs={"id": "val_td_tbl_etat"}).getText().strip())
                    sUnit = i.find("td", attrs={"id": "unit_td_tbl_etat"}).getText().strip()

                    # Transform MWH to KWh
                    if sUnit == "MWh":
                        sUnit = "KWh"
                        sVal = sVal * Decimal(1000)

                    # Check for duplicate
                    if sId in result:
                        # Duplicate
                        result[sId].value = result[sId].value + sVal
                    else:
                        result[sId] = IRegulData(sId, sAli, sVal, sUnit)

                return result
        except aiohttp.ClientConnectionError:
            raise CannotConnect() from None

    async def isauth(self, http_session: aiohttp.ClientSession) -> bool:
        return await self.__isauth(http_session)

    async def authenticate(self, http_session: aiohttp.ClientSession) -> bool:
        return await self.__connect(http_session, False)

    async def defrost(self, http_session: aiohttp.ClientSession) -> bool:
        if not await self.__isauth(http_session):
            http_session.cookie_jar.clear()
            await self.__connect(http_session, True)

        payload = {"SNiregul": self.options.username, "Update": "203"}

        async with http_session.post(
            urljoin(self.iregulApiBaseUrl, "includes/processform.php"), data=payload
        ) as resp:
            return await self.__checkreturn(True, resp.url)

    async def collect(self, http_session: aiohttp.ClientSession, refreshMandatory: bool = True):
        if not await self.__isauth(http_session):
            http_session.cookie_jar.clear()
            await self.__connect(http_session, True)

        # First Login and Refresh Datas
        if await self.__refresh(http_session, refreshMandatory):
            # Collect datas
            result = {}
            result["outputs"] = await self.__collect(http_session, "sorties")
            result["sensors"] = await self.__collect(http_session, "sondes")
            result["inputs"] = await self.__collect(http_session, "entrees")
            result["measures"] = await self.__collect(http_session, "mesures")

            return result


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
