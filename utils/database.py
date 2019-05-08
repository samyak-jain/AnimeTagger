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

    def add_to_downloaded(self):
        pass

    def add_to_blacklist(self):
        pass

    def remove_from_blacklist(self):
        pass
