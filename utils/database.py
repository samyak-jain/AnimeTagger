from typing import List, Dict

import motor.motor_asyncio
from models import DatabaseOptions


class DatabaseHandler:
    blacklist_collection: motor.motor_asyncio.AsyncIOMotorCollection
    download_collection: motor.motor_asyncio.AsyncIOMotorCollection
    database: motor.motor_asyncio.AsyncIOMotorDatabase
    client: motor.motor_asyncio.AsyncIOMotorClient

    def __init__(self, options: DatabaseOptions):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb://{options.database_user}:"
                                                             f"{options.database_password}@{options.database_uri}")
        self.database = self.client[options.database_name]
        self.download_collection = self.database["downloaded"]
        self.blacklist_collection = self.database["blacklist"]

    async def add_to_downloaded(self, url: str, name: str):
        if self.check_if_url_exists(self.download_collection):
            return

        await self.download_collection.insert_one({
            'url': url,
            'name': name
        })

    async def add_many_to_downloaded(self, urls: List[str], names: List[str]):
        for url in urls:
            if self.check_if_url_exists(self.download_collection):
                return

        await self.download_collection.insert_many([

            {
                'url': url,
                'name': name
            }

            for url, name in zip(urls, names)
        ])

    async def add_to_blacklist(self, url: str, name: str):
        if self.check_if_url_exists(self.blacklist_collection):
            return

        await self.blacklist_collection.insert_one({
            'url': url,
            'name': name
        })

    async def remove_from_blacklist_with_url(self, url: str):
        if not self.check_if_url_exists(self.blacklist_collection):
            return

        await self.blacklist_collection.delete_many({
            'url': url
        })

    async def remove_from_blacklist_with_name(self, name: str):
        if not self.check_if_name_exists(self.blacklist_collection):
            return

        await self.blacklist_collection.delete_many({
            'name': name
        })

    @staticmethod
    async def check_if_url_exists(url: str, collection: motor.motor_asyncio.AsyncIOMotorCollection) -> bool:
        cursor: motor.motor_asyncio.AsyncIOMotorCursor = collection.find({
            'url': url
        })

        documents: List[Dict[str, str]] = await cursor.to_list(length=100)

        return not (len(documents) < 1)

    @staticmethod
    async def check_if_name_exists(name: str, collection: motor.motor_asyncio.AsyncIOMotorCollection) -> bool:
        cursor: motor.motor_asyncio.AsyncIOMotorCursor = collection.find({
            'name': name
        })

        documents: List[Dict[str, str]] = await cursor.to_list(length=100)

        return not (len(documents) < 1)
