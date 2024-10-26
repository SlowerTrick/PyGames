extends HBoxContainer

@onready var game_manager: Node = get_node("/root/Game/GameManager")
@onready var heart_gui: Panel = $HeartGUI
@onready var heal_meter: Panel = $HealMeter
@onready var heart_animation: Timer = $HeartAnimation
var max_health
var string_bar
var health_panels = []

func _ready():
	heart_gui.hide()  # Esconde o nó original para que não seja visível
	max_health = game_manager.player_health
	string_bar = game_manager.string_bar
	create_health_bar(max_health)

func create_health_bar(health_amount):
	for heart in range(health_amount):
		var health_panel = heart_gui.duplicate()
		health_panel.show()  # Mostra o painel duplicado
		health_panels.append(health_panel)
		add_child(health_panel)
	update_health(max_health)

func update_health(actual_health):
	for heart in range(max_health):
		var sprite = health_panels[heart].get_node("AnimatedSprite2D")
		if heart < actual_health:
			sprite.animation = 'heart'  # Coração cheio
		else:
			sprite.animation = 'heartless'  # Coração vazio

func _on_heart_animation_timeout() -> void:
	#var test = heal_meter.get_node("AnimatedSprite2D")
	#print(test)
	#if string_bar == 6:
		#test.play('Heal')
	 
	for heart in range(max_health):
		var sprite = health_panels[heart].get_node("AnimatedSprite2D")
		if sprite.animation == 'heart':
			sprite.play('heart')

func create_string_bar(string_amount):
	pass

func update_string_bar(string_amount):
	pass
