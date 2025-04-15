extends Node

func create_circle(radius : float, pts : int) -> PackedVector2Array:
	
	var arr := PackedVector2Array()
	var angle_change = deg_to_rad(360.0/pts)

	var angle = 0
	for i in range(1, pts + 1):
		
		var x = sin(angle)
		var y = cos(angle)
		
		arr.append(Vector2(x * radius, y * radius))
		
		angle += angle_change
	
	return arr
	
func calc_offset(pos_a: Vector2, pos_b: Vector2, scale: Vector2) -> Vector2:
	var off = (pos_b - pos_a) * scale * Vector2(-1, 1)
	#print_debug("Pos: " + str(pos_a) + " = Offset: " + str(off))
	return off


func calc_scale_at_lat(lat : float) -> Vector2:

	print("Calculating scale for latitude: " + str(lat))
	var rad_lat = deg_to_rad(lat)

	var lat_term_a = 111132.92
	var lat_term_b = 559.82 * cos(2 * rad_lat)
	var lat_term_c = 1.175 * cos(4 * rad_lat)
	var lat_term_d = 0.0023 * cos(6 * rad_lat)
#	print(lat_term_a + " " + lat_term_b + " " + lat_term_c + " " + lat_term_d)
	var lat_scale = lat_term_a - lat_term_b + lat_term_c - lat_term_d

	var lon_term_a = 111412.84 * cos(rad_lat)
	var lon_term_b = 93.5 * cos(3 * rad_lat)
	var lon_term_c = 0.118 * cos(5 * rad_lat)
#	print(lon_term_a + " " + lon_term_b + " " + lon_term_c)
	var lon_scale = lon_term_a - lon_term_b + lon_term_c

	print("Lat m per degree: " + str(lat_scale) + " Lon m per degree: " + str(lon_scale))
	return Vector2(lon_scale, lat_scale)
