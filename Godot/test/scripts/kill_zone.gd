extends Area2D

@onready var timer: Timer = $Timer
@onready var game_manager: Node = get_node("/root/Game/GameManager")

func _on_body_entered(body):
	body.inivicibility_frames.start()
	game_manager.player_take_damage()
	if game_manager.player_health <= 0:
		Engine.time_scale = 0.5
		timer.start()
		body.get_node("CollisionShape2D").queue_free()
	else:
		Global.frame_freeze(0.1, 0.4)
	
func _on_timer_timeout():
	Engine.time_scale = 1
	get_tree().reload_current_scene()
