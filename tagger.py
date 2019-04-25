import requests
import urllib.parse

from typing import Dict, List, Any, Optional

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


def tag_song():
	pass


if __name__=="__main__":
	print(query_vgmdb("Isekai Quartet"))