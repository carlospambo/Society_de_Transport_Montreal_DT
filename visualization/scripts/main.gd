extends Node3D

@onready var rmq_connection = $rmq_listener
@onready var map_interpolation = $MapInterpolation

var root
var key_point_scene = preload("res://key_point.tscn")
var bus_scene = preload("res://bus.tscn")
var bus_3D_scene = preload("res://bus_3D.tscn")
var bus_stop = preload("res://bus_stop.tscn")

var routes_subscribed = [41, 140, 45, 24, 121]

func _ready() -> void:
	root = get_tree().get_root()
	rmq_connection.connect("OnMessage", _on_message)
	routes_updated()
	await get_tree().create_timer(1.0).timeout
	spawn_bus_stops()

func spawn_bus_stops():
	var bus_stops_json = load_json_file("res://assets/bus_stops.json")
	for route in bus_stops_json:
		if int(route['route_id']) in routes_subscribed:
			for stop_data in route['routes']:
				var bus_stop_instance: Node3D = bus_stop.instantiate()
				bus_stop_instance.name = stop_data.get('stop_name', "default_name")
				
				var stop_latitude: float = stop_data.get('latitude', 0)
				var stop_longitude: float = stop_data.get('longitude', 0)
				var real_stop_pos: Vector2 = map_interpolation.get_position_by_closest_triangulation(stop_latitude, stop_longitude)
				bus_stop_instance.position = Vector3(real_stop_pos[0], 0, real_stop_pos[1])
				
				$BusStops.add_child(bus_stop_instance)
				
	for route_id: int in routes_subscribed:
		pass

func toggle_bus_stops(toggled_on):
	if toggled_on:
		$BusStops.show()
	else:
		$BusStops.hide()

func toggle_reference_points(toggled_on):
	if toggled_on:
		$MapInterpolation/ReferencePoints.show()
	else:
		$MapInterpolation/ReferencePoints.hide()

func _on_message(message):
	var data = JSON.parse_string(message)
	var bus_data = data.data
	print(bus_data)
	for entity: Dictionary in bus_data:
		if int(entity['vehicle.trip.route_id']) in routes_subscribed:
			var entity_id = str(entity['vehicle.vehicle.id'])
			var bus_3d: Node3D
			if root.has_node(entity_id):
				bus_3d = root.get_node(entity_id)
			else:
				bus_3d = bus_3D_scene.instantiate()
				bus_3d.name = entity_id
				root.add_child(bus_3d)
			var latitude: float = entity.get('vehicle.position.latitude', 0)
			var longitude: float = entity.get('vehicle.position.longitude', 0)
			var bearing: float = entity.get('vehicle.position.bearing', 0)
			var speed: float = entity.get('vehicle.position.speed', 0)
			bearing -= 20 # Manual corrective delta, I don't know why I need it
			print("Latitude: " + str(latitude))
			print("Longitude: " + str(longitude))
			print("Bearing: " + str(bearing))
			print("Speed: " + str(speed))
			set_transform_from_geodata(bus_3d, latitude, longitude, bearing)

func set_transform_from_geodata(object: Bus3D, lat: float, long: float, bearing: float):
	# Get the real x and z positions from coordinates
	var real_pos = map_interpolation.get_position_by_closest_triangulation(lat, long)
	# Tell the bus object that a new message was received and send it data
	object.on_update(Vector3(real_pos[0], 15, real_pos[1]), Time.get_ticks_msec())

func load_json_file(file_path: String):
	var file := FileAccess.open(file_path, FileAccess.READ)
	if file:
		print("Found file")
		var content := file.get_as_text()
		file.close()
		
		var json := JSON.new()
		var parse_result := json.parse(content)
		
		if parse_result == 0:
			var data = json.get_data()
			return data
		else:
			push_error("Failed to parse JSON file")
	else:
		push_error("Failed to open file: " + file_path)
	
	print("Found no data")
	return {}

func parse_comma_string(input_string: String) -> Array:
	# Remove any whitespace
	var clean_string = input_string.strip_edges().replace(" ", "")
	
	# If the string is empty, return an empty array
	if clean_string == "":
		return []
	
	var result = []
	var values = clean_string.split(",")
	
	# Try to convert each value to an integer
	for value: String in values:
		if value.is_valid_int():
			result.append(int(value))
		else:
			print("Warning: Skipping invalid integer value: ", value)
	
	return result
	
func add_to_subscribed_routes():
	var input_string: String = %AddRoutesText.text
	%AddRoutesText.clear()
	var parsed_values = parse_comma_string(input_string)
	for value in parsed_values:
		if not routes_subscribed.has(value):
			routes_subscribed.append(value)
	routes_updated()

func remove_from_subscribed_routes():
	var input_string: String = %RemoveRoutesText.text
	%RemoveRoutesText.clear()
	var parsed_values = parse_comma_string(input_string)
	for value in parsed_values:
		if routes_subscribed.has(value):
			routes_subscribed.erase(value)
	routes_updated()

func routes_updated():
	%RoutesSubscribed.text = "Currently subscribed routes: " + str(routes_subscribed)
	for child in $BusStops.get_children():
		child.queue_free()
	spawn_bus_stops()
