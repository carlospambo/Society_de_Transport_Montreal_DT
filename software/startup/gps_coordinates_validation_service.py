import json
import logging
import math
import time
from communication.protocol import EARTH_RADIUS, MAX_ALLOW_DISTANCE
from communication.mongodb import MongoDB
from config.config import load_config, config_logger

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

                    bus_stop = results[0]['routes'][payload["data"][i]['vehicle.current_stop_sequence'] - 1]
                    form_coordinates = (bus_stop['latitude'], bus_stop['longitude'])
                    to_coordinates = (payload["data"][i]['vehicle.position.latitude'], payload["data"][i]['vehicle.position.longitude'])
                    distance = self.calculate_distance(form_coordinates, to_coordinates)
                    payload["data"][i]["vehicle.position.coordinates.status"] = "OK" if distance <= MAX_ALLOW_DISTANCE else "ANOMALY"

                else:
                    payload["data"][i]["vehicle.position.coordinates.status"] = "NOT_FOUND"
                    self.logger.error(f"No data found in the database. Cannot validate coordinates for route : {route_id}")

            except AssertionError as e:
                self.logger.error(f"{str(e)} for : {payload['data'][i]}")


        response["time"] = time.time_ns()
        response["data"] = payload["data"]

        self.logger.debug(f"Returning: {response}")

        return response