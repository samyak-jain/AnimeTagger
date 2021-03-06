import asyncio
import urllib.parse
from asyncio import Task
from typing import Any, Dict, Optional, List, Tuple

import requests
from aiohttp import ClientSession

from api import API
from models import Song
from utils.text_processing import clean_string, calculate_similarity


class GENIUS(API):
    def __init__(self, token: Optional[str]):
        self.token = token
        self.BASE_URL = "https://api.genius.com"

        assert self.token is not None
        self.SEARCH_URL = f"{self.BASE_URL}/search?access_token={self.token}"

    def get_song_url(self, api):
        return f"{self.BASE_URL}{api}?access_token={self.token}"

    def query(self, user_query: str, session: ClientSession) -> Task:
        return asyncio.create_task(self.fetch(f"{self.SEARCH_URL}&q={user_query}", session))

    def album(self, response_list: List[Optional[Dict[str, Any]]], initial_query: str, best_similarity: float) \
            -> Tuple[float, Optional[Song]]:

        song_name: Optional[str] = None
        artists: Optional[str] = None
        album_art: Optional[str] = None
        album_name: Optional[str] = None
        index: int = -1
        results: List[Tuple[float, Optional[str], Optional[str], Optional[str]]] = []

        for response in response_list:
            index += 1

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

                if song.get("result") is None:
                    continue

                song_result: Dict[str, Any] = song["result"]

                if song_result.get("api_path") is not None:
                    print(song_result.get("title"))
                    print(song_result["api_path"])
                    api_path = song_result["api_path"]
                    api_result: Dict[str, Any] = requests.get(self.get_song_url(api_path)).json()
                    if api_result is None:
                        continue

                    if api_result["meta"]["status"] != 200:
                        continue

                    try:
                        if api_result["response"]["song"]["album"]["name"] is not None:
                            album_name = api_result["response"]["song"]["album"]["name"]
                        else:
                            continue
                    except (KeyError, TypeError):
                        continue

                if song_result.get("title") is not None:
                    song_name = song_result["title"]

                    assert song_name is not None
                    similarity = calculate_similarity(song_name, initial_query)

                    assert similarity is not None
                    if similarity < best_similarity:
                        continue

                if song_result.get("primary_artist") is not None and \
                        song_result["primary_artist"].get("name") is not None:
                    artists = song_result["primary_artist"]["name"]

                    if 'genius' in clean_string(artists) or 'eddie van der meer' in clean_string(artists):
                        continue

                if song_result.get("header_image_url") is not None:
                    album_art = song_result["header_image_url"]

                if song_name is not None and artists is not None and album_art is not None and similarity is not None:
                    results.append((similarity, song_name, artists, album_art))

        if len(results) < 1:
            return 0, None

        final_result = max(results, key=lambda element: element[0])
        final_song_name, final_artists, final_album_art = final_result[1:]
        return final_result[0], Song(song_name=final_song_name, artists=final_artists, album_art=final_album_art,
                                     album_name=album_name)

    def url_encode(self, url: str) -> str:
        tokens: List[str] = url.split(" ")
        encoded_tokens: List[str] = [urllib.parse.quote(token) for token in tokens]
        return '+'.join(encoded_tokens)
