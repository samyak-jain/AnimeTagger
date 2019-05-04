import asyncio
import os
import subprocess
from asyncio.tasks import Task
from pathlib import Path
from shutil import rmtree
from typing import Dict, List, Any, Optional, Union, Tuple

import eyed3
import glob
from aiohttp import ClientSession
from dotenv import load_dotenv
from eyed3.id3 import TagFile
from eyed3.mp3 import Mp3AudioFile
from tqdm import tqdm

from api import API
from api.genius import GENIUS
from api.vgmdb import VGMDB
from utils.clean_text import clean_string, remove_slashes
from utils.image_handler import download_image
from models import Song

ALBUM_DIR = "albums"


async def query_databases(initial_query: str, query_list: List[List[str]], query_api: API) \
        -> Optional[Tuple[int, Dict[str, str]]]:

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

        index, song_name, artists, album_art = query_api.album(response_list, initial_query)
        query_length: int = len(parsed_query_list[index])

        if (song_name is None) or (artists is None) or (album_art is None):
            return None

        return query_length, {
            "Name": song_name,
            "Artists": artists,
            "Album Art": album_art
        }


def get_all_possible_subs(query: List[str], length: int) -> List[List[str]]:
    subs: List[List[str]] = []
    query_length: int = len(query)

    assert query_length >= length
    for start_index in range(query_length - length + 1):
        subs.append(query[start_index:start_index + length])

    return subs


def construct_query(query: str, api_list: List[API]) -> Optional[Dict[str, str]]:
    cleaned_query: str = clean_string(query)
    filtered_query: List[str] = [token for token in cleaned_query.split(" ") if len(token) > 0]

    longest_query: List[List[str]] = [filtered_query]
    initial_length: int = len(filtered_query)

    for length in tqdm(range(initial_length - 1, -1, -1)):
        query_lengths: List[Union[int, float]] = [-1]*len(api_list)
        results: List[Optional[Dict[str, str]]] = []

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
        final_result: Optional[Dict[str, str]] = results[max_index]

        if final_result is not None:
            return final_result

    return None


def tag_song(path: Path, song: str, api_list: List[API]):
    audio_file: Union[Mp3AudioFile, TagFile, None] = eyed3.load(str(path / song))
    assert audio_file is not None
    if isinstance(audio_file, TagFile):
        raise TypeError("Invalid Data Format")

    metadata: Optional[Dict[str, Optional[str]]] = None
    title: Optional[str] = audio_file.tag.title

    # Check if metadata already exists
    if title is not None:
        metadata = construct_query(title, api_list)

    if title is None or metadata is None:
        file_base: Union[bytes, str] = os.path.splitext(song)[0]
        try:
            file_name = file_base.decode("utf-8")
        except AttributeError:
            file_name = file_base

        metadata = construct_query(file_name, api_list)

        if metadata is None:
            print(f"Cannot tag file {song}")
            return

    assert metadata["Name"] is not None

    audio_file.tag.title = metadata["Name"]
    audio_file.tag.artists = metadata["Artists"]

    os.makedirs(ALBUM_DIR, exist_ok=True)
    img_path: str = f"{ALBUM_DIR}/{remove_slashes(audio_file.tag.title)}.jpg"

    assert metadata["Album Art"] is not None
    download_image(metadata["Album Art"], img_path)
    subprocess.run(["lame", "--ti", img_path, str(path / song)])
    rmtree(ALBUM_DIR)

    # Rename the file so that it matches the title
    os.rename(str(path / song), str(path / f"{remove_slashes(audio_file.tag.title)}.mp3"))

    # Remove old files
    for file_to_remove in glob.glob(str(path_name) + "/*.mp3.mp3"):
        os.remove(file_to_remove)

    print(f"{song} will now have the metadata: {metadata}")


if __name__ == "__main__":
    load_dotenv()
    path_name: Union[Path, Any] = Path("/home/samyak/music_test")
    API_LIST: List[API] = [VGMDB(), GENIUS(os.getenv("GENIUS_TOKEN"))]

    assert isinstance(path_name, Path)
    files = os.listdir(str(path_name))
    for file in files:
        print(f"{file} is being processed")
        tag_song(path_name, file, API_LIST)
