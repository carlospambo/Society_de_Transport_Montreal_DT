import sys
import os
import logging

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

from communication.rpc_server import RPCServer
from communication.mongodb import MongoDB
from config.config import load_config, config_logger
from enum import Enum

class BusStopOrder(Enum):
    STOP_SEQUENCE = 'SEQUENCE'
    STOP_NAME = 'NAME'


class CoordinatesAnomalyService(RPCServer):
    """
    This is a server service that validates a list of latitude and longitude coordinates from the buses.
    """
    def __init__(self, rabbitmq_config, mongodb_config):
        super().__init__(**rabbitmq_config)
        self.mongodb = MongoDB(**mongodb_config)
        self._logger = logging.getLogger("CoordinatesAnomalyService")


    def setup(self) -> None:
        super(CoordinatesAnomalyService, self).setup(routing_key='coordinates.anomaly.service', queue_name='coordinates.anomaly.service')
        self._logger.info("CoordinatesAnomalyService setup complete.")


    def get_stops_by_route_id(self, route_id, order_by:BusStopOrder=BusStopOrder.STOP_SEQUENCE):
        bus_stops = self.mongodb.find({'route_id': route_id})

        if order_by == BusStopOrder.STOP_SEQUENCE:
            bus_stops.
        else:
            bus_stops.

        return bus_stops


    def validate_coordinates(self, data:dict, callback_func) -> None:
        """
        This is the method that will be invoked by the RPCServer class when a message arrives in the RabbitMQ queue.
        The 'callback_func' is a function that we can call to send the results back to the client that sent the message.
        """
        self._logger.info(f"validate_coordinates called. Received values: {data}")

        if data:

            message = {"results": 'ok'}

        else:
            self._logger.warning("Received an empty dictionary. Cannot validate coordinates. Returning error")
            message = {"error": "Received an empty dictionary of values. Cannot validate coordinates."}

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
    service = CoordinatesAnomalyService(rabbitmq_config=configs["rabbitmq"])
    service.setup()
    service.start_serving()