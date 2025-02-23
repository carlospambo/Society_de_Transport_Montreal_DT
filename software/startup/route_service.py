import requests
import logging
import json
import time
from config.config import config_logger, load_config
from communication.rabbitmq import RabbitMQ
from communication.protocol import ROUTING_KEY_BUS_ROUTE, STM_API_URL, STM_API_HEADER
from google.transit import gtfs_realtime_pb2
from protobuf_to_dict import protobuf_to_dict


CTRL_EXEC_INTERVAL = 15.0

class RouteService:

    def __init__(self, rabbitmq_config, stm_api_url:str = None, stm_api_headers:dict = None):
        self.logger = logging.getLogger("RouteService")
        self.rabbitmq = RabbitMQ(**rabbitmq_config)
        self.url = stm_api_url
        self.headers = {} if not stm_api_headers else stm_api_headers
        self.bus_route_queue_name = ""


    def setup(self):
        self.rabbitmq.connect_to_server()
        self.logger.info("RabbitMQ connected.")
        self.bus_route_queue_name = self.rabbitmq.declare_local_queue(routing_key=ROUTING_KEY_BUS_ROUTE)


    def cleanup(self):
        self.logger.info("RabbitMQ connection cleaning up.")
        self.rabbitmq.close()


    def _fetch_bus_route_data(self):
        feed = gtfs_realtime_pb2.FeedMessage()
        response = requests.get(self.url, headers=self.headers)
        feed.ParseFromString(response.content)
        return feed


    def _extract_timestamp(self, _data:dict) -> int:
        try:
            return int(_data['vehicle']['timestamp'])
        except KeyError as e:
            self.logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def _process_response(self, feed, route_ids: list[int] = None, sort: bool = True) -> str:
        data = []
        feed_dict = protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed

        if not route_ids:
            route_ids = []

        self.logger.info(f"Process response for bus routes: {route_ids}")

        for entity in feed_dict['entity']:
            if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
                self.logger.info(f"Retrieved entity: {entity}")

                route_id = int(entity['vehicle']['trip']['route_id'])
                if (not route_ids) or (route_id in route_ids) :
                    data.append(entity)

        if sort:
            data.sort(key=self._extract_timestamp, reverse=True)

        return json.dumps(data)

    def send_message(self, _data, start_time):
        timestamp = time.time_ns()
        message = {
            "source": "stm_api_bus_update",
            "time": timestamp,
            "tags": {
                "source": "stm_api_bus_update"
            },
            "data": _data
        }

        self.rabbitmq.send_message(ROUTING_KEY_BUS_ROUTE, message)
        self.logger.debug(f"Message sent to {ROUTING_KEY_BUS_ROUTE}.")
        self.logger.debug(message)
        self.logger.debug(f"Elapsed after message sent: {time.time() - start_time}s")


    def fetch_by_route_id(self, route_id: int) -> str:
        return self._process_response(self._fetch_bus_route_data(), [route_id])


    def fetch_by_route_ids(self, route_ids: list[int]) -> str:
        return self._process_response(self._fetch_bus_route_data(), route_ids)


    def fetch_and_update_route(self, exec_interval=CTRL_EXEC_INTERVAL, strict_interval=False) -> str:

        try:
            while True:
                start = time.time()
                data = self._process_response(self._fetch_bus_route_data())
                self.send_message(data, start)
                elapsed = time.time() - start
                if elapsed > exec_interval:
                    self.logger.error(
                        f"Control step taking {elapsed - exec_interval}s more than specified interval {exec_interval}s. Please specify higher interval.")
                    if strict_interval:
                        raise ValueError(exec_interval)
                else:
                    time.sleep(exec_interval - elapsed)
        except:
            self.cleanup()
            raise



def start_route_service_update():
    config_logger("config/logging.conf")
    config = load_config("config/startup.conf")
    logger = logging.getLogger("BusRouteService")
    service = RouteService(config["rabbitmq"], STM_API_URL, STM_API_HEADER)
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