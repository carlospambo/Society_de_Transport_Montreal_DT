from pymongo import MongoClient
import pandas as pd
import numpy as np
import os
import time

current_dir = os.getcwd()
assert os.path.basename(current_dir) == 'startup', 'Current directory is not startup'

MONGODB_CONNECTION_STR = "mongodb://log6953fe:log6953fe@localhost:27017"

routes = pd.read_csv('../../datasets/routes.txt', sep=',', dtype={"route_id": str})
trips = pd.read_csv('../../datasets/trips.txt', sep=',', dtype={"route_id": str, "trip_id": str})
stops = pd.read_csv('../../datasets/stops.txt', sep=',', dtype={"stop_id": str})
stop_times = pd.read_csv('../../datasets/stop_times.txt', sep=',',  dtype={"trip_id": str, "stop_id": str})

def to_dictionary(df):
    data = []
    for record in df.to_numpy():
        data.append({
            'stop_id': int(record[1]),
            'stop_sequence': int(record[2]),
            'stop_name': record[3],
            'latitude': float(record[4]),
            'longitude': float(record[5])
        })
    return data


def get_stops(bus_route):
    route_trips = trips[trips['route_id'] == bus_route]
    trip_ids = route_trips['trip_id'].unique()
    route_stop_times = stop_times[stop_times['trip_id'].isin(trip_ids)]
    route_stop_times = route_stop_times.merge(stops, on="stop_id", how="left")
    route_stop_times = route_stop_times.sort_values(by=["trip_id", "stop_sequence"])
    single_trip_id = route_stop_times["trip_id"].iloc[0]  # Pick the first trip
    route_stop_times = route_stop_times[route_stop_times["trip_id"] == single_trip_id]

    return {
        'route_id': int(bus_route),
        'routes': to_dictionary(route_stop_times[["trip_id", "stop_id", "stop_sequence", "stop_name", "stop_lat", "stop_lon"]])
    }


def load_bus_stops():
    start_time = time.time()
    mongo_client = MongoClient(MONGODB_CONNECTION_STR)
    database = mongo_client["log6953fe_db"]
    bus_stops_collection = database["bus_stops"]

    for i in np.unique(routes['route_id']):
        bus_stops_collection.insert_one(get_stops(i))

    print(f"Loading bus stops took {(time.time() - start_time): .4f} seconds")

if __name__ == '__main__':
    load_bus_stops()