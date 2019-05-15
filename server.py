from os import getenv
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, UrlStr
from starlette.middleware.cors import CORSMiddleware

import fetchvids
import tagger
from models import DatabaseOptions
from utils.database import DatabaseHandler
from utils.google_drive import DriveHandler

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'])


class Payload(BaseModel):
    url: UrlStr
    name: Optional[str] = None


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
        best_result = max(search_result, key=lambda element: element['similarity'])
        url_to_remove = best_result['url']
        details = best_result
    else:
        url_to_remove = payload.url
        details = None

    db.remove_from_blacklist_with_url(url_to_remove)

    return {
        'message': f"Removed result {url_to_remove}",
        'details': details
    }


@app.post("/blacklist")
async def blacklist_song(payload: Payload):
    db.add_to_blacklist(payload.url)


@app.get("/add/")
async def add_song(payload: Payload):
    fetchvids.start(payload.url)
    tagger.start()
    drive = DriveHandler()
    drive.copy_dir(Path("./music"), getenv("MUSIC_DRIVE_ID"))


@app.post("/playlist")
async def add_playlist(payload: Payload):
    if db.add_to_playlists(payload.url) is None:
        return {
            'message': 'Playlist already exists'
        }

    return {
        'message': 'Success'
    }


@app.post("/remove/playlist")
async def delete_playlist(payload: Payload):
    if db.remove_from_playlists_with_url(payload.url) is None:
        return {
            'message': f"{payload.url} doesn't exist in the playlist database"
        }

    return {
        'message': 'Success'
    }


if __name__ == "__main__":
    load_dotenv()
    mongo_user, mongo_pass, mongo_uri, db_name, db_port = getenv("MONGO_USER"), getenv("MONGO_PASS"), \
                                                          getenv("MONGO_URI"), getenv("DB_NAME"), getenv("DB_PORT")

    assert mongo_user is not None and mongo_pass is not None and mongo_uri is not None and db_name is not None and \
           db_port is not None

    db = DatabaseHandler(DatabaseOptions(database_user=mongo_user, database_password=mongo_pass, database_uri=mongo_uri,
                                         database_name=db_name, port=db_port))

    uvicorn.run(app, host="0.0.0.0", port=int(db_name) if db_port is not None else 8000)
