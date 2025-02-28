import requests
import logging
import json
import time
import pandas as pd
from config.config import config_logger, load_config
from communication.rabbitmq import RabbitMQ
from communication.mongodb import MongoDB
from communication.protocol import ROUTING_KEY_BUS_ROUTE, STM_API_URL, STM_API_HEADER
from google.transit.gtfs_realtime_pb2 import FeedMessage
from protobuf_to_dict import protobuf_to_dict



CTRL_EXEC_INTERVAL = 18.0

def flatten_response(data:list[dict]) -> list[dict]:
    flatten_data = []
    for entity in data:
        # flatten_d = {"vehicle.id": entity["id"]}
        # if 'vehicle' in entity:
        #     flatten_d["vehicle.current_stop_sequence"] = entity['vehicle']['current_stop_sequence'] if 'current_stop_sequence' in entity['vehicle'] else None
        #     flatten_d["vehicle.current_status"] = entity['vehicle']['current_status'] if 'current_status' in entity['vehicle'] else None
        #     flatten_d["vehicle.occupancy_status"] = entity['vehicle']['occupancy_status'] if 'occupancy_status' in entity['vehicle'] else None
        #     flatten_d["timestamp"] = entity['vehicle']['timestamp'] if 'timestamp' in entity['vehicle'] else None
        #
        #     if 'trip' in entity['vehicle']:
        #         flatten_d["vehicle.trip.trip_id"] = entity['vehicle']['trip']['trip_id'] if 'trip_id' in entity['vehicle']['trip'] else None
        #         flatten_d["vehicle.trip.start_time"] = entity['vehicle']['trip']['start_time'] if 'start_time' in entity['vehicle']['trip'] else None
        #         flatten_d["vehicle.trip.start_date"] = entity['vehicle']['trip']['start_date'] if 'start_date' in entity['vehicle']['trip'] else None
        #
        #     if 'position' in entity['vehicle']:
        #         flatten_d["vehicle.position.latitude"] = entity['vehicle']['position']['latitude'] if 'latitude' in entity['vehicle']['position'] else None
        #         flatten_d["vehicle.position.longitude"] = entity['vehicle']['position']['longitude'] if 'longitude' in entity['vehicle']['position'] else None
        #         flatten_d["vehicle.position.bearing"] = entity['vehicle']['position']['bearing'] if 'bearing' in entity['vehicle']['position'] else None
        #         flatten_d["vehicle.position.speed"] = entity['vehicle']['position']['speed'] if 'speed' in entity['vehicle']['position'] else None
        flatten_data.append(pd.json_normalize(entity).T.to_dict()[0])

    return flatten_data

class RouteService:

    def __init__(self, rabbitmq_config:dict=None, mongodb_config:dict=None, url:str = None, headers:dict = None):
        self._logger = logging.getLogger("RouteService")
        default_config = load_config("config/startup.conf")
        if rabbitmq_config is None:
            self._logger.error("RabbitMQ config value is empty, reverting to default configs.")
            rabbitmq_config = default_config['rabbitmq']

        if mongodb_config is None:
            self._logger.error("MongoDB config value is empty, reverting to default configs.")
            mongodb_config = default_config["mongodb"]

        self.rabbitmq = RabbitMQ(**rabbitmq_config)
        self.mongodb = MongoDB(**mongodb_config)
        self.url = url
        self.headers = {} if not headers else headers
        self.bus_route_queue_name = ""


    def setup(self):
        self.rabbitmq.connect_to_server()
        self._logger.info("RabbitMQ connected.")
        self.bus_route_queue_name = self.rabbitmq.declare_local_queue(routing_key=ROUTING_KEY_BUS_ROUTE)


    def cleanup(self):
        self._logger.info("RabbitMQ connection cleaning up.")
        self.rabbitmq.close()


    def _fetch_bus_route_data(self):
        feed = FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)
        return feed


    def _extract_timestamp(self, _data:dict) -> int:
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            self._logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0

    def _process_response(self, feed, route_ids:list[int]=None, sort:bool=True, flatten:bool=True) -> list[dict]:
        data = []
        feed_dict = protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed

        if not route_ids:
            route_ids = []

        self._logger.info(f"Process response for bus routes: {route_ids}")

        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                self._logger.debug(f"Retrieved entity: {entity}")

                route_id = int(entity['vehicle']['trip']['route_id'])
                if (not route_ids) or (route_id in route_ids) :
                    data.append(entity)

        if sort:
            data.sort(key=self._extract_timestamp, reverse=True)

        if flatten:
            data = flatten_response(data)

        return data

    def send_message(self, _data: list[dict], start_time: float):
        timestamp = time.time_ns()
        message = {
            "source": "stm_api_bus_update",
            "time": timestamp,
            "tags": {
                "source": "stm_api_bus_update"
            },
            "data": json.dumps(_data)
        }

        self.rabbitmq.send_message(ROUTING_KEY_BUS_ROUTE, message)
        self._logger.debug(f"Message sent to {ROUTING_KEY_BUS_ROUTE}.")
        self._logger.debug(message)
        self._logger.debug(f"Elapsed after message sent: {time.time() - start_time}s")


    def store_records(self, _data: list[dict]):
        self.mongodb.save(_data)


    def fetch_by_route_id(self, route_id: int) -> list[dict]:
        return self._process_response(self._fetch_bus_route_data(), [route_id])


    def fetch_by_route_ids(self, route_ids: list[int]) -> list[dict]:
        return self._process_response(self._fetch_bus_route_data(), route_ids)


    def fetch_and_update_route(self, exec_interval=CTRL_EXEC_INTERVAL, strict_interval=False) -> None:

        try:
            while True:
                start = time.time()
                data = self._process_response(self._fetch_bus_route_data())
                self.send_message(data, start)
                self.store_records(data)

                elapsed = time.time() - start

                if elapsed > exec_interval:
                    self._logger.error(
                        f"Control step taking {elapsed - exec_interval}s more than specified interval {exec_interval}s. Please specify higher interval."
                    )
                    if strict_interval:
                        raise ValueError(exec_interval)
                else:
                    time.sleep(exec_interval - elapsed)
        except:
            self.cleanup()
            raise


def start_route_service_update():
    config_logger("config/logging.conf")
    logger = logging.getLogger("RouteService")

    service = RouteService(url=STM_API_URL, headers=STM_API_HEADER)
    service.setup()
    while True:
        try:
            service.fetch_and_update_route()
        except KeyboardInterrupt:
            exit(0)
        except Exception as exc:
            logger.error("The following exception occurred. Attempting to reconnect.")
            logger.error(exc)
            time.sleep(1.0)


if __name__ == '__main__':
    start_route_service_update()