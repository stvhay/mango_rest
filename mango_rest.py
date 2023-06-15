import httpx
import uuid
from dotenv import load_dotenv

from data_models import WatchList, WatchLists, PointList

class MangoClient:
    XSRF_TOKEN = str(uuid.uuid4())
    headers = { "X-XSRF-TOKEN": XSRF_TOKEN }
    cookies= { "XSRF-TOKEN": XSRF_TOKEN }
    
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.client = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        self.client = httpx.Client(base_url=self.ip, headers=MangoClient.headers, cookies=MangoClient.cookies)
        self.post('/rest/latest/login', json={"username": self.username, "password": self.password})
        self.password = None
        return self
    
    def close(self):
        self.client.close()

    def get(self, url, **kwargs):
        return self.client.get(url, **kwargs)

    def post(self, url, **kwargs):
        return self.client.post(url, **kwargs)

    def watchlists(self):
        r = self.client.get('/rest/latest/watch-lists')
        return WatchLists(**r.json())

    def watchlist(self, xid):
        r = self.client.get(f'/rest/latest/watch-lists/{xid}')
        return WatchList(**r.json())

    def pointquery(self, rql):
        r = self.client.get(f'/rest/latest/data-points?{rql}')
        return PointList(**r.json())
