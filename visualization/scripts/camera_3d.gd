extends Camera3D

@export var move_speed: float = 5.0
@export var target_distance: float = 30.0
@export var min_distance: float = 10.0
@export var max_distance: float = 200.0
@export var zoom_speed: float = 10.0
@export var rotation_speed: float = 0.005
@export var fly_speed: float = 50.0  # Speed for free-fly movement
@export var fly_speed_min: float = 1.0  # Minimum fly speed
@export var fly_speed_max: float = 250.0  # Maximum fly speed
@export var fly_speed_change: float = 5.0  # How much speed changes per scroll

var selected_object: Node3D = null
var original_position: Vector3
var original_rotation: Quaternion
var tween: Tween
var yaw: float = 0.0
var pitch: float = 0.0
var rotating: bool = false
var free_flying: bool = false  # Flag to toggle free-fly mode

func _ready():
	original_position = global_transform.origin
	original_rotation = global_transform.basis.get_rotation_quaternion()

func _input(event):
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
			handle_object_selection()
		elif event.button_index == MOUSE_BUTTON_MIDDLE:
			rotating = event.pressed  # Start rotating with middle mouse button
		elif event.button_index == MOUSE_BUTTON_RIGHT and event.pressed:
			# Toggle free-fly mode with right mouse button
			free_flying = !free_flying
			if free_flying:
				Input.set_mouse_mode(Input.MOUSE_MODE_CAPTURED)
				# Cancel object selection when entering free-fly mode
				if selected_object and selected_object.has_method("_on_unselected"):
					selected_object._on_unselected()
				selected_object = null
			else:
				Input.set_mouse_mode(Input.MOUSE_MODE_VISIBLE)

	if free_flying:
		if Input.is_action_just_pressed("cam_zoom_in"):
			fly_speed = clamp(fly_speed + fly_speed_change, fly_speed_min, fly_speed_max)
		elif Input.is_action_just_pressed("cam_zoom_out"):
			fly_speed = clamp(fly_speed - fly_speed_change, fly_speed_min, fly_speed_max)
		print("Fly speed: ", fly_speed)  # Feedback for the user
	else:
		# Zooming with Mouse Scroll
		if Input.is_action_just_pressed("cam_zoom_in"):
			target_distance = max(min_distance, target_distance - zoom_speed)
		elif Input.is_action_just_pressed("cam_zoom_out"):
			target_distance = min(max_distance, target_distance + zoom_speed)
	
	# Rotate camera when middle mouse button is held and moved
	if event is InputEventMouseMotion:
		if rotating:
			# Use consistent rotation_speed without converting to radians here
			# since we're working with screen pixels
			yaw -= event.relative.x * rotation_speed  
			pitch -= event.relative.y * rotation_speed
			
			# Clamp pitch to prevent camera flipping
			pitch = clamp(pitch, -PI/2 + 0.1, PI/2 - 0.1)
		elif free_flying:
			# Free-fly rotation
			yaw -= event.relative.x * rotation_speed
			pitch -= event.relative.y * rotation_speed
			
			# Clamp pitch to prevent camera flipping
			pitch = clamp(pitch, -PI/2 + 0.1, PI/2 - 0.1)
			
			# Apply rotation directly in free-fly mode
			var q_yaw = Quaternion(Vector3.UP, yaw)
			var q_pitch = Quaternion(Vector3.RIGHT, pitch)
			var rotation_quat = q_yaw * q_pitch
			global_transform.basis = Basis(rotation_quat)

func _process(delta):
	if selected_object:
		var target_position = selected_object.global_transform.origin
		
		# Use quaternions for more stable rotations
		var q_yaw = Quaternion(Vector3.UP, yaw)
		var q_pitch = Quaternion(Vector3.RIGHT, pitch)
		
		# Combine rotations in the correct order
		var rotation_quat = q_yaw * q_pitch
		
		# Convert to basis
		var rotation_basis = Basis(rotation_quat)
		
		# Calculate the new camera position
		var offset = rotation_basis * Vector3(0, 0, target_distance)
		var new_position = target_position + offset
		
		# Smoothly move the camera
		global_transform.origin = global_transform.origin.lerp(new_position, move_speed * delta)
		
		# Make the camera look at the target using the same rotation
		global_transform.basis = rotation_basis.looking_at(target_position - new_position)
	elif free_flying:
		# Free-fly movement
		handle_free_fly_movement(delta)

func handle_free_fly_movement(delta):
	var input_dir = Vector3()
	
	# Get input direction
	if Input.is_action_pressed("cam_move_forward"):  # W key
		input_dir.z -= 1
	if Input.is_action_pressed("cam_move_backward"):  # S key
		input_dir.z += 1
	if Input.is_action_pressed("cam_move_left"):  # A key
		input_dir.x -= 1
	if Input.is_action_pressed("cam_move_right"):  # D key
		input_dir.x += 1
	if Input.is_action_pressed("cam_move_up"):  # Space
		input_dir.y += 1
	if Input.is_action_pressed("cam_move_down"):  # Shift or Ctrl
		input_dir.y -= 1
	
	# Normalize to prevent faster diagonal movement
	if input_dir.length_squared() > 0:
		input_dir = input_dir.normalized()
	
	# Transform input direction to camera's local space
	var movement = global_transform.basis * input_dir * fly_speed * delta
	
	# Apply movement
	global_transform.origin += movement

func handle_object_selection():
	var space_state = get_world_3d().direct_space_state
	var mouse_pos = get_viewport().get_mouse_position()
	var from = project_ray_origin(mouse_pos)
	var to = from + project_ray_normal(mouse_pos) * 10000  # Extend ray
	var query = PhysicsRayQueryParameters3D.create(from, to)
	var result = space_state.intersect_ray(query)
	
	if result and result.has("collider"):
		var clicked_object = result["collider"].get_parent().get_parent()
		if clicked_object and clicked_object.has_method("_on_selected"):
			clicked_object._on_selected()
			lock_camera_to(clicked_object)
			free_flying = false  # Exit free-fly mode when object is selected
		else:
			reset_camera()  # Clicked something else → reset
	else:
		reset_camera()  # Clicked empty space → reset

func lock_camera_to(target: Node3D):
	selected_object = target
	
	# Calculate initial yaw and pitch based on current camera position
	var direction = (global_transform.origin - target.global_transform.origin).normalized()
	
	# Calculate proper initial angles
	yaw = atan2(direction.x, direction.z)
	pitch = -asin(clamp(direction.y, -1.0, 1.0))  # Negative because camera pitch works opposite

func reset_camera():
	if selected_object and selected_object.has_method("_on_unselected"):
		selected_object._on_unselected()
	selected_object = null
	rotating = false
