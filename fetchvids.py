import subprocess
from pathlib import Path
from subprocess import Popen
from typing import List, Optional


def get_vid_list(cookie_path: Path, playlist_url: str) -> List[str]:
    fetch_result: Popen = subprocess.Popen(["sh", str(Path.cwd() / "scripts/fetch_vids.sh"), str(cookie_path),
                                            playlist_url], stdout=subprocess.PIPE)

    list_of_urls: List[str] = fetch_result.stdout.read().decode("utf-8").split("\n")
    filtered_urls: List[str] = [url for url in list_of_urls if len(url) > 0]

    return filtered_urls


def download_vids(download_path: Path, url_list: List[str], max_number: Optional[int] = None):
    if max_number is None:
        max_number = len(url_list)

    for url in url_list[:max_number]:
        subprocess.run(["youtube-dl", "-x", "--audio-format", "mp3", url, "-o", str(download_path.absolute()) +
                        "/%(title)s.%(ext)s", "--add-metadata"])

        


if __name__ == "__main__":
    cookie: Path = Path("cookies.txt")
    youtube_url: str = "https://www.youtube.com/watch?v=Q9WcG0OMElo&list=RDGMEMhCgTQvcskbGUxqI4Sn2QYw&start_radio=1"

    vid_list: List[str] = get_vid_list(cookie, youtube_url)
    print(vid_list)
    download_vids(Path("./music"), vid_list, 2)
