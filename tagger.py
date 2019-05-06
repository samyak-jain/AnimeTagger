import asyncio
import glob
import os
import subprocess
import sys
from asyncio.tasks import Task
from pathlib import Path
from shutil import rmtree
from typing import Dict, List, Any, Optional, Union, Tuple

import eyed3
from aiohttp import ClientSession
from dotenv import load_dotenv
from eyed3.id3 import TagFile
from eyed3.mp3 import Mp3AudioFile
from tqdm import tqdm

from api import API
from api.acoustid import ACOUSTID
from api.genius import GENIUS
from api.vgmdb import VGMDB
from models import Song
from utils.image_handler import download_image
from utils.text_processing import clean_string, remove_slashes, detect_language

ALBUM_DIR = "albums"


async def query_databases(initial_query: str, query_list: List[List[str]], query_api: API) \
        -> Optional[Tuple[int, Optional[Song]]]:

    def filter_criteria(query: str) -> bool:
        tokens: List[str] = query.split(" ")
        return not all(len(token) < 3 for token in tokens)

    def remove_empty(query: str) -> str:
        tokens: List[str] = query.split(" ")
        return ' '.join([token for token in tokens if len(token) > 0])

    concatenated_query_list: List[str] = [' '.join(query) for query in query_list]
    filtered_query_list: List[str] = [remove_empty(query) for query in concatenated_query_list if
                                      filter_criteria(query)]
    parsed_query_list: List[str] = [query_api.url_encode(query) for query in filtered_query_list]

    if len(parsed_query_list) == 0:
        return None

    tasks: List[Task] = []
    async with ClientSession() as session:
        for query in parsed_query_list:
            task: Task = query_api.query(query, session)
            tasks.append(task)

        response_list: List[Optional[Dict[str, Any]]] = await asyncio.gather(*tasks)

        index, song = query_api.album(response_list, initial_query)
        query_length: int = len(parsed_query_list[index])

        if song is None:
            return None

        if (song.song_name is None) or (song.artists is None) or (song.album_name is None):
            return None

        return query_length, song


def get_all_possible_subs(query: List[str], length: int) -> List[List[str]]:
    subs: List[List[str]] = []
    query_length: int = len(query)

    assert query_length >= length
    for start_index in range(query_length - length + 1):
        subs.append(query[start_index:start_index + length])

    return subs


def construct_query(query: str, api_list: List[API]) -> Optional[Song]:
    cleaned_query: str = clean_string(query)
    filtered_query: List[str] = [token for token in cleaned_query.split(" ") if len(token) > 0]

    longest_query: List[List[str]] = [filtered_query]
    initial_length: int = len(filtered_query)

    for length in tqdm(range(initial_length - 1, -1, -1)):
        query_lengths: List[Union[int, float]] = [-1]*len(api_list)
        results: List[Optional[Song]] = []

        for pos, api_tag in enumerate(api_list):
            async_result = asyncio.run(query_databases(query, longest_query, api_tag))

            if async_result is not None:
                query_len, result = async_result
                results.append(result)

                if result is not None:
                    query_lengths[pos] = query_len
            else:
                results.append(None)

        longest_query = get_all_possible_subs(filtered_query, length)

        if all(element == -1 for element in query_lengths):
            continue

        def max_criteria(element: Optional[int]) -> Union[int, float]:
            if element is None:
                return -1

            return query_lengths[element]

        max_index: int = max(range(len(query_lengths)), key=max_criteria)
        final_result: Optional[Song] = results[max_index]

        if final_result is not None:
            return final_result

    return None


def tag_song(path: Path, song: str, api_list: List[API]):
    audio_file: Union[Mp3AudioFile, TagFile, None] = eyed3.load(str(path / song))
    assert audio_file is not None
    if isinstance(audio_file, TagFile):
        raise TypeError("Invalid Data Format")

    metadata: Optional[Song] = None
    title: Optional[str] = audio_file.tag.title

    # Use acoustid to get details
    acoust_api_key: str = os.getenv("AC_KEY")
    fingerprint: ACOUSTID = ACOUSTID(path / song, acoust_api_key)
    fingerprint_result: Optional[Dict[str, Union[str, float]]] = fingerprint.inference()
    fingerprint_success: bool = False
    fingerprint_title: Optional[str] = None
    fingerprint_artist: Optional[str] = None

    file_base: Union[bytes, str] = os.path.splitext(song)[0]
    try:
        file_name = file_base.decode("utf-8")
    except AttributeError:
        file_name = file_base

    if fingerprint_result is not None:
        fingerprint_success = True
        fingerprint_title = fingerprint_result["title"]
        fingerprint_artist = fingerprint_result["artist"]

    possibilities: List[Optional[str]] = []
    title_lang: Optional[int] = detect_language(title)
    name_lang: Optional[int] = detect_language(file_name)

    to_be_added: List[str] = [title, file_name]
    if title_lang is not None and name_lang is not None:
        if title_lang <= name_lang:
            possibilities.extend(to_be_added)
        else:
            possibilities.extend(to_be_added[::-1])
    else:
        possibilities.extend(to_be_added)

    for possibility in possibilities:
        if possibility is None:
            continue

        metadata = construct_query(possibility, api_list)

        if metadata is not None:
            break

    if metadata is None:
        print(f"Cannot tag file {song}")
        return

    if fingerprint_success:
        assert fingerprint_artist is not None and fingerprint_title is not None
        audio_file.tag.title = fingerprint_title
        audio_file.tag.artists = fingerprint_artist
    else:
        audio_file.tag.title = metadata.song_name
        audio_file.tag.artists = metadata.artists

    audio_file.tag.album = metadata.album_name

    os.makedirs(ALBUM_DIR, exist_ok=True)
    img_path: str = f"{ALBUM_DIR}/{remove_slashes(audio_file.tag.title)}.jpg"

    if metadata.album_art is not None:
        download_image(metadata.album_art, img_path)

        # To suppress output of lame command
        with open(os.devnull, 'wb') as DEVNULL:
            subprocess.run(["lame", "--ti", img_path, str(path / song)], stdout=DEVNULL, stderr=subprocess.STDOUT)

        rmtree(ALBUM_DIR)

    # Rename the file so that it matches the title
    os.rename(str(path / song), str(path / f"{remove_slashes(audio_file.tag.title)}.mp3"))

    # Remove old files
    for file_to_remove in glob.glob(str(path_name) + "/*.mp3.mp3"):
        os.remove(file_to_remove)

    final_metadata: Dict[str, Optional[str]] = {
        'song': audio_file.tag.title,
        'album': audio_file.tag.album,
        'artist': audio_file.tag.artists,
        'album art': metadata.album_art
    }
    print(f"{song} will now have the metadata: {final_metadata}")


if __name__ == "__main__":
    load_dotenv()
    # path_name: Union[Path, Any] = Path("/home/samyak/music_test")
    path_name: Union[Path, Any] = Path(sys.argv[1])
    API_LIST: List[API] = [VGMDB(), GENIUS(os.getenv("GENIUS_TOKEN"))]

    assert isinstance(path_name, Path)
    files = os.listdir(str(path_name))
    for file in files:
        print(f"{file} is being processed")
        tag_song(path_name, file, API_LIST)
