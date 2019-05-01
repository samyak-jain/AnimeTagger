from tenacity import retry, stop_after_attempt
import requests
import asyncio
from aiohttp import ClientSession, client_exceptions
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os
from tqdm import tqdm
import string
import re

BASE_URL = "https://vgmdb.info"
SEARCH_URL = f"{BASE_URL}/search"

@retry(stop=stop_after_attempt(2))
async def fetch(url, session):
	try:
		async with session.get(url) as response:
			return await response.json()
	except client_exceptions.ContentTypeError as exception:
		print(f"Bad Url: {url}")
		print(exception)

		return None

async def query_vgmdb(query_list: List[str]) -> Optional[Dict[str, Optional[str]]]:
	song_name: Optional[str] = None
	artists: Optional[str] = None
	album_art: Optional[str] = None


	query_without_punc_list = [re.sub('[%s]' % re.escape(string.punctuation), ' ', query) for query in query_list]
	parsed_query_list = [urllib.parse.quote(query) for query in query_without_punc_list]


	tasks = []
	async with ClientSession() as session:
		for query in parsed_query_list:
			task = asyncio.create_task(fetch(f"{SEARCH_URL}/{query}?format=json", session))
			tasks.append(task)

		response_list = await asyncio.gather(*tasks)


	for search_result in response_list:

		if search_result is None:
			continue
	
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

	return None

def get_all_possible_substrings(query: str, length: int) -> List[str]:
	substrings: List[str] = []
	query_length: int = len(query)

	assert query_length >= length
	for start_index in range(query_length - length):
		substrings.append(query[start_index:start_index+length])

	return substrings

def construct_query(query: str) -> Optional[Dict[str, Optional[str]]]:
	longest_query: List[str] = [query]

	for length in tqdm(range(len(query)-1, 1, -1)):
		result = asyncio.run(query_vgmdb(longest_query))

		if result is not None:
			return result

		longest_query = get_all_possible_substrings(query, length)

	return None


def tag_song(path: Path, song: str):
	pass

if __name__=="__main__":
	path = Path("/home/samyak/music_test")
	files = os.listdir(str(path))
	file_names = [os.path.splitext(file_name)[0] for file_name in files]
	for file_name in file_names:
		result = construct_query(file_name)
		if result is None:
			print(f"Attempt at tagging {file_name} failed")
		else:
			print(f"Tagging successfull. The result is {result}")
