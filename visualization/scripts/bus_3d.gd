extends Node3D

class_name  Bus3D

@export var ray_length : float = 20000.0  # Length of the ray
@export var outline_color : Color

@onready var ghost = $ghost
@onready var ghost_mesh = $ghost/ghost_mesh
@onready var bus = $bus
@onready var bus_mesh = $bus/bus_mesh
var target_position : Vector3 = position
var estimated_position : Vector3 = position
var last_position : Vector3 = position
var last_message_time: float
var selected = false
var original_outline_color : Color

@export var FOLLOW_SPEED = 4.0
var t = 0.0

func _ready() -> void:
	original_outline_color = bus_mesh.get_surface_override_material(0).next_pass.get_shader_parameter("outline_color")

func _physics_process(delta):
	t += delta * 0.07
	t = min(t,1)
	ghost.global_position = bus.global_position.lerp(estimated_position, t)

	# Lerps the bus to the new position when a new target position is set
	position = position.lerp(target_position, delta * FOLLOW_SPEED)

func on_update(_target_pos: Vector3, _time: float):
	# If a new position was determined to move to
	if _target_pos.x != target_position.x and _target_pos.z != target_position.z:
		_target_pos.y = ground_y(_target_pos + Vector3(0, 100, 0))
		target_position.y = ground_y(_target_pos + Vector3(0, 100, 0))
		last_position.y = target_position.y
		
		last_position = target_position
		target_position = _target_pos
		t = 0
		estimated_position = _target_pos + (_target_pos - last_position)
		look_at(estimated_position, Vector3.UP)
		rotation.x = 0
	last_message_time = _time

## Get the ground position downwards from the origin
func ground_y(origin: Vector3):
	var space_state = get_world_3d().direct_space_state
	var end_point = origin - Vector3(0, ray_length, 0)  # Cast downwards
	
	var query = PhysicsRayQueryParameters3D.create(origin, end_point)
	query.set_exclude([$bus/StaticBody3D])
	var result = space_state.intersect_ray(query)
	
	if result:
		return result.position.y
	else:
		return 20.0

func _on_selected():
	selected = true
	var mat = bus_mesh.get_surface_override_material(0).next_pass
	print("Object Selected: ", name)
	# Change material or highlight the object
	if mat:
		mat.set_shader_parameter("outline_color", outline_color)

func _on_unselected():
	var mat = bus_mesh.get_surface_override_material(0).next_pass
	if mat:
		mat.set_shader_parameter("outline_color", original_outline_color)
