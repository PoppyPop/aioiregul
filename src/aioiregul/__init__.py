import aiohttp
from urllib.parse import urljoin
from dataclasses import dataclass
from urllib import parse
from bs4 import BeautifulSoup
import asyncio


@dataclass
class ConnectionOptions:
    """IRegul options for connection."""

    username: str
    password: str
    iregul_base_url: str = 'https://vpn.i-regul.com/modules/'


@dataclass
class IRegulData:
    """IRegul data."""

    id: int
    name: str
    value: str
    unit: str


class Device:
    """IRegul device reppresentation."""

    options: ConnectionOptions
    login_url: str
    iregulApiBaseUrl: str

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

    async def __connect(self, http_session: aiohttp.ClientSession) -> bool:
        payload = {
            'sublogin': '1',
            'user': self.options.username,
            'pass': self.options.password
        }

        async with http_session.post(self.login_url, data=payload) as resp:
            result_text = await resp.text()
            soup_login = BeautifulSoup(result_text, 'html.parser')
            table_login = soup_login.find('div', attrs={'id': 'btn_i-regul'})
            if table_login != None:
                print('Login Ok')
                return True

            print('Login Ko')
            return False

    async def __refresh(self, http_session: aiohttp.ClientSession) -> bool:
        payload = {
            'SNiregul': self.options.username,
            'Update': 'etat',
            'EtatSel': '1'
        }

        async with http_session.post(urljoin(self.iregulApiBaseUrl, 'includes/processform.php'), data=payload) as resp:
            # data_upd_result = await resp.text()
            # print(resp.get)
            data_upd_dict = dict(parse.parse_qsl(
                parse.urlsplit(str(resp.url)).query))
            data_upd_cmd = data_upd_dict.get('CMD', None)

            if (data_upd_cmd == None or data_upd_cmd != 'Success'):
                print('Update Ko')
                return False

            print('Update Ok')
            return True

    async def __collect(self, http_session: aiohttp.ClientSession, type: str):
        # Collect data
        async with http_session.get(urljoin(self.iregulApiBaseUrl, 'index-Etat.php?Etat=' + type)) as resp:
            soup_collect = BeautifulSoup(await resp.text(), 'html.parser')
            table_collect = soup_collect.find(
                'table', attrs={'id': 'tbl_etat'})
            results_collect = table_collect.find_all('tr')
            print(type, '-> Number of results', len(results_collect))
            result = []

            for i in results_collect:

                sId = i.find(
                    'td', attrs={'id': 'id_td_tbl_etat'}).getText().strip()
                sAli = i.find(
                    'td', attrs={'id': 'ali_td_tbl_etat'}).getText().strip()
                sVal = i.find(
                    'td', attrs={'id': 'val_td_tbl_etat'}).getText().strip()
                sUnit = i.find(
                    'td', attrs={'id': 'unit_td_tbl_etat'}).getText().strip()

                result.append(IRegulData(sId, sAli, sVal, sUnit))

            return result

    async def authenticate(self) -> bool:
        async with aiohttp.ClientSession() as session:
            return await self.__connect(session)

    async def collect(self):
        # First Login and Refresh Datas
        async with aiohttp.ClientSession() as session:
            if await self.__connect(session) and await self.__refresh(session):
                # Collect datas
                result = {}
                result['outputs'] = await self.__collect(session, 'sorties')
                result['sensors'] = await self.__collect(session, 'sondes')
                result['inputs'] = await self.__collect(session, 'entrees')
                result['measures'] = await self.__collect(session, 'mesures')

                return result
