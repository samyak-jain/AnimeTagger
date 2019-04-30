import requests
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os
from tqdm import tqdm

BASE_URL = "https://vgmdb.info"
SEARCH_URL = f"{BASE_URL}/search"

def query_vgmdb(query: str) -> Optional[Dict[str, Optional[str]]]:
	song_name: Optional[str] = None
	artists: Optional[str] = None
	album_art: Optional[str] = None

	parsed_query: str = urllib.parse.quote(query)
	search_result: Dict[str, Any] = requests.get(f"{SEARCH_URL}/{parsed_query}?format=json").json()
	albums: List[Dict[str, Any]] = search_result["results"]["albums"]

	for album in albums:
		album_code: str = album["link"]
		album_details: Dict[str, Any] = requests.get(f"{BASE_URL}/{album_code}?format=json").json()
		album_art = album_details["picture_full"]

		# Ignore albums with no album art or track listings

		assert album_art is not None
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

		artists = ", ".join(artist_list)

		break

	if (song_name is None) or (artists is None) or (album_art is None):
		return None

	return {
		"Name": song_name,
		"Artists": artists,
		"Album Art": album_art
	}

def get_all_possible_substrings(query: str, length: int) -> List[str]:
	substrings: List[str] = []
	query_length: int = len(query)

	assert query_length >= length
	for start_index in range(query_length - length):
		substrings.append(query[start_index:start_index+length])

	return substrings

def construct_query(query: str) -> Optional[Tuple[str, Optional[Dict[str, Optional[str]]]]]:
	longest_query: List[str] = [query]

	for length in tqdm(range(len(query)-1, 1, -1)):
		for index, long_query in enumerate(longest_query):

			result: Optional[Dict[str, Optional[str]]] = query_vgmdb(long_query)
			if result is not None:
				return long_query, result

		longest_query = get_all_possible_substrings(query, length)
		print(longest_query)

	return None






def tag_song(path: Path, song: str):
	pass

if __name__=="__main__":
#	print(query_vgmdb("アイシテル"))
	path = Path("/home/samyak/music_test")
	files = os.listdir(str(path))
	file_names = [os.path.splitext(file_name)[0] for file_name in files]
	print(file_names)
	for file_name in file_names:
		result = construct_query(file_name)
		if result is None:
			print(f"Attempt at tagging {file_name} failed")
		else:
			print(f"Tagging successfull. The resultant query is {result[0]}")
			print(f"And the result is {result[1]}")
