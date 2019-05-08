from typing import List, Dict

import pymongo
from pymongo import database
from models import DatabaseOptions

from urllib.parse import quote


class DatabaseHandler:
    blacklist_collection: pymongo.collection
    download_collection: pymongo.collection
    database: pymongo.database.Database
    client: pymongo.MongoClient

    def __init__(self, options: DatabaseOptions):
        # self.client = pymongo.MongoClient(
        #     quote(f"mongodb://{options.database_user}:{options.database_password}@{options.database_uri}"))

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

    def add_many_to_collection(self, urls: List[str], names: List[str], collection: pymongo.collection):
        for url in urls:
            if self.check_if_url_exists(url, self.download_collection):
                return

        collection.insert_many([

            {
                'url': url,
                'name': name
            }

            for url, name in zip(urls, names)
        ])

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

    def get_all_blacklist(self) -> List[Dict[str, str]]:
        return self.blacklist_collection.find({}).to_list(length=10000)
