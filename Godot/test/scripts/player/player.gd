extends CharacterBody2D

# Exports

@export_group('move')
@export var speed := 150 # @export var speed: int = 200
@export var acceleration := 700
@export var friction := 900
@export var dash_distance := 650
@export_range(0.1,2) var dash_cooldown := 0.5

# Movement
var facing_direction := 1
var facing_vertical := 'none'
var direction := Vector2.ZERO
var can_move := true
var dash := false
var dash_is_available := true
var is_dashing := false
var looking_down := false
var looking_up := false
@onready var ray_cast_right: RayCast2D = $"RayCastRight"
@onready var ray_cast_left: RayCast2D = $"RayCastLeft"

# Knockback
@export var knockback_velocity : Vector2 = Vector2(300, 0)
var knockback_direction := 'none'
var knockback_tween: Tween = null
@onready var pogo: Timer = $"Timers/Attack Timers/Pogo"

#  Jump
@export_group('jump')
@export var jump_strenght := 300
@export var terminal_velocity := 500
var jump := false
var faster_fall := false
var gravity_multiplier := 1

# Attacks
@onready var nail: Area2D = $Nail

# Animations
@onready var sprite = $AnimatedSprite2D
@onready var inivicibility_frames: Timer = $Timers/HitTimer
var state := 'idle'

# Functions
func _ready():
	$Timers/DashCooldown.wait_time = dash_cooldown

func _process(delta):
	apply_gravity(delta)
	check_if_can_move()
	
	if can_move:
		get_input()
		apply_movement(delta)
		
	update_animation()

func get_input():
	# Horizontal Movement
	direction.x = Input.get_axis("left", "right")
	
	# Vertical Movement
	if Input.is_action_just_pressed("jump"):
		if is_on_floor() or is_on_wall_only() or $Timers/Coyote.time_left:
			if not is_dashing:
				jump = true
		
		if velocity.y > 0 and not is_on_floor():
			$Timers/JumpBuffer.start()
	
	if Input.is_action_just_released("jump") and not is_on_floor() and velocity.y < 0:
		faster_fall = true
	
	# Dash
	if Input.is_action_just_pressed("dash") and not $Timers/DashCooldown.time_left:
		dash = true
		$Timers/DashCooldown.start()
	
	# Facing Vertical
	if Input.is_action_pressed('down'):
		looking_down = true
		looking_up = false
		facing_vertical = 'down'
	elif Input.is_action_pressed('up'):
		looking_up = true
		looking_down = false
		facing_vertical = 'up'
	else:
		looking_up = false
		looking_down = false
		facing_vertical = 'none'

func apply_movement(delta):
	# Left/Right Movement
	if direction.x:
		velocity.x = direction.x * speed
		if direction.x > 0:
			facing_direction = 1
		elif direction.x < 0:
			facing_direction = -1	
	else:
		velocity.x = 0
	
	if is_on_wall_only():
		if ray_cast_right.is_colliding():
			facing_direction = -1
		elif ray_cast_left.is_colliding():
			facing_direction = 1
	
	# Jump
	if (jump or $Timers/JumpBuffer.time_left) and is_on_floor():
		velocity.y = -jump_strenght
		jump = false
		faster_fall = false	
		$Timers/Coyote.stop()
		$Timers/WallBlock.start()
	
	# Movement and Coyote
	var on_floor = is_on_floor()
	move_and_slide()
	if on_floor and not is_on_floor() and velocity.y >= 0:
		$Timers/Coyote.start()
		
func apply_gravity(delta):
	velocity.y += Global.gravity * delta
	
	if is_on_wall_only() and not $Timers/WallBlock.time_left:
		velocity.y = velocity.y / 1.1
	elif faster_fall and velocity.y < 0:
		velocity.y = velocity.y / 2
		
	velocity.y = velocity.y * gravity_multiplier
	velocity.y = min(velocity.y, terminal_velocity)

func check_if_can_move():
	# Verificações inciais
	if is_on_floor() or is_on_wall_only():
		dash_is_available = true
	
	# Dash
	if (dash and dash_is_available) or is_dashing:
		if (dash and dash_is_available):
			can_move = false
			dash = false
			dash_is_available = false
			is_dashing = true
			var dash_tween = create_tween()
			dash_tween.tween_property(self, 'velocity:x', facing_direction * dash_distance, 0.3)
			dash_tween.connect("finished", on_dash_finish)
			gravity_multiplier = 0	
		elif is_dashing:
			can_move = false
			move_and_slide()
			
	# Wall Jump
	elif (jump and is_on_wall_only()) or $Timers/WallJump.time_left:
		if $Timers/WallJump.time_left:
			can_move = false
			move_and_slide()
			
		elif jump and is_on_wall_only():
			can_move = false
			velocity.y = -jump_strenght * 1.2
			if facing_direction == 1:
				velocity.x = jump_strenght / 3.0
			else:
				velocity.x = -jump_strenght / 3.0
			jump = false
			faster_fall = false
			$Timers/Coyote.stop()
			$Timers/WallJump.start()
			
	# Knockback
	elif knockback_direction != 'none':
		if knockback_direction == 'right' or knockback_direction == 'left':
			if not knockback_tween:
				can_move = false
				knockback_tween = create_tween()
				# Adicionar if para alterar o tween para trabalhar em função de velocity:y
				knockback_tween.tween_property(self, 'velocity:x', facing_direction * knockback_velocity.x * -1, 0.2)
				knockback_tween.connect("finished", on_knockback_finish)
			else:
				move_and_slide()
	else:
		can_move = true
		
func on_dash_finish():
	velocity.x = move_toward(velocity.x, 0, 500)
	gravity_multiplier = 1
	is_dashing = false
	if is_on_wall_only():
		facing_direction = facing_direction * -1
		sprite.flip_h = false
	
func on_knockback_finish():
	velocity.x = move_toward(velocity.x, 0, 500)
	knockback_tween.stop()
	knockback_tween = null
	knockback_direction = 'none'

func update_animation():
	# Horizontal
	if facing_direction == 1 and nail.attack == 'none':
		sprite.flip_h = false
		state = 'run'
	elif facing_direction == -1 and nail.attack == 'none':
		sprite.flip_h = true
		state = 'run'
	if direction.x == 0:
		state = 'idle'
		
	# Vertical
	if velocity.y < 0:
		state = 'jump'
	elif velocity.y > 0:
		state = 'fall'
	
	# Wall
	if is_on_wall_only() and not $Timers/WallBlock.time_left:
		state = 'wall'
	
	# Dash
	if is_dashing:
		state = 'dash'
	
	# Attacks
	if $"Timers/Attack Timers/Neutral".time_left:
		if nail.attack == 'neutral':
			state = 'neutral_attack'
		elif nail.attack == 'up':
			state = 'up_attack'
		elif nail.attack == 'down':
			state = 'down_attack'
		
	# Hit
	if inivicibility_frames.time_left:
		state = 'hit'
		
	sprite.animation = state
