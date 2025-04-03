import traceback
import requests
import logging
import time
import pandas as pd
from startup.gps_telemetry_validation_service import GpsTelemetryValidationService
from config.config import config_logger, load_config
from communication.rabbitmq import RabbitMQ
from communication.mongodb import MongoDB
from communication.protocol import ROUTING_KEY_BUS_ROUTE_UPDATES, ROUTING_KEY_GPS_TELEMETRY_VALIDATION_SERVICE, STM_API_URL, STM_API_HEADER
from google.transit.gtfs_realtime_pb2 import FeedMessage
from protobuf_to_dict import protobuf_to_dict

config_logger("config/logging.conf")

def to_queue_format(_bytes) -> dict:
    return {
        "source": "stm_api_bus_update",
        "time": time.time_ns(),
        "data": _bytes
    }

def flatten_response(data:list[dict]) -> list[dict]:
    flatten_data = []
    for entity in data:
        flatten_data.append(pd.json_normalize(entity).T.to_dict()[0])
    return flatten_data

class RoutingService:

    def __init__(self, rabbitmq_config:dict=None, mongodb_config:dict=None, url:str=None, headers:dict=None):
        self.logger = logging.getLogger("RoutingService")
        default_config = load_config("config/startup.conf")
        if rabbitmq_config is None:
            self.logger.error("RabbitMQ config value is empty, reverting to default configs.")
            rabbitmq_config = default_config['rabbitmq']

        if mongodb_config is None:
            self.logger.error("MongoDB config value is empty, reverting to default configs.")
            mongodb_config = default_config["mongodb"]

        self.rabbitmq_client = RabbitMQ(**rabbitmq_config)
        self.mongodb_client = MongoDB(**mongodb_config)
        self.gps_telemetry_service = GpsTelemetryValidationService(self.mongodb_client)
        self.url = STM_API_URL if not url else url
        self.headers = STM_API_HEADER if not headers else headers
        self.bus_route_queue_names = {}


    def setup(self):
        self.rabbitmq_client.connect_to_server()
        self.logger.info("RabbitMQ connected.")
        self.bus_route_queue_names['BusRoutesUpdates'] = self.rabbitmq_client.declare_local_queue(routing_key=ROUTING_KEY_BUS_ROUTE_UPDATES)


    def cleanup(self):
        self.logger.info("RabbitMQ connection cleaning up.")
        self.rabbitmq_client.close()


    def extract_timestamp(self, _data:dict) -> int:
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            self.logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def fetch_bus_route_data(self):
        feed = FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)
        return feed


    def process_response(self, feed, route_ids:list[int]=None, sort:bool=True, flatten:bool=True) -> list[dict]:
        data = []
        # Convert to dictionary from the original protobuf feed
        feed_dict = protobuf_to_dict(feed)

        if not route_ids:
            route_ids = []
        self.logger.info(f"Processing response for bus routes: {route_ids}")

        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                self.logger.debug(f"Retrieved entity: {entity}")

                route_id = int(entity['vehicle']['trip']['route_id'])
                if (not route_ids) or (route_id in route_ids) :
                    data.append(entity)
        if sort:
            data.sort(key=self.extract_timestamp, reverse=True)

        if flatten:
            data = flatten_response(data)
        self.logger.info("Finished processing response.")
        return data


    def publish_to_queue(self, _data: list[dict], start_time: float):
        message = to_queue_format(_data)
        self.logger.info(f"Message sent to queues: {self.bus_route_queue_names}.")
        self.rabbitmq_client.send_message(self.bus_route_queue_names['BusRoutesUpdates'], message)
        self.logger.info(f"Elapsed after message sent: {time.time() - start_time :.4f}s")


    def fetch_by_route_id(self, route_id: int) -> list[dict]:
        return self.process_response(self.fetch_bus_route_data(), [route_id])


    def fetch_by_route_ids(self, route_ids: list[int]) -> list[dict]:
        return self.process_response(self.fetch_bus_route_data(), route_ids)


    def fetch_and_update_route(self, execution_interval, route_ids:list[int]=None, strict_interval=False) -> None:

        try:
            while True:
                start = time.time()
                data = self.process_response(self.fetch_bus_route_data(), route_ids)

                # Validate GPS Telemetry
                data = self.gps_telemetry_service.validate_telemetry(to_queue_format(data))

                if "data" in data:
                    # Publish to queue
                    self.publish_to_queue(data["data"], start)

                    # Store records
                    self.mongodb_client.save(data["data"])
                else: # Log error
                    self.logger.error(f"GPS telemetry validation service returned: {data}")

                self.logger.info("Waiting for next execution cycle ...")
                elapsed = time.time() - start

                if elapsed > execution_interval:
                    exec_time = elapsed - execution_interval
                    msg = f"Control step taking {exec_time}s more than specified interval {execution_interval}s. Please specify higher interval."
                    self.logger.error(msg)

                    if strict_interval:
                        raise ValueError(execution_interval)
                else:
                    time.sleep(execution_interval - elapsed)
        except:
            self.cleanup()
            raise


    def start(self, execution_interval, route_ids:list[int]=None):
        self.setup()
        while True:
            try:
                self.fetch_and_update_route(execution_interval, route_ids)
            except KeyboardInterrupt:
                exit(0)

            except Exception as e:
                self.logger.error(f"The following exception occurred: {e}")
                traceback.print_tb(e.__traceback__)
                exit(0)