extends CharacterBody2D

const speed = 60
var direction = 1
var state = 'idle'

@onready var ray_cast_right: RayCast2D = $RayCastRight
@onready var ray_cast_left: RayCast2D = $RayCastLeft
@onready var animated_sprite: AnimatedSprite2D = $AnimatedSprite2D

func _process(delta: float) -> void:
	apply_gravity(delta)
	
	if ray_cast_right.is_colliding():
		direction = -1
		animated_sprite.flip_h = true
	elif ray_cast_left.is_colliding():
		direction = 1
		animated_sprite.flip_h = false

	if state == 'hit_right':
		velocity.x = move_toward(velocity.x, 0, 200 * delta)
		if velocity.x <= 0 or is_on_wall():
			state = 'idle'
	elif state == 'hit_left':
		velocity.x = move_toward(velocity.x, 0, 200 * delta)
		if velocity.x >= 0 or is_on_wall():
			state = 'idle'
	else:
		velocity.x = direction * speed

	move_and_slide()
	
func apply_gravity(delta):
	velocity.y += Global.gravity * delta
