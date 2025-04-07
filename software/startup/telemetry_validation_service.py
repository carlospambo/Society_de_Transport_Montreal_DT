import json
import traceback
import logging
import math
import time
from enum import Enum
from communication.protocol import EARTH_RADIUS, MAX_ALLOW_DISTANCE, ROUTING_KEY_STM_TELEMETRY_VALIDATION, ROUTING_KEY_STM_NOTIFICATION
from communication.mongodb import MongoDB
from communication.rpc_server import RPCServer
from config.config import load_config, config_logger

class CoordinateStatus(Enum):
    OK = "OK"
    ANOMALY = "ANOMALY"
    NOT_FOUND = "NOT_FOUND"

    def __str__(self):
        return f"{self.value}"

    @classmethod
    def parse_from_distance(cls, distance, max_allowed_dist):
        return CoordinateStatus.OK if distance <= max_allowed_dist else CoordinateStatus.ANOMALY


class TelemetryValidationService(RPCServer):

    def __init__(self, rabbitmq_config:dict=None, mongodb_config:dict=None):
        self.logger = logging.getLogger("TelemetryValidationService")

        default_config = load_config("config/startup.conf")
        if rabbitmq_config is None:
            self.logger.debug("RabbitMQ config value is empty, reverting to default configs.")
            rabbitmq_config = default_config['rabbitmq']

        if mongodb_config is None:
            self.logger.debug("MongoDB config value is empty, reverting to default configs.")
            mongodb_config = default_config["mongodb"]

        self.mongodb_client = MongoDB(**mongodb_config)
        super().__init__(**rabbitmq_config)


    def complete_setup(self):
        # Subscribe to any message coming from the STM GPS Routes Update.
        self.setup(routing_key=ROUTING_KEY_STM_TELEMETRY_VALIDATION, queue_name=ROUTING_KEY_STM_TELEMETRY_VALIDATION, on_message_callback=self.validate_telemetry)
        self.declare_local_queue(routing_key=ROUTING_KEY_STM_NOTIFICATION)
        self.logger.info("TelemetryValidationService setup complete.")


    @staticmethod
    def _deg_to_rad(x):
        return x * math.pi / 180


    def _calculate_distance(self, from_coordinates:tuple, to_coordinates:tuple):
        from_lat, from_lng = from_coordinates[0], from_coordinates[1]
        to_lat, to_lng = to_coordinates[0], to_coordinates[1]
        half_d_lat = self._deg_to_rad((to_lat - from_lat) / 2)
        half_d_lon = self._deg_to_rad((to_lng - from_lng) / 2)
        a = (math.sin(half_d_lat) ** 2 + math.cos(self._deg_to_rad(from_lat)) * math.cos(self._deg_to_rad(to_lat)) * math.sin(half_d_lon) ** 2)
        return EARTH_RADIUS * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


    def _routes_sort(self, route):
        try:
            return int(route['stop_sequence'])
        except KeyError as e:
            self.logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def _determine_coordinates_status(self, result, data) -> tuple[CoordinateStatus,str]:
        routes = result['routes'] if 'routes' in result else []
        max_allowed_distance = result['maximum_distance'] if 'maximum_distance' in result else MAX_ALLOW_DISTANCE
        bus_stop = {'stop_name': ''}

        if not routes: # If no bus stops found return NOT_FOUND
            return CoordinateStatus.NOT_FOUND, bus_stop['stop_name']

        routes.sort(key=self._routes_sort, reverse=False)
        stop_sequence = int(data['vehicle.current_stop_sequence']) - 1
        bus_stop = routes[stop_sequence]
        form_coordinates = (bus_stop['latitude'], bus_stop['longitude'])
        to_coordinates = (data['vehicle.position.latitude'], data['vehicle.position.longitude'])
        distance = self._calculate_distance(form_coordinates, to_coordinates)
        status = CoordinateStatus.parse_from_distance(distance, max_allowed_distance)

        if CoordinateStatus.ANOMALY == status:
            self.logger.debug(f"Distance: {distance}, Status: {status}, Bus Stop: {bus_stop}, Vehicle: {data}")

        if  max_allowed_distance <= distance <= 1.01: # check against the next bus stop
            bus_stop = routes[stop_sequence + 1]
            form_coordinates = (bus_stop['latitude'], bus_stop['longitude'])
            distance = self._calculate_distance(form_coordinates, to_coordinates)
            status = CoordinateStatus.parse_from_distance(distance, max_allowed_distance)
            self.logger.debug(f"Distance: {distance}, Status: {status}, Bus Stop: {bus_stop}, Vehicle: {data}")

        elif distance >= 1.01: # reverse the order of bus stops
            routes.sort(key=self._routes_sort, reverse=True)
            bus_stop = routes[stop_sequence]
            form_coordinates = (bus_stop['latitude'], bus_stop['longitude'])
            distance = self._calculate_distance(form_coordinates, to_coordinates)
            status = CoordinateStatus.parse_from_distance(distance, max_allowed_distance)

            self.logger.debug(f"Distance: {distance}, Status: {status}, Bus Stop: {bus_stop}, Vehicle: {data}")

        return status, bus_stop['stop_name']


    def validate_telemetry(self, channel, method, properties, json_payload:str):
        self.logger.info(f"Received JSON payload: {json_payload}")

        payload_dict = json.loads(json_payload)

        if 'data' not in payload_dict:
            self.logger.error("Service received empty payload to be processed")
            return

        anomaly_data = []
        for i, data in enumerate(payload_dict["data"]):

            try:
                assert 'vehicle.trip.route_id' in payload_dict["data"][i], "Data dictionary must contain 'vehicle.trip.route_id' field."
                assert 'vehicle.position.latitude' in payload_dict["data"][i], "Data dictionary must contain 'vehicle.position.latitude' field."
                assert 'vehicle.position.longitude' in payload_dict["data"][i], "Data dictionary must contain 'vehicle.position.longitude' field."
                assert 'vehicle.current_stop_sequence' in payload_dict["data"][i], "Data dictionary must contain 'vehicle.current_stop_sequence' field."

                route_id =  int(data['vehicle.trip.route_id'])
                results = self.mongodb_client.database["bus_stops"].find({"route_id": route_id})
                results = list(results)
                bus_stop = ""

                if results and len(results) > 0 and 'routes' in results[0]:
                    self.logger.debug(f"Database returned: {results[0]}")
                    coordinates_status, bus_stop = self._determine_coordinates_status(results[0], payload_dict["data"][i])

                else:
                    self.logger.error(f"No data found in the database. Cannot validate coordinates for route : {route_id}")
                    coordinates_status = CoordinateStatus.NOT_FOUND

                payload_dict["data"][i]["vehicle.position.coordinates.status"] = coordinates_status.value
                payload_dict["data"][i]["vehicle.current_bus_stop"] = bus_stop
                if coordinates_status == CoordinateStatus.ANOMALY:
                    anomaly_data.append(payload_dict["data"][i])

            except AssertionError as e:
                self.logger.error(f"{str(e)} for : {payload_dict['data'][i]}")

        # Store to MongoDB
        self.mongodb_client.save(payload_dict["data"])

        # Publish anomaly messages
        if anomaly_data:
            anomaly_message = {"time": time.time_ns(), "source": "telemetry_validation_service", "data": anomaly_data}
            self.logger.debug(f"Message: {anomaly_message}")
            self.logger.debug(f"Published to queue: {ROUTING_KEY_STM_NOTIFICATION}")
            # self.send_message(routing_key=ROUTING_KEY_STM_NOTIFICATION, message=anomaly_message)


if __name__ == '__main__':
    service = TelemetryValidationService()
    service.complete_setup()

    while True:
        try:
            service.start_serving()
        except KeyboardInterrupt:
            exit(0)

        except Exception as e:
            print(f"The following exception occurred: {e}")
            traceback.print_tb(e.__traceback__)
            exit(0)
