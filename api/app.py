from flask import Flask
from data_fetcher import DataFetcher

STM_API_URL = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
STM_AUTH_API_KEY = "l7079a29ea698640cbbb965bc4011b80e4"

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


if __name__ == '__main__':
    app.run(debug = True)
