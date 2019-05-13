from os import getenv
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI
import tagger
import fetchvids
from pydantic import BaseModel, UrlStr

from models import DatabaseOptions
from utils.google_drive import DriveHandler
from utils.database import DatabaseHandler
from dotenv import load_dotenv
from utils.text_processing import calculate_similarity

app = FastAPI()


class payload(BaseModel):
    url: UrlStr


def get_database_object():
    return DatabaseHandler(DatabaseOptions(database_user=getenv("MONGO_USER"), database_password=getenv("MONGO_PASS"),
                                           database_uri=getenv("MONGO_URI"), database_name=getenv("DB_NAME"),
                                           port=getenv("DB_PORT")))


@app.get("/")
async def test():
    return {
        "message": "success"
    }


@app.get("/update")
async def update_db():
    load_dotenv()
    fetchvids.start()
    tagger.start()
    drive = DriveHandler()
    drive.copy_dir(Path("./music"), getenv("MUSIC_DRIVE_ID"))


@app.get("/search/{name}")
async def search(name: str):
    load_dotenv()
    db = get_database_object()
    downloaded_songs: List[Dict[str, str]] = db.get_all_downloaded()

    search_result: List[Dict[str, str]] = []
    for song in downloaded_songs:
        if calculate_similarity(name, song['name']) >= 0.5 or (song.get("new_name") is not None and calculate_similarity(name, song['new_name']) >= 0.5):
            search_result.append({
                'name': song['name'],
                'url': song['url']
            })

    return {
        'message': 'No result matched' if len(search_result) == 0 else 'Success',
        'results': search_result
    }


@app.get("/remove/{url}")
async def remove_song(url: str):
    pass


@app.get("/blacklist/{url}")
async def blacklist_song(url: str):
    pass


@app.get("/add/{url}")
async def add_song(url: str):
    pass
