from pathlib import Path
import urllib.parse
from typing import Dict

import requests
from requests import Response


class ACOUSTID:
    def __init__(self, path: Path, server_url: str):
        self.song_path = path
        self.server_url = server_url

    def inference(self):
        absolute_path: str = str(self.song_path.absolute())
        encoded_path: str = urllib.parse.quote(absolute_path)

        response: Response = requests.get(f"{self.server_url}/tag/{encoded_path}")

        if response.status_code != 200:
            print("There was some kind of error")
            print(f"Error: {response.status_code}")
            return None

        acoust: Dict[str, str] = response.json()
