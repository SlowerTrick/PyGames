from typing import Any
from settings import * 
from math import sin, cos, radians
from random import randint

# Pegando atributos da classe sprite do pygame
class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surface = pygame.Surface((TILE_SIZE, TILE_SIZE)), groups = None, z = Z_LAYERS['main']):
        super().__init__(groups)
        self.image = surface
        # self.image.fill('white')
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()
        self.z = z

class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups, z = Z_LAYERS['main'], animation_speed = ANIMATION_SPEED):
        self.frames, self.frame_index = frames, 0
        super().__init__(pos, self.frames[self.frame_index], groups, z)
        self.animation_speed = animation_speed
    
    def animate(self, delta_time):
        # Roda as animações com base na quantidade de sprites e no delta time
        self.frame_index += self.animation_speed * delta_time
        self.image = self.frames[int(self.frame_index % len(self.frames))]
                                 
    def update(self, delta_time):
        self.animate(delta_time)

class Item(AnimatedSprite):
    def __init__(self, item_type, pos, frames, groups, data):
        super().__init__(pos, frames, groups)
        self.initial_pos = list(pos)
        self.pos = list(pos)
        self.direction = 1
        self.rect.center = pos
        self.item_type = item_type
        self.data = data
    
    def activate(self):
        if self.item_type == 'gold':
            self.data.coins += 5
        if self.item_type == 'silver':
            self.data.coins += 1
        if self.item_type == 'diamond':
            self.data.coins += 20
        if self.item_type == 'skull':
            self.data.coins += 50
        if self.item_type == 'potion':
            self.data.player_health += 1
        if self.item_type == 'wall_jump':
            self.data.unlocked_wall_jump = True
        if self.item_type == 'dash':
            self.data.unlocked_dash = True
        if self.item_type == 'throw_attack':
            self.data.unlocked_throw_attack = True
    
    def update(self, delta_time):
        if self.item_type in ('wall_jump', 'dash', 'throw_attack') :
            if self.pos[1] >= self.initial_pos[1] or self.pos[1] <= self.initial_pos[1] - 100:
                self.direction *= -1
            self.pos[1] += self.direction / 3

        self.rect.center = self.pos

        self.frame_index += self.animation_speed * delta_time
        self.image = self.frames[int(self.frame_index % len(self.frames))]

class Door(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, reverse, mode, player, enemies, door_sounds):
        super().__init__(groups)
        # Sprite
        self.frames = frames
        self.frame_index = len(self.frames) - 1
        self.image = self.frames[self.frame_index]
        self.image = pygame.transform.scale_by(self.image, (3, 4))
        self.reverse = reverse
        self.image = pygame.transform.flip(self.image, True, False) if self.reverse else self.image
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect

        # Setup geral
        self.z = Z_LAYERS['main']
        self.open_door = False
        self.close_door = False
        self.open_door_sound = False
        self.mode = mode
        self.player = player.hitbox_rect
        self.enemies = enemies
        self.sounds = door_sounds
    
    def opened_door_logic(self, dt):
        if self.open_door:
            self.frame_index -= ANIMATION_SPEED * dt * 5
            self.image = self.frames[int(self.frame_index % len(self.frames))]
            if self.frame_index <= 1:
                self.frame_index = 1
            self.image = pygame.transform.scale_by(self.image, (3, 4))
            self.image = pygame.transform.flip(self.image, True, False) if self.reverse else self.image

            # Colisão à esquerda
            if self.reverse:
                if self.player.left <= self.rect.right:
                    self.player.left = self.rect.right
            
            # Colisão à direita
            if not self.reverse:
                if self.player.right >= self.rect.left:
                    self.player.right = self.rect.left
    
    def closed_door_logic(self, dt):
        if self.close_door:
            self.frame_index += ANIMATION_SPEED * dt * 3
            self.image = self.frames[int(self.frame_index % len(self.frames))]
            if self.frame_index >= len(self.frames) - 1:
                self.sounds['close_door'].play()
                self.kill()
            self.image = pygame.transform.scale_by(self.image, (3, 4))
            self.image = pygame.transform.flip(self.image, True, False) if self.reverse else self.image
    
    def manage_enemies(self):
        if not self.enemies:
            self.close_door = True
            self.open_door = False

    def manage_state(self):
        if self.mode == 'cross' and not self.close_door:
            if self.reverse and self.player.x > self.rect.x + 100:
                self.open_door = True
                if not self.open_door_sound:
                    self.open_door_sound = True
                    self.sounds['open_door'].play()
            elif not self.reverse and self.player.x < self.rect.x - 100:
                self.open_door = True
                if not self.open_door_sound:
                    self.open_door_sound = True
                    self.sounds['open_door'].play()

        if self.mode == 'distance' and not self.close_door:
            if self.reverse and self.player.x > self.rect.x + 1000:
                self.open_door = True
                if self.open_door_sound:
                    self.open_door_sound = True
                    self.sounds['open_door'].play()
            elif not self.reverse and self.player.x > self.rect.x - 1300: 
                self.open_door = True
                if self.open_door_sound:
                    self.open_door_sound = True
                    self.sounds['open_door'].play()
    
    def update(self, dt):
        self.manage_enemies()
        self.manage_state()
        self.opened_door_logic(dt)
        self.closed_door_logic(dt)

class ParticleEffectSprite(AnimatedSprite):
    def __init__(self, pos, frames, groups):
        super().__init__(pos, frames, groups)
        self.rect.center = pos
        self.z = Z_LAYERS['fg']
    
    def animate(self, delta_time):
        self.frame_index += self.animation_speed * delta_time
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.kill()

class MovingSprite(AnimatedSprite):
    def __init__(self, frames, groups, start_pos, end_pos, move_dir, speed, flip = False):
        super().__init__(start_pos, frames, groups)
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
        self.flip = flip
        self.reverse = {'x': False, 'y': False}

    def check_border(self):
        if self.move_dir == 'x':
            if self.rect.right >= self.end_pos[0] and self.direction.x == 1: # 0 pois é onde x está posicionado
                self.direction.x = -1
                self.rect.right = self.end_pos[0]
            if self.rect.left <= self.start_pos[0] and self.direction.x == -1:
                self.direction.x = 1
                self.rect.left = self.start_pos[0]
            # Inversão dinamica do sprite para movimento em diferentes eixos
            self.reverse['x'] = True if self.direction.x < 0 else False
        else:
            if self.rect.bottom >= self.end_pos[1] and self.direction.y == 1: # 1 pois é onde y está posicionado
                self.direction.y = -1
                self.rect.bottom = self.end_pos[1]
            if self.rect.top <= self.start_pos[1] and self.direction.y == -1:
                self.direction.y = 1
                self.rect.top = self.start_pos[1]
            # Inversão dinamica do sprite para movimento em diferentes eixos
            self.reverse['y'] = True if self.direction.y > 0 else False
    
    def update(self, delta_time):
        self.old_rect = self.rect.copy()
        self.rect.topleft += self.direction * self.speed * delta_time
        self.check_border()

        self.animate(delta_time)
        if self.flip:
            self.image = pygame.transform.flip(self.image, self.reverse['x'], self.reverse['y'])

class Spike(Sprite):
    def __init__(self, pos, surface, groups, radius, speed, start_angle, end_angle, z = Z_LAYERS['main']):
        self.center = pos
        self.radius = radius
        self.speed = speed
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.angle = self.start_angle
        self.direction = 1
        self.full_circle = True if self.end_angle == -1 else False

        # Trigonometria
        x = self.center[0] + cos(radians(self.angle)) * self.radius
        y = self.center[1] + sin(radians(self.angle)) * self.radius

        super().__init__((x, y), surface, groups, z)
    
    def update(self, delta_time):
        self.angle += self.direction * self.speed * delta_time

        if not self.full_circle:
            if self.angle >= self.end_angle:
                self.direction = -1
            if self.angle < self.start_angle:
                self.direction = 1
                
        x = self.center[0] + cos(radians(self.angle)) * self.radius
        y = self.center[1] + sin(radians(self.angle)) * self.radius
        self.rect.center = (x,y)

class Cloud(Sprite):
    def __init__(self, pos, surface, groups, z=Z_LAYERS['clouds']):
        super().__init__(pos, surface, groups, z)
        self.speed = randint(50,120)
        self.direction = -1
        self.rect.midbottom = pos

    def update(self, delta_time):
        self.rect.x += self.direction * self.speed * delta_time

        if self.rect.right <= 0:
            self.kill()