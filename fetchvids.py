import subprocess
from os import getenv
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List, Optional, Tuple

from dotenv import load_dotenv

import json
from models import DatabaseOptions
from utils.database import DatabaseHandler


def get_vid_list(cookie_path: Path, playlist_url: str) -> List[str]:
    fetch_result: Popen = subprocess.Popen(["sh", str(Path.cwd() / "scripts/fetch_vids.sh"), str(cookie_path),
                                            playlist_url], stdout=PIPE)

    list_of_urls: List[str] = fetch_result.stdout.read().decode("utf-8").split("\n")
    filtered_urls: List[str] = [url for url in list_of_urls if len(url) > 0]

    return filtered_urls


def download_vids(download_path: Path, url_list: List[str], db: DatabaseHandler, max_number: Optional[int] = None):
    if max_number is None:
        max_number = len(url_list)

    blacklist_urls: List[str] = list(db.get_all_blacklist())
    already_downloaded_list: List[str] = list(db.get_all_downloaded())
    urls_to_be_blacklisted: List[str] = []
    number_of_vids_downloaded: int = 0

    outputs: List[Tuple[str, str]] = []
    for url in url_list:
        if url in blacklist_urls:
            print(f"Not executing url {url} since it is in blacklist")
            continue

        if url in already_downloaded_list:
            print(f"{url} has already been downloaded")
            continue

        assert len(url) > 18
        youtube_key = getenv("YOUTUBE_KEY")

        assert youtube_key is not None
        vid_health = subprocess.run(["sh", "scripts/get_vid_health.sh", url[17:], youtube_key], stdout=PIPE)

        try:
            items = json.loads(vid_health.stdout.decode('utf-8').rstrip())['items']
        except json.decoder.JSONDecodeError:
            print("Unknown Error")
            continue

        if len(items) == 0:
            urls_to_be_blacklisted.append(url)
            continue

        if number_of_vids_downloaded >= max_number:
            break

        x = subprocess.Popen(["sh", str(Path.cwd() / "scripts/download_vids.sh"), url,
                              str(download_path.absolute()) + "/%(title)s.%(ext)s"], stdout=PIPE)
        x.wait()
        test = x.stdout.read().decode('utf-8')
        outputs.append((url, test))

        number_of_vids_downloaded += 1

    print(f"Added songs {outputs}")

    downloaded_songs: List[Tuple[str, str]] = [(url, output) for url, output in outputs
                                               if output is not None and url not in urls_to_be_blacklisted]

    download_urls, download_names = zip(*downloaded_songs)

    if len(urls_to_be_blacklisted) > 0:
        db.add_many_to_blacklist(urls_to_be_blacklisted)

    if len(downloaded_songs) > 0:
        db.add_many_to_collection(download_urls, download_names, db.download_collection)


def start():
    load_dotenv()
    database = DatabaseHandler(DatabaseOptions(database_user=getenv("MONGO_USER"),
                                               database_password=getenv("MONGO_PASS"),
                                               database_uri=getenv("MONGO_URI"),
                                               database_name=getenv("DB_NAME"),
                                               port=getenv("DB_PORT")))

    cookie: Path = Path("secrets/cookies.txt")
    youtube_url: str = "https://www.youtube.com/watch?v=Q9WcG0OMElo&list=RDGMEMhCgTQvcskbGUxqI4Sn2QYw&start_radio=1"

    vid_list: List[str] = get_vid_list(cookie, youtube_url)
    download_vids(Path("./music"), vid_list, database, 10)


if __name__ == "__main__":
    start()
