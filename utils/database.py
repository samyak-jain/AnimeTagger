from typing import List, Dict, Optional

import pymongo
from pymongo import database
from pymongo.collection import Collection

from models import DatabaseOptions
from utils.text_processing import calculate_similarity, clean_string


class DatabaseHandler:
    playlist_collection: Collection
    blacklist_collection: Collection
    download_collection: Collection
    database: pymongo.database.Database
    client: pymongo.MongoClient

    def __init__(self, options: DatabaseOptions):
        self.client = pymongo.MongoClient(options.database_uri, options.port)
        self.database = self.client[options.database_name]
        self.database.authenticate(options.database_user, options.database_password)
        self.download_collection = self.database["downloaded"]
        self.blacklist_collection = self.database["blacklist"]
        self.playlist_collection = self.database["playlists"]

    @staticmethod
    def search_collection_by_name(name: str, collection: Collection):
        downloaded_songs: List[Dict[str, str]] = list(collection.find({}))

        search_result: List[Dict[str, Optional[str]]] = []
        for song in downloaded_songs:

            if song.get("new_name") is not None:
                similarity = max(calculate_similarity(name, song["new_name"]), calculate_similarity(name, song['name']))
            else:
                similarity = calculate_similarity(name, song['name'])

            if similarity >= 0.5:
                search_result.append({
                    'name': song['name'],
                    'url': song['url'],
                    'new_name': song.get('new_name'),
                    'similarity': similarity
                })

        return search_result

    @staticmethod
    def check_if_url_exists(url: str, collection: Collection) -> bool:
        cursor: pymongo.cursor = collection.find({
            'url': url
        })

        documents: List[Dict[str, str]] = list(cursor)

        return not (len(documents) < 1)

    def add_to_blacklist(self, url: str):
        if self.check_if_url_exists(url, self.blacklist_collection):
            return

        self.blacklist_collection.insert_one({
            'url': url
        })

    def add_to_playlists(self, url: str):
        if self.check_if_url_exists(url, self.playlist_collection):
            return

        self.playlist_collection.insert_one({
            'url': url
        })

    def add_many_to_blacklist(self, urls: List[str]):
        urls_not_added_yet: List[str] = []

        for url in urls:
            if not self.check_if_url_exists(url, self.blacklist_collection):
                urls_not_added_yet.append(url)

        if len(urls_not_added_yet) < 1:
            return

        self.blacklist_collection.insert_many([
            {"url": url} for url in urls_not_added_yet
        ])

    def add_many_to_downloaded(self, urls: List[str], names: List[str]):
        urls_not_added_yet: List[str] = []

        for url in urls:
            if not self.check_if_url_exists(url, self.download_collection):
                urls_not_added_yet.append(url)

        self.download_collection.insert_many([

            {
                'url': url,
                'name': name
            }

            for url, name in zip(urls, names)
        ])

    def update_downloaded(self, old_name: str, new_name: str):
        downloads = self.download_collection.find({})
        for download in downloads:
            if clean_string(old_name) == clean_string(download['name']):
                result = self.download_collection.find_one_and_update({'_id': download['_id']}, {'$set': {'new_name': new_name}})

                if result is not None:
                    return

        print("Trying to update something that doesn't exist")

    def remove_from_blacklist_with_url(self, url: str):
        if not self.check_if_url_exists(url, self.blacklist_collection):
            return

        self.blacklist_collection.delete_many({
            'url': url
        })

    def remove_from_playlists_with_url(self, url: str):
        if not self.check_if_url_exists(url, self.playlist_collection):
            return

        self.playlist_collection.delete_many({
            'url': url
        })

    def get_all_blacklist_urls(self) -> List[str]:
        return [element['url'] for element in self.blacklist_collection.find({})]

    def get_all_downloaded_urls(self) -> List[str]:
        return [element['url'] for element in self.download_collection.find({})]

    def get_all_playlist_urls(self) -> List[str]:
        return [element['url'] for element in self.playlist_collection.find({})]
