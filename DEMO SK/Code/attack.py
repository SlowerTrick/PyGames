from settings import *
from timecount import Timer

class Neutral_Attack(pygame.sprite.Sprite):
    def __init__(self, pos, groups, frames, facing_side, vertical_sight, jumping):
        super().__init__(groups)

        self.frames = frames
        self.frame_index = 0  # Iniciando o índice de frames em 0
        self.animation_direction = 'none'

        # Definindo direção e inicialização do frame_index e animation_direction
        if vertical_sight == 'down':
            self.animation_direction = 'right' if facing_side == 'right' else 'left'
            self.frame_index = 0 if self.animation_direction == 'right' else len(self.frames[vertical_sight]) - 0.01
        elif vertical_sight == 'up':
            self.animation_direction = 'left' if facing_side == 'left' else 'right'
            self.frame_index = 0 if self.animation_direction == 'right' else len(self.frames[vertical_sight]) - 0.01
        elif facing_side in {'left', 'right'}:
            self.animation_direction = 'right'
            self.frame_index = 0

        # Armazenar a direção inicial
        self.facing_side = facing_side
        self.vertical_sight = vertical_sight
        self.jumping = jumping
        self.knockback_applied = False

        self.z = Z_LAYERS['main']
        self.timers = {'lifetime': Timer(200)}
        self.timers['lifetime'].activate()

        self.image = self.frames[self.facing_side][int(self.frame_index)]
        self.update_position(pos)

    def update_position(self, pos):
        if self.vertical_sight == 'down' and self.jumping:
            attack_pos = (pos[0] - 30, pos[1] + 45)
            self.facing_side = 'down'
        elif self.vertical_sight == 'up':
            attack_pos = (pos[0] - 30, pos[1] - 45)
            self.facing_side = 'up'
        else:
            attack_pos = (pos[0] + 30, pos[1] - 10) if self.facing_side == 'right' else (pos[0] - 80, pos[1] - 10)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = attack_pos

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()
        if not self.timers['lifetime'].active:
            self.kill()

        # Atualizar a animação
        if self.animation_direction == 'right':
            self.frame_index += ANIMATION_SPEED * dt * 3
            if self.frame_index >= 1:
                self.frame_index = 1
        elif self.animation_direction == 'left':
            self.frame_index -= ANIMATION_SPEED * dt * 3
            if self.frame_index <= 1:
                self.frame_index = 1
        self.image = self.frames[self.facing_side][int(self.frame_index)]

class Throw_Attack(pygame.sprite.Sprite):
    def __init__(self, pos, groups, frames, facing_side, vertical_sight, audio_files):
        self.on_wall = False
        super().__init__(groups)

        # Setup do objeto
        self.image = frames
        self.rect = self.image.get_frect(center = pos)
        self.initial_x = pos[0]
        self.initial_y = pos[1]

        if facing_side == 'right':
            self.rect.y += 10
            self.rect.x += 70
        else:
            self.rect.y += 10
            self.rect.x -= 70
            self.initial_x -= 70 

        # Movimento e suas nuances
        self.speed = 1000
        self.initial_facing_side = facing_side
        self.going = 'forward'

        if facing_side == 'right':
            self.direction = 1
        else:
            self.direction = -1
            self.image = pygame.transform.flip(self.image, True, False)

        # Posição na tela e temporizadores
        self.z = Z_LAYERS['main']
        self.timers = {'travel_time': Timer(500), 'max_time': Timer(2000)}
        self.timers['travel_time'].activate()
        self.timers['max_time'].activate()
        self.audio_files = audio_files

    def draw_rope(self, surface, player_pos, attack_pos):
        rope_color = (255, 255, 255)
        rope_width = 2

        player_pos = list(player_pos)
        attack_pos = list(attack_pos)

        if self.initial_facing_side == 'right':
            attack_pos[0] -= 45
        else:
            attack_pos[0] += 45

        pygame.draw.line(surface, rope_color, player_pos, attack_pos, rope_width)

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()

        self.rect.x += self.direction * self.speed * dt
        if not self.timers['travel_time'].active and self.going == 'forward' and not self.speed == 0:
            self.going = 'backward'
            self.direction *= -1

        if self.initial_facing_side == 'right':
            if self.going == 'backward' and self.rect.x <= self.initial_x:
                self.kill()
                self.audio_files['catch'].play()
        else:
            if self.going == 'backward' and self.rect.x >= self.initial_x:
                self.kill()
                self.audio_files['catch'].play()
        if not self.timers['max_time']:
            self.kill()
            self.audio_files['catch'].play()