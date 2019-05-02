from asyncio.tasks import Task
from shutil import rmtree
import subprocess
import eyed3
from eyed3.id3 import TagFile
from eyed3.mp3 import Mp3AudioFile
from tenacity import retry, stop_after_attempt
import requests
import asyncio
from aiohttp import ClientSession, client_exceptions
import urllib.parse
import urllib.request
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import os
from tqdm import tqdm
import string
import re

BASE_URL = "https://vgmdb.info"
SEARCH_URL = f"{BASE_URL}/search"
ALBUM_DIR = "~/albums"


@retry(stop=stop_after_attempt(2))
async def fetch(url: str, session: ClientSession) -> Optional[Dict[str, Any]]:
    try:
        async with session.get(url) as response:
            return await response.json()
    except client_exceptions.ContentTypeError as exception:
        print(f"Bad Url: {url}")
        print(exception)

        return None


async def query_vgmdb(query_list: List[List[str]]) -> Optional[Dict[str, Optional[str]]]:
    song_name: Optional[str] = None
    artists: Optional[str] = None
    album_art: Optional[str] = None

    def filter_criteria(query: str) -> bool:
        tokens: List[str] = query.split(" ")
        return not all(len(token) < 3 for token in tokens)

    def remove_empty(query: str) -> str:
        tokens: List[str] = query.split(" ")
        return ' '.join([token for token in tokens if len(token) > 0])

    concatenated_query_list: List[str] = [' '.join(query) for query in query_list]
    filtered_query_list: List[str] = [remove_empty(query) for query in concatenated_query_list if
                                      filter_criteria(query)]
    parsed_query_list: List[str] = [urllib.parse.quote(query) for query in filtered_query_list]

    if len(parsed_query_list) == 0:
        return None

    tasks: List[Task] = []
    async with ClientSession() as session:
        for query in parsed_query_list:
            task: Task = asyncio.create_task(fetch(f"{SEARCH_URL}/{query}?format=json", session))
            tasks.append(task)

        response_list: List[Optional[Dict[str, Any]]] = await asyncio.gather(*tasks)

    for search_result in response_list:
        if search_result is None:
            continue

        albums: List[Dict[str, Any]] = search_result["results"]["albums"]

        if len(albums) < 1:
            continue

        for album in albums:
            album_code: str = album["link"]
            album_details: Dict[str, Any] = requests.get(f"{BASE_URL}/{album_code}?format=json").json()
            album_art = album_details["picture_full"]

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

        if (song_name is None) or (artists is None) or (album_art is None):
            return None

        return {
            "Name": song_name,
            "Artists": artists,
            "Album Art": album_art
        }

    return None


def get_all_possible_subs(query: List[str], length: int) -> List[List[str]]:
    subs: List[List[str]] = []
    query_length: int = len(query)

    assert query_length >= length
    for start_index in range(query_length - length):
        subs.append(query[start_index:start_index + length])

    return subs


def construct_query(query: str) -> Optional[Dict[str, Optional[str]]]:
    query_without_punc: str = re.sub('[%s]' % re.escape(string.punctuation), ' ', query)
    filtered_query: List[str] = [token for token in query_without_punc.split(" ") if len(token) > 0]

    def sort_criteria(element: Optional[str]) -> int:
        assert element is not None
        return len(element)

    sorted_query: List[str] = sorted(filtered_query, key=sort_criteria, reverse=True)
    longest_query: List[List[str]] = [sorted_query]
    initial_length: int = len(sorted_query)

    for length in tqdm(range(initial_length - 1, -1, -1)):
        result: Optional[Dict[str, Optional[str]]] = asyncio.run(query_vgmdb(longest_query))

        if result is not None:
            return result

        longest_query = get_all_possible_subs(sorted_query, length)

    return None


def tag_song(path: Path, song: str):
    audio_file: Union[Mp3AudioFile, TagFile, None] = eyed3.load(str(path / song))
    assert audio_file is not None
    if isinstance(audio_file, TagFile):
        raise TypeError("Invalid Data Format")

    metadata: Optional[Dict[str, Optional[str]]] = None
    title: Optional[str] = audio_file.tag.title

    # Check if metadata already exists
    if title is not None:
        metadata = construct_query(title)

    if title is None or metadata is None:
        file_base: Union[bytes, str] = os.path.splitext(song)[0]
        try:
            file_name = file_base.decode("utf-8")
        except AttributeError:
            file_name = file_base

        metadata = construct_query(file_name)

        if metadata is None:
            print(f"Cannot tag file {song}")
            return

    assert metadata["Name"] is not None

    audio_file.tag.title = metadata["Name"]
    audio_file.tag.artists = metadata["Artists"]

    os.makedirs(ALBUM_DIR, exist_ok=True)
    img_path: str = f"{ALBUM_DIR}/{audio_file.tag.title}"

    assert metadata["Album Art"] is not None
    urllib.request.urlretrieve(metadata["Album Art"], img_path)
    subprocess.run(["lame", "--ti", img_path, str(path / song)])
    rmtree(ALBUM_DIR)

    # Rename the file so that it matches the title
    os.rename(str(path / f"{song}.mp3"), str(path / f"{audio_file.tag.title}.mp3"))

    # Remove the old file
    os.remove(str(path / song))

    print(f"{song} will now have the metadata: {metadata}")


if __name__ == "__main__":
    path_name: Union[Path, Any] = Path("/home/samyak/music_test")

    assert isinstance(path_name, Path)
    files = os.listdir(str(path_name))
    for file in files:
        print(f"{file} is being processed")
        tag_song(path_name, file)
