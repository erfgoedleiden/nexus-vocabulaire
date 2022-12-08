from ssl import SSLContext
from typing import Optional

import requests
import urllib3


class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    """
    Transport adapter that allows us to use custom ssl_context.
    Adapted from https://stackoverflow.com/questions/71603314/ssl-error-unsafe-legacy-renegotiation-disabled
    """

    def __init__(self, ssl_context: Optional[SSLContext] = None, **kwargs: dict):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections: int, maxsize: int, block: bool = False) -> None:
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)
