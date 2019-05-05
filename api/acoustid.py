from pathlib import Path


class ACOUSTID:
    def __init__(self, path: Path, server_url: str):
        self.song_path = path
        self.server_url = server_url

    def inference(self):
        pass