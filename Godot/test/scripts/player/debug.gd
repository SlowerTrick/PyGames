extends Label

@onready var wall_jump: Timer = $"../Timers/WallJump"
@onready var player: CharacterBody2D = $".."
@onready var nail: Area2D = $"../Nail"
@onready var pogo: Timer = $"../Timers/Attack Timers/Pogo"

func _process(_delta):
	text = str(player.knockback_direction, '   ', int(player.velocity.y), '   ', pogo.time_left)
