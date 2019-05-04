import requests
import shutil
from pathlib import Path

from typing import Union

from requests import Response


def download_image(url: str, path: Union[str, Path]):
    path_object: Path = Path(path)
    response: Response = requests.get(url, stream=True)

    if response.status_code != 200:
        print(f"Error: Could not request url. State Code {response.status_code}")
    elif path_object.is_file():
        print(f"Error: There is already a file with path {str(path_object)}")
    else:
        string_path: str = (str(path_object))
        with open(string_path, "wb+") as image_file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, image_file)
