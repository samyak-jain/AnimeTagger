from pathlib import Path
from typing import Dict, Optional, Union

from utils.aidmatch import aidmatch


class ACOUSTID:
    def __init__(self, path: Path, api_key: str):
        self.song_path = path
        self.api_key = api_key

    def inference(self) -> Optional[Dict[str, Union[str, float]]]:
        absolute_path: str = str(self.song_path.absolute())
        results = aidmatch(absolute_path, self.api_key)

        if len(results) < 1:
            return None

        max_score = max(results, key=lambda element: element['score'])

        if max_score['score'] < 0.5:
            return None

        return max_score
