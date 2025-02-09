
from google.transit import gtfs_realtime_pb2
import requests, json, protobuf_to_dict

valid_route_ids  = []
url = ""
headers = { }

def extract_timestamp(data):
    try:
        return int(data['vehicle']['timestamp'])

    except KeyError as e:
        print(f"Exception: {str(e)}")
        return 0

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get(url, headers=headers)
feed.ParseFromString(response.content)

vehicles_json = []
feed_dict = protobuf_to_dict.protobuf_to_dict(feed) # convert to dictionary from the original protobuf feed

for entity in feed_dict['entity']:
    if 'vehicle' in entity and 'trip' in entity['vehicle'] and 'route_id' in entity['vehicle']['trip']:
        route_id = int(entity['vehicle']['trip']['vehicle'])
        if route_id in valid_route_ids:
            vehicles_json.append(entity)

vehicles_json.sort(key=extract_timestamp, reverse=True)

print(json.dumps(vehicles_json))

