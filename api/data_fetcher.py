from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
import requests
import logging
import json


class DataFetcher:

    def __init__(self, url: str, headers: dict = None):
        self.url = url
        self.headers = {} if headers is None else headers
        self._logger = logging.getLogger("DataFetcher")


    def _extract_timestamp(self, _data:dict) -> int:
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            self._logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def _process(self, feed, bus_id) -> str:
        data = []
        feed_dict = protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed

        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                print(f"Retrieved entity: {entity}")
                route_id = int(entity['vehicle']['trip']['route_id'])
                if bus_id == route_id:
                    data.append(entity)

        data.sort(key=self._extract_timestamp, reverse=True)

        return json.dumps(data)


    def fetch(self, route_id) -> str:
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)
        return self._process(feed, route_id)
