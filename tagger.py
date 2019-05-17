import asyncio
import glob
import os
import sys
from asyncio.tasks import Task
from os import getenv
from pathlib import Path
from shutil import rmtree
from typing import Dict, List, Any, Optional, Union, Tuple

import eyed3
from aiohttp import ClientSession
from dotenv import load_dotenv
from eyed3.id3 import TagFile
from eyed3.mp3 import Mp3AudioFile
from pathos.multiprocessing import ThreadPool
from tqdm import tqdm

from api import API
from api.acoustid import ACOUSTID
from api.genius import GENIUS
from api.vgmdb import VGMDB
from models import Song, CommandLineOptions, DatabaseOptions
from utils.console import command_line_parser
from utils.database import DatabaseHandler
from utils.image_handler import download_image
from utils.text_processing import clean_string, remove_slashes, detect_language

ALBUM_DIR = "albums"
command_line_options: Optional[CommandLineOptions] = None


async def query_databases(initial_query: str, query_list: List[List[str]], query_api: API, best_similarity: float) \
        -> Optional[Tuple[float, Optional[Song]]]:
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

        similarity, song = query_api.album(response_list, initial_query, best_similarity)

        if song is None:
            return None

        if (song.song_name is None) or (song.artists is None) or (song.album_name is None):
            return None

        if similarity > best_similarity:
            return similarity, song

        return best_similarity, None


def get_all_possible_subs(query: List[str], length: int) -> List[List[str]]:
    subs: List[List[str]] = []
    query_length: int = len(query)

    assert query_length >= length
    for start_index in range(query_length - length + 1):
        subs.append(query[start_index:start_index + length])

    return subs


def construct_query(query: str, api_list: List[API]) -> Optional[Song]:
    global command_line_options

    cleaned_query: str = clean_string(query)
    filtered_query: List[str] = [token for token in cleaned_query.split(" ") if len(token) > 0]

    longest_query: List[List[str]] = [filtered_query]
    initial_length: int = len(filtered_query)
    best_similarity: float = -1
    best_result: Optional[Song] = None

    if command_line_options is not None and command_line_options.progress:
        iterate_over = tqdm(range(initial_length - 1, -1, -1))
    else:
        iterate_over = range(initial_length - 1, -1, -1)

    final_query_list: List[List[str]] = []
    for length in iterate_over:
        final_query_list.extend(longest_query)
        longest_query = get_all_possible_subs(filtered_query, length)

    for api_tag in api_list:
        async_result = asyncio.run(query_databases(query, final_query_list, api_tag, best_similarity))

        if async_result is not None:
            current_sim, result = async_result

            if result is not None:
                if current_sim > best_similarity:
                    best_result = result

                best_similarity = current_sim
                if best_similarity > 0.8:
                    return best_result

    return best_result


def tag_song(path: Path, song: str, api_list: List[API], db: DatabaseHandler, number: int):
    print(f"File NO: {number}")
    print(f"{song} is being processed")

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

    possibilities: List[Optional[str]] = [fingerprint_title]
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
        audio_file.tag.artist = fingerprint_artist
    else:
        audio_file.tag.title = metadata.song_name
        audio_file.tag.artist = metadata.artists

    audio_file.tag.album = metadata.album_name

    os.makedirs(ALBUM_DIR, exist_ok=True)
    img_path: str = f"{ALBUM_DIR}/{remove_slashes(audio_file.tag.title)}.jpg"

    # Save all the changes to the tags
    if metadata.album_art is not None:
        download_image(metadata.album_art, img_path)
        with open(img_path, "rb") as img:
            imgdata = img.read()
            audio_file.tag.images.set(3, imgdata, "image/jpg", metadata.album_name)

        rmtree(ALBUM_DIR)
    audio_file.tag.save()

    # Rename the file so that it matches the title
    db.update_downloaded(song[:-4].rstrip(), remove_slashes(audio_file.tag.title).rstrip())
    os.rename(str(path / song), str(path / f"{remove_slashes(audio_file.tag.title)}.mp3"))

    # Remove old files
    for file_to_remove in glob.glob(str(path) + "/*.mp3.mp3"):
        os.remove(file_to_remove)

    final_metadata: Dict[str, Optional[str]] = {
        'song': audio_file.tag.title,
        'album': audio_file.tag.album,
        'artist': audio_file.tag.artist,
        'album art': metadata.album_art
    }
    print(f"{song} will now have the metadata: {final_metadata}")
    print(f"{number} done")


def start(path_dir: Optional[Path] = None):
    load_dotenv()
    global command_line_options

    if path_dir is None:
        command_line_options = command_line_parser(sys.argv)
        assert command_line_options is not None
        path_name: Union[Path, Any] = Path(command_line_options.command_list[1])
    else:
        path_name = path_dir

    database = DatabaseHandler(DatabaseOptions(database_user=getenv("MONGO_USER"),
                                               database_password=getenv("MONGO_PASS"),
                                               database_uri=getenv("MONGO_URI"),
                                               database_name=getenv("DB_NAME"),
                                               port=getenv("DB_PORT")))

    api_list: List[API] = [VGMDB(), GENIUS(os.getenv("GENIUS_TOKEN"))]

    assert isinstance(path_name, Path)
    files = os.listdir(str(path_name))

    with ThreadPool() as pool:
        pool.starmap(tag_song, [(path_name, file, api_list, database, index) for index, file in enumerate(files)])


if __name__ == "__main__":
    start()
