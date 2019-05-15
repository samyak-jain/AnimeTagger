from os import getenv
from pathlib import Path
from typing import List, Dict

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, UrlStr

import fetchvids
import tagger
from models import DatabaseOptions
from utils.database import DatabaseHandler
from utils.google_drive import DriveHandler
from utils.text_processing import calculate_similarity

app = FastAPI()


class Payload(BaseModel):
    url: UrlStr
    name: str = None


@app.get("/")
async def test():
    return {
        "message": "success",
    }


@app.get("/update")
async def update_db():
    fetchvids.start()
    tagger.start()
    drive = DriveHandler()
    drive.copy_dir(Path("./music"), getenv("MUSIC_DRIVE_ID"))


@app.get("/search/{name}")
async def search(name: str):
    search_result = db.search_collection_by_name(name, db.download_collection)

    return {
        'message': 'No result matched' if len(search_result) == 0 else 'Success',
        'results': search_result
    }


@app.post("/remove")
async def remove_from_blacklist(payload: Payload):
    if payload.name is not None:
        search_result = db.search_collection_by_name(payload.name, db.blacklist_collection)
        db.remove_from_blacklist_with_name(search_result[])



@app.post("/blacklist")
async def blacklist_song(payload: Payload):
    db.add_to_blacklist(payload.url)


@app.get("/add/{url}")
async def add_song(url: str):
    pass


if __name__ == "__main__":
    load_dotenv()
    db = DatabaseHandler(DatabaseOptions(database_user=getenv("MONGO_USER"), database_password=getenv("MONGO_PASS"),
                                           database_uri=getenv("MONGO_URI"), database_name=getenv("DB_NAME"),
                                           port=getenv("DB_PORT")))

    uvicorn.run(app, host="0.0.0.0", port=int(getenv("PORT")) if getenv("PORT") is not None else 8000)
