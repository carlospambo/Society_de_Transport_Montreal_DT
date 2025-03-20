import json
import os

STM_API_URL = "https://api.stm.info/pub/od/gtfs-rt/ic/v2/vehiclePositions"
STM_API_HEADER = {'apiKey': os.environ["STM_API_KEY"], 'Accept': 'application/x-protobuf'}
ENCODING = "ascii"
ROUTING_KEY_BUS_ROUTE_UPDATES = "bus.routes.updates"
ROUTING_KEY_GPS_COORDINATES_ANOMALY_SERVICE = "gps.coordinates.anomaly.service"


def convert_str_to_bool(body):
    if body is None:
        return None
    else:
        return body.decode(ENCODING) == "True"


def encode_json(object_):
    return json.dumps(object_).encode(ENCODING)


def decode_json(bytes_):
    return json.loads(bytes_.decode(ENCODING))


def from_ns_to_s(time_ns):
    return time_ns / 1e9


def from_s_to_ns(time_s):
    return int(time_s * 1e9)


def from_s_to_ns_array(time_s):
    ns_floats = time_s * 1e9
    ns_ints = ns_floats.astype(int)
    return ns_ints