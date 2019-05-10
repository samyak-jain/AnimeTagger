import subprocess
from os import getenv
from pathlib import Path
from subprocess import Popen, PIPE
from typing import List, Optional, Tuple

from dotenv import load_dotenv

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
    processes: List[Popen] = []
    number_of_vids_downloaded: int = 0

    for url in url_list:
        if url in blacklist_urls:
            print(f"Not executing url {url} since it is in blacklist")
            continue

        if number_of_vids_downloaded >= max_number:
            break

        processes.append(subprocess.Popen(["sh", str(Path.cwd() / "scripts/download_vids.sh"), url,
                                           str(download_path.absolute()) + "/%(title)s.%(ext)s"], stdout=PIPE))

        number_of_vids_downloaded += 1

    outputs: List[Optional[str]] = [None]*max_number
    count: int = 0

    while processes:
        for index, proc in enumerate(processes):
            if proc.poll() is None:
                print("waiting")

            outputs[index + count] = proc.stdout.read().decode("utf-8")

            proc.terminate()

            processes.remove(proc)
            count += 1

    print(f"Added songs {outputs}")
    data_to_add: List[str] = [url_list[index] for index, output in enumerate(outputs) if output is not None and len(output) < 1]

    if len(data_to_add) > 0:
        db.add_many_to_blacklist(data_to_add)


if __name__ == "__main__":
    load_dotenv()
    database = DatabaseHandler(DatabaseOptions(database_user=getenv("MONGO_USER"),
                                               database_password=getenv("MONGO_PASS"),
                                               database_uri=getenv("MONGO_URI"),
                                               database_name=getenv("DB_NAME"),
                                               port=getenv("DB_PORT")))

    cookie: Path = Path("cookies.txt")
    youtube_url: str = "https://www.youtube.com/watch?v=Q9WcG0OMElo&list=RDGMEMhCgTQvcskbGUxqI4Sn2QYw&start_radio=1"

    vid_list: List[str] = get_vid_list(cookie, youtube_url)
    download_vids(Path("./music"), vid_list, database, 10)
