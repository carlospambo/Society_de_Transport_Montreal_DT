from turtledemo.chaos import coosys

import pymongo.errors
from pymongo import MongoClient
import logging

class MongoDB:

    def __init__(self, conn_str=None):
        self._logger = logging.getLogger("MongoDbClient")
        try:
            self._db_client = MongoClient(conn_str)
        except pymongo.errors.ConnectionFailure as e:
            self._logger.error(f"Unable to connect to {conn_str}", e)
            raise pymongo.errors.ConnectionFailure("")

    def check_db_exists(self, database_name):
        if database_name not in self._db_client.list_database_names():
            self._logger.info(f"{database_name} database exists in the collection.")
            return True
        else:
            return False

    def insert_one(self, data):
        return


    def insert_many(self, data):
        return