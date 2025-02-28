from flask import Flask
from startup.stm_api_service import StmApiService
from config.config import config_logger, load_config
from communication.protocol import STM_API_URL, STM_API_HEADER
import logging


app = Flask(__name__)

@app.route('/api/route-updates/<int:route_id>', methods = ['GET'])
def fetch_updates_by_route_id(route_id):
    return stm_api_service.fetch_by_route_id(route_id=route_id)


@app.route('/api/vehicle/<int:vehicle_id>', methods = ['GET'])
def fetch_updates_by_vehicle_id(vehicle_id):
    raise NotImplementedError("Method not yet implemented!")


@app.route('/api/routes/<int:route_id>', methods = ['GET'])
def fetch_route_by_route_id(route_id):
    raise NotImplementedError("Method not yet implemented!")


@app.route('/api/routes>', methods = ['GET'])
def fetch_all_routes():
    raise NotImplementedError("Method not yet implemented!")


def start_http_api() -> None:
    app.run(debug = True)


if __name__ == '__main__':
    config_logger("config/logging.conf")
    logger = logging.getLogger("RestAPI")
    stm_api_service = StmApiService(STM_API_URL, STM_API_HEADER)
    start_http_api()