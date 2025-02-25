import pymongo.errors
from pymongo import MongoClient
import logging


class MongoDb:

    def __init__(self, database_name:str, collection_name:str, vhost:str=None, port:int=None, username:str=None, password:str=None, connection_str=None):
        self._logger = logging.getLogger("MongoDb")
        assert database_name, "Database name is a required field."
        assert collection_name, "Collection name is a required field."
        self._client = None
        self._database = None
        self._collection = None
        self._db_name= collection_name
        self._col_name = collection_name

        if not connection_str:
            assert vhost, "Vhost is a required field when a connection string is not provided."
            assert port, "Port number is a required field when a connection string is not provided."
            assert username, "Username is a required field when a connection string is not provided."
            assert password, "Password is a required field when a connection string is not provided."
            self._connection_str = f"mongodb://{username}:{password}@{vhost}:{port}/"
        else:
            self._connection_str = connection_str
        self._setup()


    def _setup(self):
        try:
            self._client = MongoClient(self._connection_str)
            self._db_exists()
            self._collection_exists()

        except (pymongo.errors.ConnectionFailure, MongoDbResourceDoesNotExist) as e:
            error_msg = f"Unable to connect to {self._connection_str}{self._db_name}/{self._col_name}, error: {str(e)}"
            self._logger.error(error_msg)
            raise pymongo.errors.ConnectionFailure(error_msg)


    def _db_exists(self):
        if self._client and self._db_name in self._client.list_database_names():
            self._logger.info(f"{self._db_name} database exists.")
        else:
            err_msg = f"{self._db_name} database does not exists."
            self._logger.error(err_msg)
            raise MongoDbResourceDoesNotExist(err_msg)


    def _collection_exists(self):
        if self._client and self._client[self._database] and self._client[self._database][self._col_name]:
            self._logger.info(f"{self._col_name} collection exists in database {self._db_name}.")
        else:
            err_msg = f"{self._col_name} collection does not exists in database {self._db_name}."
            self._logger.error(err_msg)
            raise MongoDbResourceDoesNotExist(err_msg)


    def insert_one(self, data):
        return


    def insert_many(self, data):
        return


class MongoDbResourceDoesNotExist(Exception):
    """Exception raised for non-existing MongoDb resources."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return self.message