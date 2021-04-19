import aiohttp
from urllib.parse import urljoin
from dataclasses import dataclass
from urllib import parse
from bs4 import BeautifulSoup
from slugify import slugify
from datetime import datetime, timedelta


@dataclass
class ConnectionOptions:
    """IRegul options for connection."""

    username: str
    password: str
    iregul_base_url: str = 'https://vpn.i-regul.com/modules/'
    refresh_rate: timedelta = timedelta(minutes=1)

@dataclass
class IRegulData:
    """IRegul data."""

    id: str
    name: str
    value: str
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

        self.login_url = urljoin(
            self.options.iregul_base_url, 'login/process.php')
        self.iregulApiBaseUrl = urljoin(
            self.options.iregul_base_url, 'i-regul/')

    async def __connect(self, http_session: aiohttp.ClientSession, throwException: bool) -> bool:
        payload = {
            'sublogin': '1',
            'user': self.options.username,
            'pass': self.options.password
        }

        try:
            async with http_session.post(self.login_url, data=payload) as resp:
                result_text = await resp.text()
                soup_login = BeautifulSoup(result_text, 'html.parser')
                table_login = soup_login.find(
                    'div', attrs={'id': 'btn_i-regul'})
                if table_login != None:
                    print('Login Ok')
                    return True

                print('Login Ko')
                if (throwException):
                    raise InvalidAuth()
                else:
                    return False
        except aiohttp.ClientConnectionError:
            raise CannotConnect()

    async def __refresh(self, http_session: aiohttp.ClientSession, throwException: bool) -> bool:
        payload = {
            'SNiregul': self.options.username,
            'Update': 'etat',
            'EtatSel': '1'
        }

        # Refresh rate limit
        if (self.lastupdate == None):
            # First pass
            self.lastupdate = datetime.now()
            return True

        if (datetime.now() - self.lastupdate < self.options.refresh_rate):
            print('Too short, refresh not required')
            return True

        print('Last refresh: ', self.lastupdate)
        self.lastupdate = datetime.now()

        try:
            async with http_session.post(urljoin(self.iregulApiBaseUrl, 'includes/processform.php'), data=payload) as resp:
                # data_upd_result = await resp.text()
                # print(resp.get)
                data_upd_dict = dict(parse.parse_qsl(
                    parse.urlsplit(str(resp.url)).query))
                data_upd_cmd = data_upd_dict.get('CMD', None)

                if (data_upd_cmd == None or data_upd_cmd != 'Success'):
                    print('Update Ko')
                    if (throwException):
                        raise CannotConnect()
                    else:
                        return False

                print('Update Ok')
                return True
        except aiohttp.ClientConnectionError:
            raise CannotConnect()

    async def __collect(self, http_session: aiohttp.ClientSession, type: str):
        # Collect data
        try:
            async with http_session.get(urljoin(self.iregulApiBaseUrl, 'index-Etat.php?Etat=' + type)) as resp:
                soup_collect = BeautifulSoup(await resp.text(), 'html.parser')
                table_collect = soup_collect.find(
                    'table', attrs={'id': 'tbl_etat'})
                results_collect = table_collect.find_all('tr')
                print(type, '-> Number of results', len(results_collect))
                result = {}

                for i in results_collect:

                    sId = i.find(
                        'td', attrs={'id': 'id_td_tbl_etat'}).getText().strip()
                    sAli = i.find(
                        'td', attrs={'id': 'ali_td_tbl_etat'}).getText().strip()
                    sVal = i.find(
                        'td', attrs={'id': 'val_td_tbl_etat'}).getText().strip()
                    sUnit = i.find(
                        'td', attrs={'id': 'unit_td_tbl_etat'}).getText().strip()

                    sId = slugify(sId + "-" + sAli)

                    result[sId] = IRegulData(sId, sAli, sVal, sUnit)

                return result
        except aiohttp.ClientConnectionError:
            raise CannotConnect()

    async def authenticate(self) -> bool:
        async with aiohttp.ClientSession() as session:
            return await self.__connect(session, False)

    async def collect(self):
        # First Login and Refresh Datas
        async with aiohttp.ClientSession() as session:
            if await self.__connect(session, True) and await self.__refresh(session, True):
                # Collect datas
                result = {}
                result['outputs'] = await self.__collect(session, 'sorties')
                result['sensors'] = await self.__collect(session, 'sondes')
                result['inputs'] = await self.__collect(session, 'entrees')
                result['measures'] = await self.__collect(session, 'mesures')

                return result


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
