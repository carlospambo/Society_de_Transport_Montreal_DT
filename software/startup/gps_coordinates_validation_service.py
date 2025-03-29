import json
import logging
import math
import time
from enum import Enum
from communication.protocol import EARTH_RADIUS, MAX_ALLOW_DISTANCE
from communication.mongodb import MongoDB
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


class GpsCoordinatesValidationService:

    def __init__(self, mongodb_client: MongoDB):
        self.logger = logging.getLogger("GpsCoordinatesValidationService")
        self.mongodb_client = mongodb_client


    @staticmethod
    def deg_to_rad(x):
        return x * math.pi / 180


    def calculate_distance(self, from_coordinates:tuple, to_coordinates:tuple):
        from_lat, from_lng = from_coordinates[0], from_coordinates[1]
        to_lat, to_lng = to_coordinates[0], to_coordinates[1]

        half_d_lat = self.deg_to_rad((to_lat - from_lat) / 2)
        half_d_lon = self.deg_to_rad((to_lng - from_lng) / 2)

        a = (math.sin(half_d_lat) ** 2 + math.cos(self.deg_to_rad(from_lat)) * math.cos(self.deg_to_rad(to_lat)) * math.sin(half_d_lon) ** 2)

        return EARTH_RADIUS * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def routes_sort(self, route):
        try:
            return int(route['stop_sequence'])
        except KeyError as e:
            self.logger.error(f"Error at extracting timestamp: {str(e)}")
            return 0


    def determine_coordinates_status(self, result, data) -> CoordinateStatus:
        routes = result['routes'] if 'routes' in result else []
        max_allowed_distance = result['maximum_distance'] if 'maximum_distance' in result else MAX_ALLOW_DISTANCE

        if not routes: # If no bus stops found return NOT_FOUND
            return CoordinateStatus.NOT_FOUND

        routes.sort(key=self.routes_sort, reverse=False)
        stop_sequence = int(data['vehicle.current_stop_sequence']) - 1
        form_coordinates = (routes[stop_sequence]['latitude'], routes[stop_sequence]['longitude'])
        to_coordinates = (data['vehicle.position.latitude'], data['vehicle.position.longitude'])
        distance = self.calculate_distance(form_coordinates, to_coordinates)
        status = CoordinateStatus.parse_from_distance(distance, max_allowed_distance)

        if CoordinateStatus.ANOMALY == status:
            self.logger.debug(f"Distance: {distance}, Status: {status}, Bus Stop: {routes[stop_sequence + 1]}, Vehicle: {data}")

        if  max_allowed_distance <= distance <= 1.01: # check against the next bus stop
            form_coordinates = (routes[stop_sequence + 1]['latitude'], routes[stop_sequence + 1]['longitude'])
            distance = self.calculate_distance(form_coordinates, to_coordinates)
            status = CoordinateStatus.parse_from_distance(distance, max_allowed_distance)
            self.logger.debug(f"Distance: {distance}, Status: {status}, Bus Stop: {routes[stop_sequence + 1]}, Vehicle: {data}")

        elif distance >= 1.01: # reverse the order of bus stops
            routes.sort(key=self.routes_sort, reverse=True)
            form_coordinates = (routes[stop_sequence]['latitude'], routes[stop_sequence]['longitude'])
            distance = self.calculate_distance(form_coordinates, to_coordinates)
            status = CoordinateStatus.parse_from_distance(distance, max_allowed_distance)
            self.logger.debug(f"Distance: {distance}, Status: {status}, Bus Stop: {routes[stop_sequence + 1]}, Vehicle: {data}")

        return status


    def validate_gps_coordinates(self, payload:dict) -> dict:
        self.logger.debug(f"Received values: {json.dumps(payload)}")

        response = {"source": "gps_coordinates_validation_service"}

        if 'data' not in payload:
            self.logger.error("Payload dictionary must contain 'data' field")
            response["time"] = time.time_ns()
            response["error"] = "Payload dictionary must contain 'data' field"
            return response

        for i, data in enumerate(payload["data"]):

            try:
                assert 'vehicle.trip.route_id' in payload["data"][i], "Data dictionary must contain 'vehicle.trip.route_id' field."
                assert 'vehicle.position.latitude' in payload["data"][i], "Data dictionary must contain 'vehicle.position.latitude' field."
                assert 'vehicle.position.longitude' in payload["data"][i], "Data dictionary must contain 'vehicle.position.longitude' field."
                assert 'vehicle.current_stop_sequence' in payload["data"][i], "Data dictionary must contain 'vehicle.current_stop_sequence' field."

                route_id =  int(data['vehicle.trip.route_id'])
                results = self.mongodb_client.database["bus_stops"].find({"route_id": route_id})
                results = list(results)

                if results and len(results) > 0 and 'routes' in results[0]:
                    self.logger.debug(f"Database returned: {results[0]}")
                    coordinates_status = self.determine_coordinates_status(results[0], payload["data"][i])
                else:
                    self.logger.error(f"No data found in the database. Cannot validate coordinates for route : {route_id}")
                    coordinates_status = CoordinateStatus.NOT_FOUND

                payload["data"][i]["vehicle.position.coordinates.status"] = coordinates_status.value
            except AssertionError as e:
                self.logger.error(f"{str(e)} for : {payload['data'][i]}")

        response["time"] = time.time_ns()
        response["data"] = payload["data"]

        self.logger.debug(f"Returning: {response}")

        return response