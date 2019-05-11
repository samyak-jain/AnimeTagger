from fastapi import FastAPI
import tagger
import fetchvids

app = FastAPI()


@app.get("/update")
async def update_db():
    fetchvids.start()
    tagger.start()


@app.get("/search/{name}")
async def search(name: str):
    pass


@app.get("/remove/{url}")
async def remove_song(url: str):
    pass


@app.get("/blacklist/{url}")
async def blacklist_song(url: str):
    pass


@app.get("/add/{url}")
async def add_song(url: str):
    pass
