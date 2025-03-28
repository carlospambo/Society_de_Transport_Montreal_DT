from pymongo.errors import BulkWriteError, ConnectionFailure
from pymongo import MongoClient
import logging


class MongoDB:

    def __init__(self, database_name:str, collection_name:str, vhost:str=None, port:int=None, username:str=None, password:str=None, connection_str=None):
        self.logger = logging.getLogger("MongoDb")
        assert database_name, "Database name is a required field."
        assert collection_name, "Collection name is a required field."
        self.client = None
        self.database = None
        self.collection = None
        self.db_name = database_name
        self.col_name = collection_name

        if not connection_str:
            assert vhost, "Vhost is a required field when a connection string is not provided."
            assert port, "Port number is a required field when a connection string is not provided."
            assert username, "Username is a required field when a connection string is not provided."
            assert password, "Password is a required field when a connection string is not provided."
            self.connection_str = f"mongodb://{username}:{password}@{vhost}:{port}"
        else:
            self.connection_str = connection_str
        self.setup()


    def setup(self):
        try:
            self.client = MongoClient(self.connection_str)
            self.db_exists()
            self.collection_exists()
            self.collection = self.database[self.col_name]

        except ConnectionFailure as e:
            error_msg = f"Unable to connect to {self.connection_str}/{self.db_name}/{self.col_name}, error: {str(e)}"
            self.logger.error(error_msg)
            raise ConnectionFailure(error_msg)


    def db_exists(self):
        if self.client and self.db_name in self.client.list_database_names():
            self.database = self.client[self.db_name]
            self.logger.info(f"{self.db_name} database exists.")
        else:
            self.database = self.client[self.db_name]
            self.logger.error(f"ec{self.db_name} database did not exist.")


    def collection_exists(self):
        if self.database is None:
            self.database = self.client[self.db_name]

        if self.col_name in self.database.list_collection_names():
            self.logger.info(f"{self.col_name} collection exists in database {self.db_name}.")
            self.collection = self.database[self.col_name]
        else:
            self.logger.error(f"{self.col_name} collection did not exist in database {self.db_name}.")
            self.logger.info(f"Creating collection {self.col_name} in database {self.db_name}.")
            self.collection = self.database[self.col_name]


    def save(self, data: list[dict]):
        if not data:
            self.logger.info("Skipped writing to db, empty list provided.")
            return

        try:
            self.logger.info("Starting writing to db ... ")

            results = self.collection.insert_many(data)

            self.logger.info("Ending writing to db ... ")
            return results
        except BulkWriteError as e:
            self.logger.error(f"Error: {str(e)}")


    def find(self, _filter: dict):
        try:
            self.logger.debug(f"Start fetch from db for {_filter} ... ")

            results = self.collection.find(_filter)

            self.logger.debug(f"End fetch with results: {results}")

            return results
        except BulkWriteError as e:
            self.logger.error(f"Error: {str(e)}")