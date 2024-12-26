from settings import *
from sprites import Sprite
from random import choice, randint, uniform
from timecount import Timer
from pygame import gfxdraw, BLEND_RGB_ADD
from math import sqrt

class AllSprites(pygame.sprite.Group):
    def __init__(self, width, height, bg_color, top_limit = 0):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = vector()
        self.width, self.height = width * TILE_SIZE, height * TILE_SIZE
        self.borders = {
            'left': 0,
            'right': -self.width + WINDOW_WIDTH,
            'bottom': -self.height + WINDOW_HEIGHT,
            'top': top_limit,
        }
        self.bg_color = bg_color
        
        # Controle do tremor da câmera
        self.shake_magnitude = 5  # Intensidade do tremor
        self.shake_timer = Timer(0)   # Duração do tremor

    def camera_constraint(self):
        # Limitação da camera do jogador
        self.offset.x = self.offset.x if self.offset.x < self.borders['left'] else self.borders['left']
        self.offset.x = self.offset.x if self.offset.x > self.borders['right'] else self.borders['right']
        self.offset.y = self.offset.y if self.offset.y > self.borders['bottom'] else self.borders['bottom']
        self.offset.y = self.offset.y if self.offset.y < self.borders['top'] else self.borders['top']
    
    def start_shaking(self, duration, intensity=5):
        # Inicia o tremor da câmera por uma certa duração e intensidade.
        self.shake_magnitude = intensity
        self.shake_timer = Timer(duration, self.stop_shaking, repeat=False)
        self.shake_timer.activate()

    def stop_shaking(self):
        self.shake_timer.deactivate()
        
    def apply_shake(self):
        # Aplica o tremor da câmera se o temporizador estiver ativo.
        self.shake_timer.update()
        if self.shake_timer.active:
            self.offset.x += uniform(-self.shake_magnitude, self.shake_magnitude)
            self.offset.y += uniform(-self.shake_magnitude, self.shake_magnitude)
            
    def draw_sky(self):
        self.display_surface.fill(self.bg_color)
        # self.display_surface.fill('#181818')

    def draw(self, target_pos, delta_time):
        # Movimentação da camera do jogador
        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2) # "-" pois o movimento é oposto ao crescimento da tela
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2) # "-" pois o movimento é oposto ao crescimento da tela
        
        # Aplica o tremor da câmera e limita a tela de acordo com o jogador
        self.camera_constraint()
        self.apply_shake()

        # Desenho do céu
        self.draw_sky()

        for sprite in sorted(self, key = lambda sprite: sprite.z):
            # Desenha os elementos com base na ordem em Z_LAYER
            offset_pos = sprite.rect.topleft + self.offset
            self.display_surface.blit(sprite.image, offset_pos)