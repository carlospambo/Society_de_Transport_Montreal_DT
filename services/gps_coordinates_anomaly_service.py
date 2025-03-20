import sys
import os
import logging
import math

# Configure python path to load modules
# Get the current working directory. Should be 'services'
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

from communication.protocol import ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE
from communication.rpc_server import RPCServer
from communication.mongodb import MongoDB
from config.config import load_config, config_logger


EARTH_RADIUS = 6371 # Radius of the Earth in Kilometers
MAX_ALLOW_DIST = 0.1 # Maximum allowed distance in Kilometers

class GPSCoordinatesAnomalyService(RPCServer):
    """
    This is a server service that validates a list of latitude and longitude coordinates from the buses.
    """
    def __init__(self, rabbitmq_config, mongodb_config):
        super().__init__(**rabbitmq_config)
        # change collection name
        mongodb_config["collection_name"] = "bus_stops"

        self.mongodb = MongoDB(**mongodb_config)
        self._logger = logging.getLogger("GPSCoordinatesAnomalyService")


    def setup(self) -> None:
        super(GPSCoordinatesAnomalyService, self).setup(routing_key=ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE, queue_name=ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE)
        self._logger.info("GPSCoordinatesAnomalyService setup complete.")


    @staticmethod
    def _deg_to_rad(x):
        return x * math.pi / 180


    def _distance(self, from_coordinates:tuple, to_coordinates:tuple):
        from_lat, from_lng = from_coordinates[0], from_coordinates[1]
        to_lat, to_lng = to_coordinates[0], to_coordinates[1]

        half_d_lat = self._deg_to_rad((to_lat - from_lat) / 2)
        half_d_lon = self._deg_to_rad((to_lng - from_lng) / 2)

        a = (math.sin(half_d_lat) ** 2 + math.cos(self._deg_to_rad(from_lat)) * math.cos(self._deg_to_rad(to_lat)) * math.sin(half_d_lon) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return EARTH_RADIUS * c


    def validate_gps_coordinates(self, payload:dict, callback_func) -> None:
        """
        This is the method that will be invoked by the RPCServer class when a message arrives in the RabbitMQ queue.
        The 'callback_func' is a function that we can call to send the results back to the client that sent the message.
        """
        self._logger.debug(f"Validate_coordinates called. Received values: {payload}")

        try:
            assert 'data' in payload, "Payload dictionary mus contain 'data' field."

            data = payload['data']
            assert 'route_id' in data, "Data dictionary must contain 'route_id' field."
            assert 'latitude' in data, "Data dictionary must contain 'latitude' field."
            assert 'longitude' in data, "Data dictionary must contain 'longitude' field."
            assert 'stop_sequence' in data, "Data dictionary must contain 'stop_sequence' field."

            results = self.mongodb.find({'route_id': int(data['route_id'])})
            results = list(results)

            if results and len(results) > 0 and 'routes' in results[0]:
                self._logger.debug(f"Database returned: {results[0]}")

                bus_stop = results[0]['routes'][data['stop_sequence'] - 1]

                dist = self._distance((bus_stop['latitude'], bus_stop['longitude']), (data['latitude'], data['longitude']))

                message = {"results": 'OK'if dist > MAX_ALLOW_DIST else 'ANOMALY'}

                self._logger.debug(f"Validate results, sending: {message} back.")

            else:
                message = {"error": 'No data found in the database.'}
                self._logger.error("No data found in the database. Cannot validate coordinates. Returning error")

        except Exception as e:
            message = {"error": f"{str(e)}"}
            self._logger.error(f"{str(e)}")

        # send results back
        callback_func(message)


if __name__ == "__main__":

    # Get a path to the config directory used in the DT:
    conf_path = os.path.join(os.path.dirname(os.getcwd()), 'software', 'config')

    # Get a path to the logging.conf and startup.conf files used in the DT:
    logging_conf_path = conf_path +  '/logging.conf'
    startup_conf_path = conf_path +  '/startup.conf'

    assert os.path.exists(startup_conf_path), 'startup.conf file not found'
    assert os.path.exists(logging_conf_path), 'logging.conf file not found'

    # Get logging configuration
    config_logger(logging_conf_path)

    # The startup.conf comes from the DT repository.
    configs = load_config(startup_conf_path)

    # Start the service
    service = GPSCoordinatesAnomalyService(configs["rabbitmq"], configs["mongodb"])
    service.setup()
    service.start_serving()