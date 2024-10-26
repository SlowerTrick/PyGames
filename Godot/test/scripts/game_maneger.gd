extends Node

@export_range(1, 99) var player_health = 5
@export_range(1, 99) var string_bar = 6
var score = 0
@onready var score_label: Label = $Score_label
@onready var hearts_container: HBoxContainer = $"../CanvasLayer/HeartsContainer"

func add_point():
	score += 1
	score_label.text = "You collected " + str(score) + " coin(s)"

func player_take_damage():
	player_health -= 1
	hearts_container.update_health(player_health)

func update_string_bar():
	pass
