from abc import ABC, abstractmethod
from asyncio import Task
from typing import Optional, Dict, Any, List, Tuple

from aiohttp import ClientSession, client_exceptions
from tenacity import stop_after_attempt, retry
from models import Song


class API(ABC):
    @staticmethod
    @retry(stop=stop_after_attempt(2))
    async def fetch(url: str, session: ClientSession) -> Optional[Dict[str, Any]]:
        try:
            async with session.get(url) as response:
                return await response.json()
        except client_exceptions.ContentTypeError as exception:
            print(f"Bad Url: {url}")
            print(exception)

            return None

    @abstractmethod
    def query(self, user_query: str, session: ClientSession) -> Task:
        pass

    @abstractmethod
    def album(self, response_list: List[Optional[Dict[str, Any]]], initial_query: str) -> \
            Tuple[int, Optional[Song]]:
        pass

    @abstractmethod
    def url_encode(self, url: str) -> str:
        pass
