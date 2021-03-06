from typing import Optional, List, Dict

from pydantic import BaseModel


class Song(BaseModel):
    song_name: str
    artists: str
    album_art: Optional[str]
    album_name: str


class CommandLineOptions(BaseModel):
    flag_maps: Dict[str, str] = {
        "p": "progress",
        "h": "help"
    }
    progress: bool = False
    command_list: List[str]


class DatabaseOptions(BaseModel):
    database_user: str
    database_password: str
    database_uri: str
    database_name: str
    port: int
