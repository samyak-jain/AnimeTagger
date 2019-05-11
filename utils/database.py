from typing import List, Dict

import pymongo
from pymongo import database

from models import DatabaseOptions


class DatabaseHandler:
    blacklist_collection: pymongo.collection
    download_collection: pymongo.collection
    database: pymongo.database.Database
    client: pymongo.MongoClient

    def __init__(self, options: DatabaseOptions):
        self.client = pymongo.MongoClient(options.database_uri, options.port)
        self.database = self.client[options.database_name]
        self.database.authenticate(options.database_user, options.database_password)
        self.download_collection = self.database["downloaded"]
        self.blacklist_collection = self.database["blacklist"]

    def add_to_downloaded(self, url: str, name: str):
        if self.check_if_url_exists(url, self.download_collection):
            return

        self.download_collection.insert_one({
            'url': url,
            'name': name
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

    def add_many_to_collection(self, urls: List[str], names: List[str], collection: pymongo.collection):
        urls_not_added_yet: List[str] = []

        for url in urls:
            if not self.check_if_url_exists(url, collection):
                urls_not_added_yet.append(url)

        collection.insert_many([

            {
                'url': url,
                'name': name
            }

            for url, name in zip(urls, names)
        ])

    def update_downloaded(self, old_name: str, new_name: str):
        result = self.download_collection.find_one_and_update({'name': old_name}, {'$set': {'new_name': new_name}})

        if result is None:
            print("Trying to update something that doesn't exist")

    def add_to_blacklist(self, url: str, name: str):
        if self.check_if_url_exists(url, self.blacklist_collection):
            return

        self.blacklist_collection.insert_one({
            'url': url,
            'name': name
        })

    def remove_from_blacklist_with_url(self, url: str):
        if not self.check_if_url_exists(url, self.blacklist_collection):
            return

        self.blacklist_collection.delete_many({
            'url': url
        })

    def remove_from_blacklist_with_name(self, name: str):
        if not self.check_if_name_exists(name, self.blacklist_collection):
            return

        self.blacklist_collection.delete_many({
            'name': name
        })

    @staticmethod
    def check_if_url_exists(url: str, collection: pymongo.collection) -> bool:
        cursor: pymongo.cursor = collection.find({
            'url': url
        })

        documents: List[Dict[str, str]] = list(cursor)

        return not (len(documents) < 1)

    @staticmethod
    def check_if_name_exists(name: str, collection: pymongo.collection) -> bool:
        cursor: pymongo.cursor = collection.find({
            'name': name
        })

        documents: List[Dict[str, str]] = list(cursor)

        return not (len(documents) < 1)

    def get_all_blacklist(self) -> List[str]:
        return [element['url'] for element in self.blacklist_collection.find({})]

    def get_all_downloaded(self) -> List[str]:
        return [element['url'] for element in self.download_collection.find({})]
