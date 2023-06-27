import httpx
import uuid
from dotenv import load_dotenv
import asyncio

from data_models import WatchList, WatchLists, PointList

class MangoClient:
    XSRF_TOKEN = str(uuid.uuid4())
    headers = { "X-XSRF-TOKEN": XSRF_TOKEN }
    cookies = { "XSRF-TOKEN": XSRF_TOKEN }
    
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.client = None
        self.semaphore = asyncio.Semaphore(5)  # Limiting to 5 connections

    async def __aenter__(self):
        return await self.open()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def open(self):
        self.client = httpx.AsyncClient(base_url=self.ip, headers=MangoClient.headers, cookies=MangoClient.cookies)
        await self.post('/rest/latest/login', json={"username": self.username, "password": self.password})
        self.password = None
        return self
    
    async def close(self):
        await self.client.aclose()

    async def get(self, url, **kwargs):
        async with self.semaphore:
            return await self.client.get(url, **kwargs)

    async def post(self, url, **kwargs):
        async with self.semaphore:
            return await self.client.post(url, **kwargs)

    async def watchlists(self):
        r = await self.get('/rest/latest/watch-lists')
        return WatchLists(**r.json())

    async def watchlist(self, xid):
        r = await self.get(f'/rest/latest/watch-lists/{xid}')
        return WatchList(**r.json())

    async def pointquery(self, rql):
        r = await self.get(f'/rest/latest/data-points?{rql}')
        return PointList(**r.json())
