import sys
import os
import logging
import math
import time

# Get the current working directory. Should be 'services', configure python path to load modules
current_dir = os.getcwd()

assert os.path.basename(current_dir) == 'services', 'Current directory is not services'

# Get the parent directory. Should be the root of the repository
parent_dir = os.path.dirname(current_dir)

# The root of the repo should contain the 'software' folder. Otherwise, something went wrong.
assert os.path.exists(os.path.join(parent_dir, 'software')), 'software folder not found in the repository root'

stm_dt_software_dir = os.path.join(parent_dir, 'software')

assert os.path.exists(stm_dt_software_dir), 'stm_dt/software directory not found'

# Add the parent directory to sys.path
sys.path.append(stm_dt_software_dir)

from communication.protocol import ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE, EARTH_RADIUS, MAX_ALLOW_DISTANCE
from communication.rpc_server import RPCServer
from communication.mongodb import MongoDB
from config.config import load_config, config_logger


class GpsCoordinatesAnomalyService(RPCServer):

    def __init__(self, rabbitmq_config, mongodb_config):
        super().__init__(**rabbitmq_config)
        self.mongodb = MongoDB(**mongodb_config)
        self._logger = logging.getLogger("GpsCoordinatesAnomalyService")


    def setup(self) -> None:
        super(GpsCoordinatesAnomalyService, self).setup(
            routing_key=ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE,
            queue_name=ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE
        )
        self._logger.info("GpsCoordinatesAnomalyService setup complete.")


    @staticmethod
    def _deg_to_rad(x):
        return x * math.pi / 180


    def _distance(self, from_coordinates:tuple, to_coordinates:tuple):
        from_lat, from_lng = from_coordinates[0], from_coordinates[1]
        to_lat, to_lng = to_coordinates[0], to_coordinates[1]

        half_d_lat = self._deg_to_rad((to_lat - from_lat) / 2)
        half_d_lon = self._deg_to_rad((to_lng - from_lng) / 2)

        a = (math.sin(half_d_lat) ** 2 + math.cos(self._deg_to_rad(from_lat)) * math.cos(self._deg_to_rad(to_lat)) * math.sin(half_d_lon) ** 2)

        return EARTH_RADIUS * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


    def validate_gps_coordinates(self, payload:dict, callback_func) -> None:
        self._logger.debug(f"'validate_gps_coordinates' called. Received values: {payload}")

        response = {"source": "stm_gps_coordinates_anomaly_service"}

        if 'data' not in payload:
            response["time"] = time.time_ns()
            response["error"] = "Payload dictionary must contain 'data' field"

            # Send error
            callback_func(response)

        for i in enumerate(payload["data"]):

            try:
                assert 'vehicle.trip.route_id' in payload["data"][i], "Data dictionary must contain 'vehicle.trip.route_id' field."
                assert 'vehicle.position.latitude' in payload["data"][i], "Data dictionary must contain 'vehicle.position.latitude' field."
                assert 'vehicle.position.longitude' in payload["data"][i], "Data dictionary must contain 'vehicle.position.longitude' field."
                assert 'vehicle.current_stop_sequence' in payload["data"][i], "Data dictionary must contain 'vehicle.current_stop_sequence' field."

                route_id =  int(payload["data"][i]['vehicle.trip.route_id'])
                results = self.mongodb.database["bus_stops"].find({"route_id": route_id})
                results = list(results)

                if results and len(results) > 0 and 'routes' in results[0]:
                    self._logger.debug(f"Database returned: {results[0]}")

                    bus_stop = results[0]['routes'][payload["data"][i]['vehicle.current_stop_sequence'] - 1]
                    form_coordinates = (bus_stop['latitude'], bus_stop['longitude'])
                    to_coordinates = (payload["data"][i]['vehicle.position.latitude'], payload["data"][i]['vehicle.position.longitude'])
                    distance = self._distance(form_coordinates, to_coordinates)

                    payload["data"][i]["vehicle.position.coordinates.status"] = "OK" if distance <= MAX_ALLOW_DISTANCE else "ANOMALY"

                else:
                    payload["data"][i]["vehicle.position.coordinates.status"] = "NOT_FOUND"
                    self._logger.error(f"No data found in the database. Cannot validate coordinates for route : {route_id}")

            except AssertionError as e:
                self._logger.error(f"{str(e)} for : {payload['data'][i]}")

        response["time"] = time.time_ns()
        response["data"] = payload["data"]

        # Store to a database
        self._logger.debug("Start writing to database")

        self.mongodb.database["gps_coordinates_validation"].insert_many(response["data"])

        self._logger.debug("Finished writing to database")

        self.logger.debug(f"Validated results, sending back: {response}")

        # Send results back
        callback_func(response)


if __name__ == "__main__":

    # Get a path to the config directory used in the DT:
    conf_path = os.path.join(os.path.dirname(os.getcwd()), 'software', 'config')

    # Get a path to the logging.conf and startup.conf files used in the DT:
    logging_conf_path = conf_path +  '/logging.conf'
    startup_conf_path = conf_path +  '/startup.conf'

    assert os.path.exists(startup_conf_path), 'startup.conf file not found.'
    assert os.path.exists(logging_conf_path), 'logging.conf file not found.'

    # Get logging configuration
    config_logger(logging_conf_path)

    # The startup.conf comes from the DT repository.
    configs = load_config(startup_conf_path)

    # Start the service
    service = GpsCoordinatesAnomalyService(configs["rabbitmq"], configs["mongodb"])
    service.setup()
    service.start_serving()