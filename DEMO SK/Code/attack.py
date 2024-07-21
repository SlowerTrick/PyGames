from settings import *
from timecount import Timer

class Neutral_Attack(pygame.sprite.Sprite):
    def __init__(self, pos, groups, frames, facing_side, vertical_sight, jumping):
        super().__init__(groups)

        self.frames = frames
        self.frame_index = 0

        # Armazenar a direção inicial
        self.facing_side = facing_side
        self.vertical_sight = vertical_sight
        self.jumping = jumping

        self.z = Z_LAYERS['main']
        self.timers = {'lifetime': Timer(400)}
        self.timers['lifetime'].activate()

        self.image = self.frames[self.facing_side][self.frame_index]
        self.rect = self.image.get_rect()

        # Chama update_position para definir a posição inicial corretamente
        self.update_position(pos)

    def update_position(self, pos):
        if self.vertical_sight == 'down' and self.jumping:
            attack_pos = (pos[0] - 25, pos[1] + 60)
            self.facing_side = 'down'
        elif self.vertical_sight == 'up':
            attack_pos = (pos[0] - 25, pos[1] - 30)
            self.facing_side = 'up'
        else:
            attack_pos = (pos[0] + 40, pos[1] - 10) if self.facing_side == 'right' else (pos[0] - 40, pos[1] - 10)
        
        self.rect.topleft = attack_pos

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()
        if not self.timers['lifetime'].active:
            self.kill()

        # Atualizar a animação
        self.frame_index += ANIMATION_SPEED * dt * 2
        self.frame_index = self.frame_index if self.frame_index < len(self.frames[self.facing_side]) else 0
        self.image = self.frames[self.facing_side][int(self.frame_index)]

class Throw_Attack(pygame.sprite.Sprite):
    def __init__(self, pos, groups, frames, facing_side, vertical_sight):
        self.on_wall = False
        super().__init__(groups)

        # Setup do objeto
        self.image = frames
        self.rect = self.image.get_frect(center = pos)
        self.initial_x = pos[0]

        if facing_side == 'right':
            self.rect.y += 30
            self.rect.x += 50
        else:
            self.rect.y += 30
            self.rect.x -= 50
            self.initial_x -= 60

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
        self.timers = {'travel_time': Timer(500), 'reverse': Timer(500)}
        self.timers['travel_time'].activate()

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
        else:
            if self.going == 'backward' and self.rect.x >= self.initial_x:
                self.kill()