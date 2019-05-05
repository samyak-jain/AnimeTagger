import subprocess
from pathlib import Path
from subprocess import Popen
from typing import List, Optional


def get_vid_list(cookie_path: Path, playlist_url: str) -> List[str]:
    download_command: List[str] = ["youtube-dl", "--cookies", str(cookie_path), playlist_url, "--flat-playlist", "-j"]
    json_parse_command: List[str] = ["jq", "-r", ".id"]
    sed_command: List[str] = ["sed", "s_^_https://youtu.be/_"]

    download_result: Popen = subprocess.Popen(download_command, stdout=subprocess.PIPE)
    json_parse_result: Popen = subprocess.Popen(json_parse_command, stdin=download_result.stdout,
                                                stdout=subprocess.PIPE)

    sed_result = subprocess.Popen(sed_command, stdin=json_parse_result.stdout, stdout=subprocess.PIPE)

    list_of_urls: List[str] = sed_result.stdout.read().decode("utf-8").split("\n")
    filtered_urls: List[str] = [url for url in list_of_urls if len(url) > 0]

    return filtered_urls


def download_vids(download_path: Path, url_list: List[str], max_number: Optional[int] = None):
    if max_number is None:
        max_number = len(url_list)

    for url in url_list[:max_number]:
        subprocess.run(["youtube-dl", url, "-o", str(download_path.absolute()) + "%(title)s.%(ext)s"])


if __name__ == "__main__":
    cookie: Path = Path("cookies.txt")
    youtube_url: str = "https://www.youtube.com/watch?v=Q9WcG0OMElo&list=RDGMEMhCgTQvcskbGUxqI4Sn2QYw&start_radio=1"

    vid_list: List[str] = get_vid_list(cookie, youtube_url)
    download_vids(Path("./music"), vid_list)
