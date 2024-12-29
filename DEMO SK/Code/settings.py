import pygame, sys, os
from pygame.math import Vector2 as vector

os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init() # Inicialização do pygame
info = pygame.display.Info()
WINDOW_WIDTH,WINDOW_HEIGHT = info.current_w,info.current_h
TILE_SIZE = 64
ANIMATION_SPEED = 6
BASE_HEALTH = 5
STRING_MAX = 6

Z_LAYERS = {
	'bg': 0,
	'clouds': 1,
	'bg tiles': 2,
	'path': 3,
	'bg details': 4,
	'main': 5,
	'water': 6,
	'fg': 7
}
