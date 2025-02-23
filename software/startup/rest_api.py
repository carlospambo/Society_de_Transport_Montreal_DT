from flask import Flask
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict
from multiprocessing import Process
import requests
import logging
import json
import os

STM_API_URL = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"

class DataFetcher:

    def __init__(self, url: str, headers: dict = None, verbose: bool = False):
        self.url = url
        self.headers = {} if headers is None else headers
        self._verbose = verbose
        self._l = logging.getLogger("DataFetcher")


    def _extract_timestamp(self, _data:dict) -> int:
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            if self._verbose:
                self._l.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def _process(self, feed, route_ids: list[int] = None, sort: bool = True) -> str:
        data = []
        feed_dict = protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed

        if not route_ids:
            route_ids = []
        if self._verbose:
            self._l.info(f"Process response for bus routes: {route_ids}")

        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                if self._verbose:
                    self._l.info(f"Retrieved entity: {entity}")

                route_id = int(entity['vehicle']['trip']['route_id'])
                if (not route_ids) or (route_id in route_ids) :
                    data.append(entity)

        if sort:
            data.sort(key=self._extract_timestamp, reverse=True)

        return json.dumps(data)


    def _fetch_feed(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)

        return feed


    def fetch_by_route_id(self, route_id: int) -> str:
        return self._process(self._fetch_feed(), [route_id])


    def fetch_by_route_ids(self, route_ids: list[int]) -> str:
        return self._process(self._fetch_feed, route_ids)

    def fetch_all(self) -> str:
        return self._process(self._fetch_feed)


app = Flask(__name__)
stm_data_fetcher = DataFetcher(STM_API_URL, {
    'apiKey': os.environ["STM_API_KEY"],
    'Accept': 'application/x-protobuf'
})

@app.route('/api/route/<int:route_id>', methods = ['GET'])
def fetch_by_id(route_id):
    return stm_data_fetcher.fetch_by_route_id(route_id=route_id)


@app.route('/api/vehicle/<int:vehicle_id>', methods = ['GET'])
def fetch_by_vehicle_id(vehicle_id):
    raise NotImplementedError("Method not yet implemented!")


def start_api() -> None:
    app.run(debug = True)


if __name__ == '__main__':
    start_api()