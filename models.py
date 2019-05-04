from typing import Optional

from pydantic import BaseModel


class Song(BaseModel):
    song_name: str
    artists: str
    album_art: Optional[str]
    album_name: str
