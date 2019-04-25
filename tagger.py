import requests
import urllib.parse
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

BASE_URL = "https://vgmdb.info"
SEARCH_URL = f"{BASE_URL}/search"

def query_vgmdb(query: str) -> Dict[str, str]:
	song_name: str

	parsed_query: str = urllib.parse.quote(query)
	search_result: Dict[str, Any] = requests.get(f"{SEARCH_URL}/{parsed_query}?format=json").json()
	albums: List[Dict[str, Any]] = search_result["results"]["albums"]

	for album in albums:
		album_code: str = album["link"]
		album_details: Dict[str, Any] = requests.get(f"{BASE_URL}/{album_code}?format=json").json()
		album_art: str = album_details["picture_full"]

		# Ignore albums with no album art or track listings
		if "nocover" in album_art or len(album_details["discs"]) == 0:
			continue

		track_names: List[Dict[str, Any]] = [track["names"] for track in album_details["discs"][0]["tracks"]]

		# If english name exists, make that the song name
		romaji_existed: bool = False
		for track in track_names:
			romaji_name: Optional[str] = track.get("Romaji")
			
			if romaji_name is not None:
				romaji_existed = True
				song_name = romaji_name
				break

		# Else make the japanese name as the title of the song
		if not romaji_existed:
			song_name = track_names[0]["Japanese"]


		performers: List[Dict[str, Any]] = album_details["performers"]
		artist_list: List[str] = []

		for performer in performers:
			names: Dict[str, str] = performer["names"]
			english_name: Optional[str] = names.get("en")

			name: str
			# Add japanese name if there is no english name for the artist
			if english_name is None:
				name = names["ja"]
			else:
				name = english_name

			artist_list.append(name)

		artists: str = ", ".join(artist_list)

		break

	return {
		"Name": song_name,
		"Artists": artists,
		"Album Art": album_art
	}


def construct_query():
	pass


def tag_song(path: Path, song: str):
	audio = MP3(str(path / song), ID3=ID3)    
	query: str = os.path.splitext(song)[0]
	meta: Dict[str, str] = query_vgmdb(query)
	audio.tags.add(
	    APIC(
	        encoding=3, # 3 is for utf-8
	        mime='image/jpg', # image/jpeg or image/png
	        type=3, # 3 is for the cover image
	        desc=u'Cover',
	        data=requests.get(meta["Album Art"]).content
	    )
	)

	audio.save()

if __name__=="__main__":
	# print(query_vgmdb("アイシテル"))
	path = Path("/home/samyak/music_test")
	files = os.listdir(str(path))
	for file in files:
		tag_song(path, file)