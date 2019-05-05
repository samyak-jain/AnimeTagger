import subprocess
from subprocess import Popen
from typing import List


def get_vid_list():
    download_command: List[str] = ["youtube-dl", "--cookies", "cookies.txt", "https://www.youtube.com/watch?v"
                                                                             "=Q9WcG0OMElo&list"
                                                                             "=RDGMEMhCgTQvcskbGUxqI4Sn2QYw"
                                                                             "&start_radio=1", "--flat-playlist", "-j"]

    json_parse_command: List[str] = ["jq", "-r", ".id"]
    sed_command: List[str] = ["sed", "s_^_https://youtu.be/_"]

    download_result: Popen = subprocess.Popen(download_command, stdout=subprocess.PIPE)
    json_parse_result: Popen = subprocess.Popen(json_parse_command, stdin=download_result.stdout,
                                                stdout=subprocess.PIPE)

    sed_result = subprocess.Popen(sed_command, stdin=json_parse_result.stdout, stdout=subprocess.PIPE)

    list_of_urls: List[str] = sed_result.stdout.read().decode("utf-8").split("\n")

    filtered_urls: List[str] = [url for url in list_of_urls if len(url) > 0]

    return filtered_urls


if __name__ == "__main__":
    print(get_vid_list())
