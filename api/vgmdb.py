import asyncio
import urllib.parse
from asyncio import Task
from typing import List, Optional, Dict, Any, Tuple

import requests
from aiohttp import ClientSession
from api import API
from models import Song


class VGMDB(API):
    def __init__(self):
        self.BASE_URL = "https://vgmdb.info"
        self.SEARCH_URL = f"{self.BASE_URL}/search"

    def query(self, user_query: str, session: ClientSession) -> Task:
        return asyncio.create_task(self.fetch(f"{self.SEARCH_URL}/{user_query}?format=json", session))

    def album(self, response_list: List[Optional[Dict[str, Any]]], initial_query: str) -> \
            Tuple[int, Optional[Song]]:

        song_name: Optional[str] = None
        artists: Optional[str] = None
        album_art: Optional[str] = None
        album_name: Optional[str] = None
        index: int = -1

        for search_result in response_list:
            index += 1
            if search_result is None:
                continue

            albums: List[Dict[str, Any]] = search_result["results"]["albums"]

            if len(albums) < 1:
                continue

            for album in albums:
                album_code: str = album["link"]
                album_details: Dict[str, Any] = requests.get(f"{self.BASE_URL}/{album_code}?format=json").json()
                album_art = album_details["picture_full"]
                album_name = album_details["name"]

                if album_name is None:
                    continue

                # Ignore albums with no album art or track listings
                assert album_art is not None and len(album_art) > 0 and album_details["discs"] is not None
                if "nocover" in album_art or len(album_details["discs"]) < 1:
                    continue

                track_names: List[Dict[str, Any]] = [track["names"] for track in album_details["discs"][0]["tracks"]]

                # If english name exists, make that the song name
                romaji_existed: bool = False
                for track in track_names:
                    romaji_name: Optional[str] = track.get("Romaji")

                    if romaji_name is not None:
                        romaji_existed = True
                        song_name = romaji_name
                        break

                    english_name: Optional[str] = track.get("English")

                    if english_name is not None:
                        romaji_existed = True
                        song_name = english_name
                        break

                # Else make the japanese name as the title of the song
                if not romaji_existed:
                    song_name = track_names[0]["Japanese"]

                performers: List[Dict[str, Any]] = album_details["performers"]
                artist_list: List[str] = []

                for performer in performers:
                    names: Dict[str, str] = performer["names"]
                    english_name = names.get("en")

                    # Add japanese name if there is no english name for the artist
                    if english_name is None:
                        name = names["ja"]
                    else:
                        name = english_name

                    artist_list.append(name)

                artists = ", ".join(artist_list)

                break

        if song_name is None or artists is None or album_name is None:
            return 0, None

        return index, Song(song_name=song_name, artists=artists, album_art=album_art, album_name=album_name)

    def url_encode(self, url: str) -> str:
        return urllib.parse.quote(url)
