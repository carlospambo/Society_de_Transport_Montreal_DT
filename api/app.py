from flask import Flask, jsonify
from google.transit import gtfs_realtime_pb2
import requests
import logging
from protobuf_to_dict import protobuf_to_dict

STM_API_URL = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
STM_AUTH_API_KEY = "l7079a29ea698640cbbb965bc4011b80e4"


class DataFetcher:

    def __init__(self, url: str, headers: dict = None):
        self.url = url
        self.headers = {} if headers is None else headers
        self._logger = logging.getLogger("DataFetcher")


    def _extract_timestamp(self, _data:dict):
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            self._logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def _process(self, feed, bus_id):
        data = []
        feed_dict = protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed

        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                print(f"Retrieved entity: {entity}")
                route_id = int(entity['vehicle']['trip']['route_id'])
                if bus_id == route_id:
                    data.append(entity)

        data.sort(key=self._extract_timestamp, reverse=True)

        return jsonify(data)

    def fetch(self, route_id):
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)
        return self._process(feed, route_id)

# creating a Flask app
app = Flask(__name__)
stm_data_fetcher = DataFetcher(STM_API_URL, {
    'apiKey': STM_AUTH_API_KEY,
    'Accept': 'application/x-protobuf'
})

@app.route('/api/route/<int:route_id>', methods = ['GET'])
def fetch_by_id(route_id):
    return stm_data_fetcher.fetch(route_id=route_id)

@app.route('/api/vehicle/<int:vehicle_id>', methods = ['GET'])
def fetch_by_vehicle_id(vehicle_id):
    raise NotImplementedError("Method not yet implemented!")

# driver function
if __name__ == '__main__':
    app.run(debug = True)
