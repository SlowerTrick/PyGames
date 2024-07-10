from typing import Any
from pygame.sprite import Group
from settings import *

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface = pygame.Surface((TILE_SIZE, TILE_SIZE)), groups = None):
        super().__init__(groups)
        self.image = surface
        self.image.fill('white')
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()

class MovingSprite(Sprite):
    def __init__(self, groups, start_pos, end_pos, move_dir, speed):
        surface = pygame.Surface((200, 50))
        super().__init__(start_pos, surface, groups)
        if move_dir == 'x':
            self.rect.midleft = start_pos
        else:
            self.rect.midtop = start_pos
        self.start_pos = start_pos
        self.end_pos = end_pos

        # Movimentação
        self.moving = True
        self.speed = speed
        self.direction = vector(1, 0) if move_dir == 'x' else vector(0, 1)
        self.move_dir = move_dir

    def check_border(self):
        if self.move_dir == 'x':
            if self.rect.right >= self.end_pos[0] and self.direction.x == 1: # 0 pois é onde x está posicionado
                self.direction.x = -1
                self.rect.right = self.end_pos[0]

            if self.rect.left <= self.start_pos[0] and self.direction.x == -1:
                self.direction.x = 1
                self.rect.left = self.start_pos[0]
        else:
            if self.rect.bottom >= self.end_pos[1] and self.direction.y == 1: # 1 pois é onde y está posicionado
                self.direction.y = -1
                self.rect.bottom = self.end_pos[1]

            if self.rect.top <= self.start_pos[1] and self.direction.y == -1:
                self.direction.y = 1
                self.rect.top = self.start_pos[1]
    
    def update(self, delta_time):
        self.old_rect = self.rect.copy()
        self.rect.topleft += self.direction * self.speed * delta_time
        self.check_border()