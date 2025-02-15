
from google.transit import gtfs_realtime_pb2
import requests
import json
import logging
import protobuf_to_dict
from software.communication.rabbitmq import RabbitMQ
from software.storage.mongodb import MongoClient


class DataFetcher:

    def __init__(self, rabbitmq: RabbitMQ, mongodb: MongoClient, url: str, headers: dict = None, bus_ids: list = None):
        self.bus_ids = [] if bus_ids is None else bus_ids
        self.url = url
        self.headers = {} if headers is None else headers
        self._rabbitmq = rabbitmq
        self._mongodb = mongodb
        self._logger = logging.getLogger("DataFetcher")


    def extract_timestamp(self, _data:dict):
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            self._logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def process(self, feed):
        vehicles_json = []
        feed_dict = protobuf_to_dict.protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed
        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                bus_id = int(entity['vehicle']['trip']['vehicle'])
                if bus_id in self.bus_ids:
                    vehicles_json.append(entity)

        vehicles_json.sort(key=self.extract_timestamp, reverse=True)

        return vehicles_json

    def fetch(self, logger):
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)
        # TODO :: Send to RabbitMQ queue and store to MongoDB
        logger.info(f"JSON: {json.dumps(self.process(feed))}")

        # self._rabbitmq.send_message()
        # self._mongodb.insert_many()


