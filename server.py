from os import getenv
from pathlib import Path

from fastapi import FastAPI
import tagger
import fetchvids
from pydantic import BaseModel, UrlStr

from models import DatabaseOptions
from utils.google_drive import DriveHandler
from utils.database import DatabaseHandler
from dotenv import load_dotenv

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
    db = get_database_object()


@app.get("/remove/{url}")
async def remove_song(url: str):
    pass


@app.get("/blacklist/{url}")
async def blacklist_song(url: str):
    pass


@app.get("/add/{url}")
async def add_song(url: str):
    pass
