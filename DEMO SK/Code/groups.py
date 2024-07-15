from typing import Iterable
from pygame.sprite import AbstractGroup
from settings import *

class AllSprites(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = vector()

    def draw(self, target_pos):
        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2) # "-" pois o movimento é oposto ao crescimento da tela
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2) # "-" pois o movimento é oposto ao crescimento da tela

        for sprite in sorted(self, key = lambda sprite: sprite.z):
            # Desenha os elementos com base na ordem em Z_LAYER
            offset_pos = sprite.rect.topleft + self.offset
            self.display_surface.blit(sprite.image, offset_pos)