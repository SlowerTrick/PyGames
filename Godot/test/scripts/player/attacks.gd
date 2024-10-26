extends Area2D

@onready var sprite: AnimatedSprite2D = $"../AnimatedSprite2D"
@onready var neutral_attack_timer: Timer = $"../Timers/Attack Timers/Neutral"
@onready var neutral_collision: CollisionPositionLR = $Neutral
@onready var air_collision: CollisionPositionUD = $Air
@onready var player: CharacterBody2D = $".."
@export var damage := 1
var attack = 'none'
var knockback_direction = 'none'
@onready var pogo: Timer = $"../Timers/Attack Timers/Pogo"

func _ready():
	monitoring = false
	
func _process(delta):
	get_input()
	state_check()

func _on_body_entered(body: Node2D) -> void:
	var horizontal_distance = neutral_collision.global_position.distance_to(body.global_position)
	var vertical_distance = air_collision.global_position.distance_to(body.global_position)
	var attack_type = 'none'

	if horizontal_distance < vertical_distance && attack != 'up' && attack != 'down':
		attack_type = 'neutral'
	elif vertical_distance < horizontal_distance && attack != 'neutral':
		attack_type = attack
	
	if attack_type == attack:
		for child in body.get_children():
			if child is Damageable:
				child.hit(damage, player.facing_direction)
				# Adicionar knockback vertical
				if attack_type == 'neutral':
					if player.facing_direction > 0:
						player.knockback_direction = 'left'
					else:
						player.knockback_direction = 'right'
				else:
					if attack_type == 'down':
						player.knockback_direction = 'up'
					else:
						player.knockback_direction = 'down'
				Global.frame_freeze(0.6, 0.2)

func get_input():
	if Input.is_action_just_pressed("neutral_attack") and not neutral_attack_timer.time_left:
		if player.facing_vertical == 'up':
			neutral_attack_timer.start()
			attack = 'up'
		elif player.facing_vertical == 'down':
			neutral_attack_timer.start()
			attack = 'down'
		else:
			neutral_attack_timer.start()
			monitoring = true
			attack = 'neutral'
	else:
		if not neutral_attack_timer.time_left:
			attack = 'none'

func state_check():
	# During attack
	if neutral_attack_timer.time_left and attack != 'none':
		monitoring = true
	else: 
		monitoring = false
	
	# Facing direction
	if player.facing_direction == 1 and attack == 'none':
		neutral_collision.position = neutral_collision.right
	elif player.facing_direction == -1 and attack == 'none':
		neutral_collision.position = neutral_collision.left
	
	# Facing vertical
	if player.facing_vertical == 'up' and attack == 'none':  
		air_collision.position = air_collision.up
	elif player.facing_vertical == 'down' and attack == 'none':
		air_collision.position = air_collision.down
