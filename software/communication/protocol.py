import json
import os

STM_API_URL = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
STM_API_HEADER = {'apiKey': os.environ["STM_API_KEY"], 'Accept': 'application/x-protobuf'}
ENCODING = "ascii"
ROUTING_KEY_BUS_ROUTE_UPDATES = "bus.routes.updates"
ROUTING_KEY_GPS_COORDINATES_VALIDATION_SERVICE = "gps.coordinates.validation.service"
EARTH_RADIUS = 6371 # Radius of the Earth in Kilometers
MAX_ALLOW_DISTANCE = 0.5 # Maximum allowed distance in Kilometers
CTRL_EXEC_INTERVAL = 15.0

def encode_json(object_):
    return json.dumps(object_).encode(ENCODING)


def decode_json(bytes_):
    return json.loads(bytes_.decode(ENCODING))

