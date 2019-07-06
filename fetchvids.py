import os
import shutil
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


def download_vids(download_path: Path, url_list: List[str], db: DatabaseHandler, max_number: Optional[int] = None) \
        -> List[str]:

    if max_number is None:
        max_number = len(url_list)

    blacklist_urls: List[str] = list(db.get_all_blacklist_urls())
    already_downloaded_list: List[str] = list(db.get_all_downloaded_urls())
    urls_to_be_blacklisted: List[str] = []
    number_of_vids_downloaded: int = 0
    downloading_url_list: List[str] = []

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

        number_of_vids_downloaded += 1
        downloading_url_list.append(url)

    batch_path = Path(Path.cwd() / "batch_file.txt")
    with open(batch_path, "w") as f:
        f.write('\n'.join(downloading_url_list))

    download = subprocess.Popen(["sh", "scripts/download_vids.sh", str(batch_path), str(download_path.absolute()) +
                                 "/%(title)s.%(ext)s", "--verbose"], stdout=PIPE)

    names: List[str] = download.stdout.read().decode('utf-8').split('\n')
    outputs = list(zip(downloading_url_list, names))
    os.remove(batch_path)
    print(f"Added songs {outputs}")

    downloaded_songs: List[Tuple[str, str]] = [(url, output) for url, output in outputs
                                               if output is not None and url not in urls_to_be_blacklisted]

    if len(downloaded_songs) < 1:
        return ["Null"]

    download_urls, download_names = zip(*downloaded_songs)
    clean_download_names = [name.rstrip() for name in download_names]

    if len(urls_to_be_blacklisted) > 0:
        db.add_many_to_blacklist(urls_to_be_blacklisted)

    if len(downloaded_songs) > 0:
        db.add_many_to_downloaded(download_urls, clean_download_names)

    return clean_download_names


def start(vid: Optional[str] = None, number: Optional[int] = None) -> List[str]:
    shutil.rmtree("./music", ignore_errors=True)
    load_dotenv()
    database = DatabaseHandler(DatabaseOptions(database_user=getenv("MONGO_USER"),
                                               database_password=getenv("MONGO_PASS"),
                                               database_uri=getenv("MONGO_URI"),
                                               database_name=getenv("DB_NAME"),
                                               port=getenv("DB_PORT")))

    cookie: Path = Path("cookies.txt")

    if vid is None:
        youtube_urls: List[str] = database.get_all_playlist_urls()

        vid_list: List[str] = []
        for playlist in youtube_urls:
            vid_list += get_vid_list(cookie, playlist)
    else:
        vid_list = [vid]

    return download_vids(Path("./music"), vid_list, database, number)


if __name__ == "__main__":
    start()
