extends Node

var key_point_scene = preload("res://key_point.tscn")

# Earth radius in meters (approximate)
const EARTH_RADIUS = 6367299.7229714
@onready var reference_points: Array[Node] = $ReferencePoints.get_children()

func latlong_to_2d(longitude: float, latitude: float, ref_longitude: float, ref_latitude: float) -> Vector2:
	var ref_longitude_rad = deg_to_rad(ref_longitude)
	var ref_latitude_rad = deg_to_rad(ref_latitude)
	var lon_rad = deg_to_rad(longitude)
	var lat_rad = deg_to_rad(latitude)
	
	# Calculate differences from the reference point
	var delta_lon = lon_rad - ref_longitude_rad
	var delta_lat = lat_rad - ref_latitude_rad
	
	# Convert lat/long differences to meters
	var x = EARTH_RADIUS * delta_lon * cos(ref_latitude_rad)
	var z = EARTH_RADIUS * delta_lat
	
	return Vector2(x, z)

# Calculate barycentric coordinates for interpolation
func interpolate_latlon_to_2d(lat: float, lon: float, reference_points) -> Vector2:
	if reference_points.size() != 3:
		push_error("Reference points not set.")
		return Vector2.ZERO
	
	var p1 = reference_points[0]
	var p2 = reference_points[1]
	var p3 = reference_points[2]
	
	# Calculate triangle area (cross product method)
	var denom = (p2.lat - p3.lat) * (p1.lon - p3.lon) + (p3.lon - p2.lon) * (p1.lat - p3.lat)
	
	if denom == 0:
		push_error("Reference points must not be collinear.")
		return Vector2.ZERO

	# Barycentric coordinates
	var w1 = ((p2.lat - p3.lat) * (lon - p3.lon) + (p3.lon - p2.lon) * (lat - p3.lat)) / denom
	var w2 = ((p3.lat - p1.lat) * (lon - p3.lon) + (p1.lon - p3.lon) * (lat - p3.lat)) / denom
	var w3 = 1.0 - w1 - w2
	
	# Interpolate x and z
	var x = w1 * p1.x + w2 * p2.x + w3 * p3.x
	var z = w1 * p1.z + w2 * p2.z + w3 * p3.z

	return Vector2(x, z)

func get_position_by_closest(latitude, longitude) -> Vector2:
	var reference_points : Array[Node] = $ReferencePoints.get_children()
	var closest_reference_point = null
	var min_distance = INF
	
	for point in reference_points:
		var distance = pow(point.latitude - latitude, 2) + pow(point.longitude - longitude, 2)
		if distance < min_distance:
			min_distance = distance
			closest_reference_point = point
	
	return latlong_to_2d(longitude, latitude, closest_reference_point.longitude, closest_reference_point.latitude)

func get_position_by_closest_triangulation(latitude, longitude) -> Vector2:
	var closest_points: Array = []
	
	# Find the three closest points
	for point in reference_points:
		var distance = pow(point.latitude - latitude, 2) + pow(point.longitude - longitude, 2)
		closest_points.append({"point": point, "distance": distance})
	
	closest_points.sort_custom(func(a, b): return a["distance"] < b["distance"])
	closest_points = closest_points.slice(0, 3)  # Keep only the three closest points
	
	var refs = []
	for i in range(3):
		var point: Node3D = closest_points[i]["point"]
		refs.append({'lat': point.latitude, 'lon': point.longitude, 'x': point.global_position.x, 'z': point.global_position.z})	
	
	return interpolate_latlon_to_2d(latitude, longitude, refs)
