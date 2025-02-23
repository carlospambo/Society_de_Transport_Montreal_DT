from flask import Flask
from startup.route_service import RouteService
from config.config import config_logger, load_config
from communication.protocol import STM_API_URL, STM_API_HEADER
import logging

app = Flask(__name__)

@app.route('/api/route/<int:route_id>', methods = ['GET'])
def fetch_by_id(route_id):
    return route_service.fetch_by_route_id(route_id=route_id)


@app.route('/api/vehicle/<int:vehicle_id>', methods = ['GET'])
def fetch_by_vehicle_id(vehicle_id):
    raise NotImplementedError("Method not yet implemented!")


def start_api() -> None:
    app.run(debug = True)


if __name__ == '__main__':
    config_logger("logging.conf")
    logger = logging.getLogger("RestAPI")
    config = load_config("startup.conf")
    route_service = RouteService(STM_API_URL, STM_API_HEADER)
    start_api()