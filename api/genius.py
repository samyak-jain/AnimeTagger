import asyncio
import urllib.parse
from asyncio import Task
from typing import Any, Dict, Optional, List, Tuple
from difflib import SequenceMatcher as SM

from aiohttp import ClientSession

from api import API


class GENIUS(API):
    def __init__(self, token: Optional[str]):
        self.BASE_URL = "https://api.genius.com"

        assert token is not None
        self.SEARCH_URL = f"{self.BASE_URL}/search?access_token={token}"

    def query(self, user_query: str, session: ClientSession) -> Task:
        # print(f"{self.SEARCH_URL}?q={user_query}")
        return asyncio.create_task(self.fetch(f"{self.SEARCH_URL}&q={user_query}", session))

    def album(self, response_list: List[Optional[Dict[str, Any]]], initial_query: str) -> \
            Tuple[int, Optional[str], Optional[str], Optional[str]]:

        song_name: Optional[str] = None
        artists: Optional[str] = None
        album_art: Optional[str] = None
        index: int = -1
        results: List[Tuple[float, int, Optional[str], Optional[str], Optional[str]]] = []

        for response in response_list:
            index += 1
            # print(response)

            # Check for empty response
            if response is None:
                continue

            # Make sure request is successful
            if response["meta"]["status"] != 200:
                continue

            # Make sure that search results are not empty
            if len(response["response"]["hits"]) < 1:
                continue

            for song in response["response"]["hits"]:
                similarity: Optional[float] = None

                if song.get("title") is not None:
                    song_name = song["title"]

                    assert song_name is not None
                    similarity = SM(None, song_name, initial_query).ratio()

                if song.get("primary_artist") is not None and song["primary_artist"].get("name") is not None:
                    artists = song["primary_artist"]["name"]

                if song.get("result") is not None and song["result"].get("header_image_url") is not None:
                    album_art = song["result"]["header_image_url"]

                if song_name is not None and artists is not None and album_art is not None and similarity is not None:
                    results.append((similarity, index, song_name, artists, album_art))

        if len(results) < 1:
            return -1, None, None, None

        print(results)

        final_result = max(results, key=lambda element: element[0])

        return final_result[1:]

    def url_encode(self, url: str) -> str:
        tokens: List[str] = url.split(" ")
        encoded_tokens: List[str] = [urllib.parse.quote(token) for token in tokens]
        return '+'.join(encoded_tokens)
