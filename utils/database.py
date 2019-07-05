from typing import List, Dict, Optional

import pymongo
from pymongo import database
from pymongo.collection import Collection

from models import DatabaseOptions
from utils.text_processing import calculate_similarity, clean_string, calculate_tfidf
from bson.objectid import ObjectId


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
        song_names = [(index, song["new_name"]) for index, song in enumerate(downloaded_songs) if song.get("new_name") is not None]
        song_old_names = [(index, song["name"]) for index, song in enumerate(downloaded_songs)]

        results = calculate_tfidf(name, song_names)
        filtered_results = {index: result for index, result in enumerate(results) if result > 0.5}
        old_results = calculate_tfidf(name, song_old_names)
        filtered_old_results = {index: result for index, result in enumerate(old_results) if result > 0.5}
        combined_results = set(list(filtered_old_results.keys()) + list(filtered_results.keys()))
        search_result: List[Dict[str, Optional[str]]] = []

        for index, song in enumerate(downloaded_songs):
            if index in combined_results:
                similarity = max(filtered_results.get(index, 0), filtered_old_results.get(index, 0))
            elif song.get("new_name") is not None:
                similarity = max(calculate_similarity(name, song["new_name"]), calculate_similarity(name, song['name']))
            else:
                similarity = calculate_similarity(name, song['name'])

            if similarity >= 0.5:
                search_result.append({
                    'name': song['name'],
                    'url': song['url'],
                    'new_name': song.get('new_name'),
                    'similarity': similarity,
                    'id': str(song['_id'])
                })

        return search_result

    def get_download_by_id(self, oid: str):
        return self.download_collection.find_one({"_id": ObjectId(oid)})

    def delete_from_downloaded(self, oid: str):
        self.download_collection.delete_one({"_id": ObjectId(oid)})

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
