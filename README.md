# IRegulScrapper

## Asynchronous library to get data from Iregul systems

## This library is under development.

Requires Python 3 and uses asyncio, aiohttp and BeautifulSoup4.

```python
import iregul 
import aiohttp
import asyncio

async def main():
    opt = iregul.ConnectionOptions(username='User', password='Pass')
    async with aiohttp.ClientSession() as session:
        dev = iregul.Device(session, opt)

        res = await dev.collect()

        print(res)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```
