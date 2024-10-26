extends Node

class_name Damageable

@onready var character: CharacterBody2D = $".."
@export var health := 3
@export var knockback_velocity : Vector2 = Vector2(200, 0)

func hit(damage : int, direction: int):
	health -= damage
	character.state = 'hit'
	knockback(direction)
	
	if health <= 0:
		get_parent().queue_free() 
		
func knockback(direction: int):
	if direction > 0:
		character.state = 'hit_right'
	elif direction < 0:
		character.state = 'hit_left'
	character.velocity.x = knockback_velocity.x * direction
