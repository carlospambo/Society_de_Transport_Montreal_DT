from pymongo.errors import BulkWriteError, ConnectionFailure, OperationFailure
from pymongo import MongoClient, InsertOne
import logging


class MongoDB:

    def __init__(self, database_name:str, collection_name:str, vhost:str=None, port:int=None, username:str=None, password:str=None, connection_str=None):
        self._logger = logging.getLogger("MongoDb")
        assert database_name, "Database name is a required field."
        assert collection_name, "Collection name is a required field."
        self._client = None
        self._database = None
        self._collection = None
        self._db_name = database_name
        self._col_name = collection_name

        if not connection_str:
            assert vhost, "Vhost is a required field when a connection string is not provided."
            assert port, "Port number is a required field when a connection string is not provided."
            assert username, "Username is a required field when a connection string is not provided."
            assert password, "Password is a required field when a connection string is not provided."
            self._connection_str = f"mongodb://{username}:{password}@{vhost}:{port}"
        else:
            self._connection_str = connection_str
        self._setup()


    def _setup(self):
        try:
            self._client = MongoClient(self._connection_str)
            self._db_exists()
            self._collection_exists()
            self._collection = self._database[self._col_name]

        except ConnectionFailure as e:
            error_msg = f"Unable to connect to {self._connection_str}/{self._db_name}/{self._col_name}, error: {str(e)}"
            self._logger.error(error_msg)
            raise ConnectionFailure(error_msg)


    def _db_exists(self):
        if self._client and self._db_name in self._client.list_database_names():
            self._database = self._client[self._db_name]
            self._logger.info(f"{self._db_name} database exists.")
        else:
            self._database = self._client[self._db_name]
            self._logger.error(f"{self._db_name} database did not exist.")


    def _collection_exists(self):
        if self._database is None:
            self._database = self._client[self._db_name]

        if self._col_name in self._database.list_collection_names():
            self._logger.info(f"{self._col_name} collection exists in database {self._db_name}.")
            self._collection = self._database[self._col_name]
        else:
            self._logger.error(f"{self._col_name} collection did not exist in database {self._db_name}.")
            self._logger.info(f"Creating collection {self._col_name} in database {self._db_name}.")
            self._collection = self._database[self._col_name]


    def save(self, data: list[dict]):
        self._logger.info("Start save ... ")

        try:
            results = self._collection.insert_many(data)
            self._logger.debug(f"Bulk write operation results: {results}")

            return results
        except BulkWriteError as e:
            self._logger.error(f"Error: {str(e)}")