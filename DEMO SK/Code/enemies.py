from settings import *
from timecount import Timer
from random import choice, randint, uniform
from sprites import Item, ParticleEffectSprite
from attack import Lace_shockwave, Lace_parry
from audio import AudioManager
from math import sin

class Runner(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, collision_sprites):
        super().__init__(groups)
        self.is_enemy = True
        self.is_dead = False

        # Alteração inicial do tamanho dos sprites
        self.frames = [pygame.transform.scale_by(frame, 1.2) for frame in frames]
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(topleft=pos)

        self.z = Z_LAYERS['main']
        self.runner_health = 3

        self.direction = choice((-1, 1))
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.speed = 300

        self.hit_timer = Timer(600)
        self.death_animation_timer = Timer(3000)

        # Death animation
        self.angle = 0
        self.is_dead = False
        self.death_animation_timer.activate()

    def get_damage(self):
        if not self.hit_timer.active:
            self.direction *= -1
            self.hit_timer.activate()
            self.runner_health -= 1

    def is_alive(self):
        if self.runner_health <= 0:
            self.kill()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf
            
    def update(self, dt):
        self.hit_timer.update()

        # animação
        self.frame_index += ANIMATION_SPEED * dt
        self.image = self.frames[int(self.frame_index % len(self.frames))]
        self.image = pygame.transform.flip(self.image, True, False) if self.direction < 0 else self.image
        self.flicker()

        # movimento
        self.rect.x += self.direction * self.speed * dt

        # inverter direção
        floor_rect_right = pygame.FRect(self.rect.bottomright, (1,1))
        floor_rect_left = pygame.FRect(self.rect.bottomleft, (-1,1))
        wall_rect = pygame.FRect(self.rect.topleft + vector(-1,0), (self.rect.width + 5, 2))

        if floor_rect_right.collidelist(self.collision_rects) < 0 and self.direction > 0 or\
        floor_rect_left.collidelist(self.collision_rects) < 0 and self.direction < 0 or \
        wall_rect.collidelist(self.collision_rects) != -1:
            self.direction *= -1

class Gulka(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, create_pearl, facing_direction):
        super().__init__(groups)
        self.is_enemy = True
        self.is_gulka = True

        # Definição da direção dos sprites
        self.frames = {}
        for key, surfs in frames.items():
            if facing_direction == 'up':
                self.frames[key] = surfs
            elif facing_direction == 'down':
                self.frames[key] = [pygame.transform.rotate(surf, 180) for surf in surfs]
            elif facing_direction == 'left':
                self.frames[key] = [pygame.transform.rotate(surf, 90) for surf in surfs]
            elif facing_direction == 'right':
                self.frames[key] = [pygame.transform.rotate(surf, 270) for surf in surfs]

        self.bullet_direction = facing_direction
        self.frame_index = 0
        self.state = 'idle'
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft=pos)
        self.old_rect = self.rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player
        self.player_pos = None
        self.shoot_timer = Timer(2000)
        self.hit_timer = Timer(500)
        self.has_fired = False
        self.create_pearl = create_pearl
        self.gulka_health = 4
        self.facing_direction = facing_direction

    def state_management(self):
        player_pos, gulka_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        player_near = gulka_pos.distance_to(player_pos) < 1200

        if self.bullet_direction in ['left', 'right']:
            player_front = (gulka_pos.x < player_pos.x if self.bullet_direction == 'right' else gulka_pos.x > player_pos.x)
            player_level = abs(gulka_pos.y - player_pos.y) < 30
        else:
            player_front = (gulka_pos.y > player_pos.y if self.bullet_direction == 'up' else gulka_pos.y < player_pos.y)
            player_level = abs(gulka_pos.x - player_pos.x) < 30

        if player_near and player_front and player_level and not self.shoot_timer.active:
            self.state = 'fire'
            self.frame_index = 0
            self.shoot_timer.activate()

    def shoot(self):
        # Dispara uma pérola na direção apropriada
        if self.player_pos is None:
            if self.bullet_direction in ['up', 'down']:
                self.player_pos = (self.rect.centerx, self.player.rect.centery)
            else:
                self.player_pos = (self.player.rect.centerx, self.rect.centery)

        self.create_pearl((self.rect.center), self.player_pos)
        self.has_fired = True
        self.player_pos = None

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.gulka_health -= 1

    def is_alive(self):
        if self.gulka_health <= 0:
            self.kill()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 300) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index < len(self.frames[self.state]):
            self.image = self.frames[self.state][int(self.frame_index)]

            # Disparo no momento certo da animação
            if self.state == 'fire' and int(self.frame_index) == 3 and not self.has_fired:
                self.shoot()
        else:
            self.frame_index = 0
            if self.state == 'fire':
                self.state = 'idle'
                self.has_fired = False

    def update(self, dt):
        self.shoot_timer.update()
        self.hit_timer.update()
        self.state_management()
        self.animate(dt)
        self.flicker()

class Pearl(pygame.sprite.Sprite):
    def __init__(self, pos, groups, surf, target_pos, speed):
        self.is_enemy = True
        self.pearl = True
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.speed = speed
        self.z = Z_LAYERS['main']
        
        # Vetor direção calculado e normalizado
        self.position = vector(pos)  # Posição inicial
        self.target_pos = vector(target_pos)  # Posição do alvo
        direction_vector = self.target_pos - self.position
        self.direction = direction_vector.normalize() if direction_vector.length() > 0 else vector(0, 0)

        self.timers = {'lifetime': Timer(5000), 'reverse': Timer(500)}
        self.timers['lifetime'].activate()

    def get_damage(self):
        if not self.timers['reverse'].active:
            self.direction *= -1
            self.timers['reverse'].activate()

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()

        # Movimento constante na direção calculada
        self.position += self.direction * self.speed * dt
        self.rect.center = self.position

        # Verifica se o tempo de vida expirou
        if not self.timers['lifetime'].active:
            self.kill()

class Breakable_wall(pygame.sprite.Sprite):
    def __init__(self, pos, groups, surf):
        self.is_enemy = True
        self.is_breakable_wall = True
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.old_rect = self.rect
        self.z = Z_LAYERS['main']
        self.wall_health = 3
        self.hit_timer = Timer(1000)

        # Controle do tremor
        self.shake_magnitude = 1.25  # Intensidade do tremor (distância máxima para os lados)
        self.shake_speed = 3  # Velocidade do tremor (quantidade de oscilações por segundo)
        self.shake_timer = Timer(500, self.stop_shaking, repeat=False)  # Duração do tremor
        self.original_x = self.rect.x
        self.time_elapsed = 0  # Tempo acumulado para cálculo do tremor

    def start_shaking(self):
        self.shake_timer.activate()
        self.original_x = self.rect.x
        self.time_elapsed = 0

    def stop_shaking(self):
        self.shake_timer.deactivate()

    def apply_shake(self, dt):
        if self.shake_timer.active:
            self.time_elapsed += dt
            self.time_elapsed %= (1 / self.shake_speed)
            # Cálculo do deslocamento como uma senoide
            offset = self.shake_magnitude * sin(2 * 3.14 * self.shake_speed * self.time_elapsed)
            self.rect.x = self.original_x + offset
        else:
            # Retorna ao centro quando o tremor para
            self.rect.x = self.original_x

    def is_alive(self):
        if self.wall_health <= 0:
            self.kill()

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.wall_health -= 1
            self.start_shaking()
            self.original_x = self.rect.x

    def update(self, dt):
        self.hit_timer.update()
        self.shake_timer.update()
        self.is_alive()
        self.apply_shake(dt)

class Chest(pygame.sprite.Sprite):
    def __init__(self, pos, groups, frames, item_name, all_sprites, item_frames, item_sprite_group, data, sounds, reverse=False):
        super().__init__(groups)
        # Bools
        self.is_dead = False
        self.open_chest = True
        self.is_enemy = True

        # Alteração inicial do tamanho dos sprites
        self.frames = [
            pygame.transform.scale_by(pygame.transform.flip(frame, True, False) if reverse else frame, 2.5)
            for frame in frames['chest']
        ]
        self.particle_frames = [
            pygame.transform.scale_by(pygame.transform.flip(frame, True, False) if reverse else frame, 2.5)
            for frame in frames['particle']
        ]
        # Setup dos frames
        self.frame_index = 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(topleft=pos)
        self.old_rect = self.rect
        self.all_sprites = all_sprites

        # Item do baú
        self.item_name = item_name
        self.item_frames = item_frames
        self.item_group = item_sprite_group
        self.item_sprite = None

        # Setup geral
        self.z = Z_LAYERS['main']
        self.chest_health = 3
        self.hit_timer = Timer(600)
        self.data = data
        self.sounds = sounds

        # Controle do tremor
        self.shake_magnitude = 60  # Intensidade do tremor
        self.shake_timer = Timer(500, self.stop_shaking, repeat=False)  # Duração do tremor
        self.original_x = self.rect.x
    
    def start_shaking(self):
        self.shake_timer.activate()
        self.original_x = self.rect.x
        self.original_y = self.rect.y
    
    def stop_shaking(self):
        self.shake_timer.deactivate()

    def apply_shake(self, dt):
        if self.shake_timer.active:
            self.rect.x += uniform(-self.shake_magnitude, self.shake_magnitude) * dt
        else:
            if abs(self.rect.x - self.original_x) > self.shake_magnitude:
                self.rect.x = (self.original_x + (self.rect.x - self.original_x) / abs(self.rect.x - self.original_x) * self.shake_magnitude) * dt
            else:
                self.rect.x = self.original_x 
    
    def create_particle(self):
        ParticleEffectSprite(
            pos = self.rect.center + vector(0, -30),
            frames = self.particle_frames,
            groups = self.all_sprites
        )

    def create_item(self):
        self.sounds['chest_open'].play()
        self.item_sprite = Item(
            item_type = self.item_name, 
            pos = self.rect.center + + vector(0, -20), 
            frames = self.item_frames, 
            groups = self.item_group, 
            data = self.data,
        )

    def is_alive(self):
        if self.chest_health <= 0 and not self.is_dead:
            self.is_dead = True
            self.create_particle()
            self.create_item()
    
    
    def manage_item(self):
        # Verifica se o item foi criado e ainda existe
        if self.item_sprite and self.item_sprite.alive():
            self.sounds['special_item_loop'].play()
        else:
            self.sounds['special_item_loop'].stop()

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.chest_health -= 1
            self.start_shaking()
            self.original_x = self.rect.x

    def open_chest_animation(self, dt):
        if self.is_dead and self.open_chest:
            self.frame_index += ANIMATION_SPEED * dt
            self.image = self.frames[int(self.frame_index % len(self.frames))]
            if self.frame_index >= len(self.frames) - 1:
                self.open_chest = False

    def update(self, dt):
        self.hit_timer.update()
        self.shake_timer.update()
        self.is_alive()
        self.apply_shake(dt)
        self.open_chest_animation(dt)
        self.manage_item()

class Slime(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites):
        # Setup geral
        super().__init__(groups)
        self.is_enemy = True
        self.frame_index = 0
        self.frames = frames 
        self.state = 'idle'

        # Frames 
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.hitbox_rect = self.rect
        self.old_rect = self.rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player

        # Status
        self.direction = vector()
        self.speed = 150
        self.jump_height = 450
        self.slime_heath = 3
        self.gravity = 1300
        self.knockback_value = 350
        self.knockback_direction = 'none'
        self.on_ground = False
        self.player_near = False

        # Colisões e timers
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.hit_timer = Timer(500)
        self.death_animation_timer = Timer(3000)
        self.during_knockback = Timer(500)

        # Death animation
        self.angle = 0
        self.is_dead = False

    def collisions(self, axis):
        top_rect = pygame.FRect(self.rect.midtop, (1, 1))
        floor_rect = pygame.FRect(self.rect.midbottom, (1, 1))
        right_rect = pygame.FRect(self.rect.midleft, (1, 1))
        left_rect = pygame.FRect(self.rect.midright, (1, 1))

        if axis == 'horizontal':
            for sprite in self.collision_rects:
                if right_rect.colliderect(sprite) or left_rect.colliderect(sprite):
                    if right_rect.x < sprite.x:
                        self.hitbox_rect.right = sprite.left
                    else:
                        self.hitbox_rect.left = sprite.right
                    self.during_knockback.deactivate()
                    break

        if axis == 'vertical':
            for sprite in self.collision_rects:
                if floor_rect.colliderect(sprite):
                    self.hitbox_rect.bottom = sprite.top
                    self.direction.y = 0
                    if self.player_near:
                        self.direction.y = -self.jump_height
                    if self.knockback_direction == 'down':
                        self.during_knockback.deactivate()
                    break
                if top_rect.colliderect(sprite):
                    self.hitbox_rect.top = sprite.bottom
                    self.direction.y = 0
                    self.during_knockback.deactivate()
                    break

    def move(self, dt):
        # Movimentação Horizontal
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collisions('horizontal')

        # Movimentação Vertical
        self.direction.y += self.gravity / 2 * dt
        self.hitbox_rect.y += self.direction.y * dt
        self.direction.y += self.gravity / 2 * dt
        self.collisions('vertical')
        self.knockback(dt)

        # Finalização do movimento
        self.rect.center = self.hitbox_rect.center

    def knockback(self, delta_time):
        if self.during_knockback.active:
            if self.knockback_direction == 'left':
                self.hitbox_rect.x += -1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += 1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'down':
                self.hitbox_rect.y += 1 * self.knockback_value * delta_time
                self.collisions('vertical')

    def state_management(self):
        player_pos, slime_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        self.player_near = slime_pos.distance_to(player_pos) < 400
        player_level = abs(slime_pos.y - player_pos.y) < 200

        if self.player_near and player_level:
            if player_pos.x <= slime_pos.x:
                self.direction.x = -1
                self.speed = 150
            else:
                self.direction.x = 1
                self.speed = 150
        else:
            self.speed = 0

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.slime_heath -= 1

    def is_alive(self):
        if self.slime_heath <= 0:
            self.is_dead = True
            self.state = 'idle'
            self.frame_index = 0
            self.death_animation_timer.activate()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def death_animation(self, dt):
        self.death_animation_timer.update()
        if self.death_animation_timer.active:
            self.angle += 3
            if self.angle >= 360:
                self.angle = 0

            # Rotação da imagem
            self.image = pygame.transform.rotate(self.frames[self.state][self.frame_index], self.angle)
            self.rect = self.image.get_rect(center=self.hitbox_rect.center)

            # Movimentação do sprite Horizontal
            if self.knockback_direction == 'left':
                self.hitbox_rect.x -= self.direction.x * self.speed * dt / 2
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += self.direction.x * self.speed * dt / 2

            # Movimentação do sprite vertical
            self.direction.y += self.gravity / 2 * dt
            self.hitbox_rect.y += self.direction.y * dt
            self.direction.y += self.gravity / 2 * dt
            self.rect.center = self.hitbox_rect.center
        else:
            self.kill()

    def update(self, dt):
        if not self.is_dead:
            self.hit_timer.update()
            self.during_knockback.update()
            self.state_management()

            # Animação
            self.frame_index += ANIMATION_SPEED * dt
            if self.frame_index < len(self.frames[self.state]):
                self.image = self.frames[self.state][int(self.frame_index)]
            else:
                self.frame_index = 0
            self.image = pygame.transform.flip(self.image, True, False) if self.direction.x < 0 else self.image
            self.flicker()

            self.move(dt)
        else:
            self.death_animation(dt)

class Fool_eater(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, facing_direction, sounds):
        super().__init__(groups)
        self.is_enemy = True
        self.frame_index = 0
        self.audio_files = sounds

        # Definição da direção dos sprites
        self.frames = {}
        for key, surfs in frames.items():
            if facing_direction in ('left', 'right'):
                self.frames[key] = [pygame.transform.rotate(surf, 90) for surf in surfs]
            elif facing_direction == 'down':
                self.frames[key] = [pygame.transform.rotate(surf, 180) for surf in surfs]
            else:
                self.frames[key] = surfs

        if facing_direction == 'right':
            for key, surfs in self.frames.items():
                self.frames[key] = [pygame.transform.flip(surf, True, False) for surf in surfs]

        self.state = 'idle'
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft=pos)
        self.z = Z_LAYERS['main']
        self.player = player

        # Status
        self.player_near = False
        self.facing_direction = facing_direction
        self.soul_eater_health = 3
        self.gravity = 1300
        self.sound_played = False

        # Colisões e timers
        self.hit_timer = Timer(500)
        self.cooldown_timer = Timer(500)
        self.death_animation_timer = Timer(3000)

        # Death animation
        self.is_dead = False

        # Ajuste da posição
        if facing_direction == 'down':
            self.rect.y += 80

    def state_management(self, dt):
        player_collide = self.rect.colliderect(self.player.hitbox_rect)
        if player_collide and not self.cooldown_timer.active:
            self.state = 'attack'
            self.cooldown_timer.activate()
        elif not player_collide and not self.cooldown_timer.active:
            self.state = 'idle'

        if self.frame_index == 1:
            if not self.sound_played:
                self.sound_played = True
                self.audio_files['bite'].play()
            self.is_dead = False
        else:
            if self.frame_index == 0:
                self.sound_played = False
            self.is_dead = True

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.soul_eater_health -= 1

    def is_alive(self):
        if self.soul_eater_health <= 0:
            self.kill()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def animate(self, dt):
        if self.state == 'attack':
            self.frame_index += ANIMATION_SPEED * dt
            if self.frame_index < len(self.frames[self.state]):
                self.image = self.frames[self.state][int(self.frame_index)]
            else:
                self.frame_index = len(self.frames[self.state]) - 1
        else:
            self.frame_index -= ANIMATION_SPEED * dt
            if self.frame_index > 0:
                self.image = self.frames['attack'][int(self.frame_index)]
            else:
                self.frame_index = 0
                self.image = self.frames['idle'][int(self.frame_index)]

    def update_timers(self):
        self.hit_timer.update()
        self.death_animation_timer.update()
        self.cooldown_timer.update()

    def update(self, dt):
        self.update_timers()
        self.state_management(dt)
        self.animate(dt)
        self.flicker()

class Fly(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites):
        super().__init__(groups)
        self.is_enemy = True
        self.frame_index = 0
        self.frames = frames 
        self.state = 'idle'

        # Frames 
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft=pos)
        self.hitbox_rect = self.rect
        self.old_rect = self.rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player

        # Status
        self.direction = vector()
        self.speed = 200
        self.max_speed = 150
        self.acceleration = 10
        self.deceleration = 10
        self.jump_height = 450
        self.fly_health = 3
        self.gravity = 1300
        self.knockback_value = 250
        self.knockback_direction = 'none'
        self.on_ground = False
        self.player_near = False

        # Colisões e timers
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.hit_timer = Timer(500)
        self.during_knockback = Timer(300)
        self.death_animation_timer = Timer(3000)

        # Death animation
        self.angle = 0
        self.is_dead = False

    def collisions(self, axis):
        top_rect = pygame.FRect(self.rect.midtop, (1, 1))
        floor_rect = pygame.FRect(self.rect.midbottom, (1, 1))
        right_rect = pygame.FRect(self.rect.midleft, (1, 1))
        left_rect = pygame.FRect(self.rect.midright, (1, 1))

        if axis == 'horizontal':
            for sprite in self.collision_rects:
                if right_rect.colliderect(sprite) or left_rect.colliderect(sprite):
                    if right_rect.x < sprite.x:
                        self.hitbox_rect.right = sprite.left - 1
                        self.during_knockback.deactivate()
                    else:
                        self.hitbox_rect.left = sprite.right + 1
                        self.during_knockback.deactivate()
                    break

        if axis == 'vertical':
            for sprite in self.collision_rects:
                if floor_rect.colliderect(sprite):
                    self.hitbox_rect.bottom = sprite.top - 1
                    break
                if top_rect.colliderect(sprite):
                    self.hitbox_rect.top = sprite.bottom
                    break                 

    def move(self, dt):
        # Movimentação Horizontal
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collisions('horizontal')

        # Movimentação Vertical
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collisions('vertical')
        self.knockback(dt)

        # Finalização do movimento
        self.rect.center = self.hitbox_rect.center

    def knockback(self, delta_time):
        if self.during_knockback.active:
            if self.knockback_direction == 'left':
                self.hitbox_rect.x += -1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += 1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'up':
                self.hitbox_rect.y += -1 * self.knockback_value * delta_time
                self.collisions('vertical')
            elif self.knockback_direction == 'down':
                self.hitbox_rect.y += 1 * self.knockback_value * delta_time
                self.collisions('vertical')

    def state_management(self, dt):
        player_pos, fly_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        self.player_near = fly_pos.distance_to(player_pos) < 400
        player_level = abs(fly_pos.y - player_pos.y) < 450

        if self.player_near and player_level:
            target_vector = player_pos - fly_pos
        
            if target_vector.length() > 0:  # Verifica se o vetor não é zero
                target_direction = target_vector.normalize()
                self.direction.x += target_direction.x * self.acceleration
                self.direction.y += target_direction.y * self.acceleration

                if self.direction.length() > 1:
                    self.direction = self.direction.normalize()
        else:
            self.direction.x *= (1 - self.deceleration * dt)
            self.direction.y *= (1 - self.deceleration * dt)

        if self.direction.length() < 0.1:
            self.direction.x = 0
            self.direction.y = 0

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.fly_health -= 1

    def is_alive(self):
        if self.fly_health <= 0:
            self.is_dead = True
            self.state = 'idle'
            self.frame_index = 0
            self.death_animation_timer.activate()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf
    
    def death_animation(self, dt):
        self.death_animation_timer.update()
        if self.death_animation_timer.active:
            self.angle += 3
            if self.angle >= 360:
                self.angle = 0

            # Rotação da imagem
            self.image = pygame.transform.rotate(self.frames[self.state][self.frame_index], self.angle)
            self.rect = self.image.get_rect(center=self.hitbox_rect.center)

            # Movimentação do sprite Horizontal
            if self.knockback_direction == 'left':
                self.hitbox_rect.x -= self.direction.x * self.speed * dt / 2
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += self.direction.x * self.speed * dt / 2

            # Movimentação do sprite vertical
            self.direction.y += self.gravity / 2 * dt
            self.hitbox_rect.y += self.direction.y * dt
            self.direction.y += self.gravity / 2 * dt
            self.rect.center = self.hitbox_rect.center
        else:
            self.kill()

    def update(self, dt):
        if not self.is_dead:
            self.hit_timer.update()
            self.during_knockback.update()
            self.state_management(dt)

            # Animação
            self.frame_index += ANIMATION_SPEED * dt
            if self.frame_index < len(self.frames[self.state]):
                self.image = self.frames[self.state][int(self.frame_index)]
            else:
                self.frame_index = 0
            self.image = pygame.transform.flip(self.image, True, False) if self.direction.x < 0 else self.image
            self.flicker()

            self.move(dt)
            self.knockback(dt)
        else:
            self.death_animation(dt)

class Ranged_Fly(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites, create_pearl):
        super().__init__(groups)
        self.is_enemy = True
        self.frame_index = 0
        self.frames = frames 
        self.state = 'idle'
        self.create_pearl = create_pearl

        # Frames 
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft=pos)
        self.hitbox_rect = self.rect
        self.old_rect = self.rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player

        # Status
        self.direction = vector()
        self.speed = 200
        self.max_speed = 150
        self.acceleration = 10
        self.deceleration = 10
        self.jump_height = 450
        self.fly_health = 3
        self.gravity = 1300
        self.knockback_value = 250
        self.stop_distance = 300
        self.knockback_direction = 'none'
        self.facing_side = 'right'
        self.on_ground = False
        self.player_near = False

        # Colisões e timers
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.hit_timer = Timer(500)
        self.during_knockback = Timer(300)
        self.death_animation_timer = Timer(3000)
        self.shoot_timer = Timer(2000)

        # Death animation
        self.angle = 0
        self.is_dead = False

    def collisions(self, axis):
        top_rect = pygame.FRect(self.rect.midtop, (1, 1))
        floor_rect = pygame.FRect(self.rect.midbottom, (1, 1))
        right_rect = pygame.FRect(self.rect.midleft, (1, 1))
        left_rect = pygame.FRect(self.rect.midright, (1, 1))

        if axis == 'horizontal':
            for sprite in self.collision_rects:
                if right_rect.colliderect(sprite) or left_rect.colliderect(sprite):
                    if right_rect.x < sprite.x:
                        self.hitbox_rect.right = sprite.left - 1
                        self.during_knockback.deactivate()
                    else:
                        self.hitbox_rect.left = sprite.right + 1
                        self.during_knockback.deactivate()
                    break

        if axis == 'vertical':
            for sprite in self.collision_rects:
                if floor_rect.colliderect(sprite):
                    self.hitbox_rect.bottom = sprite.top - 1
                    break
                if top_rect.colliderect(sprite):
                    self.hitbox_rect.top = sprite.bottom
                    break                 

    def move(self, dt):
        # Movimentação Horizontal
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collisions('horizontal')

        # Movimentação Vertical
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collisions('vertical')
        self.knockback(dt)

        # Finalização do movimento
        self.rect.center = self.hitbox_rect.center

    def knockback(self, delta_time):
        if self.during_knockback.active:
            if self.knockback_direction == 'left':
                self.hitbox_rect.x += -1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += 1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'up':
                self.hitbox_rect.y += -1 * self.knockback_value * delta_time
                self.collisions('vertical')
            elif self.knockback_direction == 'down':
                self.hitbox_rect.y += 1 * self.knockback_value * delta_time
                self.collisions('vertical')

    def state_management(self, dt):
        player_pos, fly_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        player_near = fly_pos.distance_to(player_pos) < 500
        player_level = abs(fly_pos.y - player_pos.y) < 500

        # Calcula a distância atual até o player.
        distance_to_player = fly_pos.distance_to(player_pos)
        tolerance = distance_to_player - self.stop_distance

        if player_near and player_level:
            target_direction = vector(0, 0)
            if distance_to_player > self.stop_distance and (tolerance > 1 or tolerance < -1):
                # Fly se move em direção ao player.
                target_vector = player_pos - fly_pos
                if target_vector.length() > 0:  # Verifica se o vetor não é zero
                    target_direction = target_vector.normalize()
            elif distance_to_player < self.stop_distance and (tolerance > 1 or tolerance < -1):
                # Fly foge do player
                target_vector = fly_pos - player_pos
                if target_vector.length() > 0:  # Verifica se o vetor não é zero
                    target_direction = target_vector.normalize()

                # Atira enquanto corre
                if not self.shoot_timer.active:
                    self.shoot_timer.activate()
                    bullet_directionX = 1 if self.facing_side == 'right' else -1
                    self.create_pearl(self.rect.center, (self.player.rect.centerx, self.player.rect.centery))
            else:
                if not self.shoot_timer.active:
                    self.shoot_timer.activate()
                    bullet_direction = 1 if self.facing_side == 'right' else -1
                    self.create_pearl(self.rect.center, (self.player.rect.centerx, self.player.rect.centery))

            # Atualiza a direção do objeto.
            self.direction.x = target_direction.x * self.acceleration
            self.direction.y = target_direction.y * self.acceleration

            if self.direction.length() > 1:
                self.direction = self.direction.normalize()
        else:
            self.direction.x *= (1 - self.deceleration * dt)
            self.direction.y *= (1 - self.deceleration * dt)

        if self.direction.length() < 0.1:
            self.direction.x = 0
            self.direction.y = 0

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.fly_health -= 1

    def is_alive(self):
        if self.fly_health <= 0:
            self.is_dead = True
            self.state = 'idle'
            self.frame_index = 0
            self.death_animation_timer.activate()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf
    
    def death_animation(self, dt):
        self.death_animation_timer.update()
        if self.death_animation_timer.active:
            self.angle += 3
            if self.angle >= 360:
                self.angle = 0

            # Rotação da imagem
            self.image = pygame.transform.rotate(self.frames[self.state][self.frame_index], self.angle)
            self.rect = self.image.get_rect(center=self.hitbox_rect.center)

            # Movimentação do sprite Horizontal
            if self.knockback_direction == 'left':
                self.hitbox_rect.x -= self.direction.x * self.speed * dt / 2
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += self.direction.x * self.speed * dt / 2

            # Movimentação do sprite vertical
            self.direction.y += self.gravity / 2 * dt
            self.hitbox_rect.y += self.direction.y * dt
            self.direction.y += self.gravity / 2 * dt
            self.rect.center = self.hitbox_rect.center
        else:
            self.kill()

    def update_timers(self):
        self.shoot_timer.update()
        self.hit_timer.update()
        self.during_knockback.update()

    def update(self, dt):
        if not self.is_dead:
            self.update_timers()
            self.state_management(dt)

            # Animação
            self.facing_side = 'left' if self.rect.x > self.player.rect.x else 'right'
            self.frame_index += ANIMATION_SPEED * dt
            if self.frame_index < len(self.frames[self.state]):
                self.image = self.frames[self.state][int(self.frame_index)]
            else:
                self.frame_index = 0
            self.image = pygame.transform.flip(self.image, True, False) if self.facing_side == 'left' else self.image
            self.flicker()

            self.move(dt)
            self.knockback(dt)
        else:
            self.death_animation(dt)

class Butterfly(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player):
        # Setup geral
        super().__init__(groups)
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.speed = 300
        self.z = Z_LAYERS['main']
        self.player = player
        self.flee_active = False

        # Timers
        self.timers = {
            'flee_timer': Timer(3000)
        }
    
    def update_timers(self):
        # Atualiza todos os temporizadores estabelicidos
        for timer in self.timers.values():
            timer.update()
    
    def state_management(self):
        player_pos, butterfly_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        player_near = butterfly_pos.distance_to(player_pos) < 700
        player_level = abs(butterfly_pos.y - player_pos.y) < 100

        if player_near and player_level:
            self.flee_active = True
            self.timers['flee_timer'].activate()
    
    def update(self, dt):
        self.update_timers()
        self.state_management()

        # Animação
        self.frame_index += ANIMATION_SPEED * dt
        self.image = self.frames[int(self.frame_index % len(self.frames))]

        # Movimento
        if self.flee_active:
            self.rect.y += -self.speed * dt
            if not self.timers['flee_timer'].active:
                self.kill()

class Lace(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites, screen_shake, shockwave_groups, sounds):
        # Setup geral
        super().__init__(groups)
        self.is_enemy = True
        self.is_dead = False
        self.on_final_animation = False
        self.frame_index = 0
        self.frames = frames 
        self.state = 'idle'
        self.screen_shake = screen_shake
        self.shockwave_groups = shockwave_groups
        self.audio_files = sounds
        self.audio_manager = AudioManager()

        # Frames 
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.hitbox_rect = self.rect.inflate(-75, 0)
        self.old_rect = self.hitbox_rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player

        # Status
        self.direction = vector()
        self.facing_side = 'none'
        self.lace_heath = 50 # 50
        self.max_health = self.lace_heath
        self.gravity = 1300
        self.on_ground = False
        self.player_near = False
        self.active_attack = 'cooldown'
        self.can_move = True
        self.can_attack = True
        self.last_attack = None
        self.knockback_value = 700
        self.knockback_direction = 'none'
        self.shockwave_created = False
        self.parry_created = False
        self.spike_sound_played = False

        # Dash Vertical
        self.dash_speed = 700
        self.dash_distance = 480
        self.dash_progress = self.dash_distance

        # Jump
        self.jump_speed = 700
        self.jump_distance = 280
        self.jump_progress = self.jump_distance
        self.spike_speed = 650

        # Colisões e timers
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.hit_timer = Timer(500)
        self.during_knockback = Timer(200)
        self.cycle = 1300
        self.timers = {
            'cycle_attacks': Timer(self.cycle),
            'ultimate': Timer(2500),
            'ultimate_cooldown': Timer(10000),
            'spike': Timer(2500),
            'spike_cooldown': Timer(4000),
            'parry': Timer(2000),
            'parry_cooldown': Timer(8000),
        }

    def collisions(self, axis):
        if self.collision_rects:
            top_rect = pygame.FRect(self.hitbox_rect.midtop, (1, 1))
            floor_rect = pygame.FRect(self.hitbox_rect.midbottom, (1, 1))
            right_rect = pygame.FRect(self.hitbox_rect.midleft, (1, 1))
            left_rect = pygame.FRect(self.hitbox_rect.midright, (1, 1))

            if axis == 'horizontal':
                for sprite in self.collision_rects:
                    if right_rect.colliderect(sprite) or left_rect.colliderect(sprite):
                        if right_rect.x < sprite.x:
                            self.hitbox_rect.right = sprite.left - 1
                        else:
                            self.hitbox_rect.left = sprite.right + 1

            if axis == 'vertical':
                for sprite in self.collision_rects:
                    if floor_rect.colliderect(sprite):
                        self.hitbox_rect.bottom = sprite.top
                        self.on_ground = True
                        break
                    else:
                        self.on_ground = False

                    if top_rect.colliderect(sprite):
                        self.hitbox_rect.top = sprite.bottom
                        self.direction.y = 0
                        self.on_ground = False
                        break

    def move(self, dt):
        if self.can_move:
            # Movimentação Vertical
            if not self.on_ground and not self.active_attack == 'air' and not self.on_final_animation and not self.timers['ultimate'].active and not self.timers['spike'].active:
                self.direction.y += self.gravity / 1.5 * dt
                self.hitbox_rect.y += self.direction.y * dt
                self.direction.y += self.gravity / 1.5 * dt
                self.direction.x = 1 if self.facing_side == 'right' else -1
                self.hitbox_rect.x += self.direction.x * self.spike_speed * dt
            self.collisions('vertical')

            # Movimentação Horizontal
            self.dash(dt)
            self.collisions('horizontal')

        # Finalização do movimento
        self.rect.center = self.hitbox_rect.center

    def knockback(self, delta_time):
        knockback_block = self.timers['ultimate'].active or self.timers['parry'].active or self.timers['spike'].active
        if self.during_knockback.active and not knockback_block:
            if self.knockback_direction == 'left':
                self.hitbox_rect.x += -1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += 1 * self.knockback_value * delta_time
                self.collisions('horizontal')
            elif self.knockback_direction == 'down':
                self.hitbox_rect.y += 1 * self.knockback_value * delta_time
                self.collisions('vertical')

    def attack(self, dt):
        if self.state != 'idle':
            special_attack = self.timers['ultimate'].active or self.timers['spike'].active or self.timers['parry'].active
            if not self.timers['cycle_attacks'].active and not special_attack:
                self.timers['cycle_attacks'].activate()

                # Sorteio inicial
                player_pos, lace_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
                player_ran_away = lace_pos.distance_to(player_pos) > 600
                attack = randint(0, 3)

                # Sorteio completo
                if self.lace_heath < self.max_health / 2 and not self.timers['ultimate_cooldown'].active:
                    attack = randint(0, 4) 

                # Evita o uso de ataques em cooldown
                if attack == 2 and self.timers['parry_cooldown'].active:
                    attack = randint(0, 1)
                elif attack == 3 and self.timers['spike_cooldown'].active:
                    attack = randint(0, 2)
                elif attack == 4 and self.timers['ultimate_cooldown'].active:
                    attack = randint(0, 3)
                
                # Definição arbitraria do ataque
                self.active_attack = ['dash', 'air', 'parry', 'spike', 'ultimate'][attack]
                
                # Evitar ultimate e spike sequenciais
                if self.active_attack == 'spike' and self.last_attack == 'ultimate':
                    attack = randint(0, 2)  
                    self.active_attack = ['parry', 'dash', 'air'][attack]
                
                # Dash obrigatório após o spike
                if self.last_attack == 'spike':
                    attack = randint(0, 1)  
                    self.active_attack = ['dash', 'air'][attack]
                
                # Spike obrigatório caso o player fuja
                if player_ran_away and not self.last_attack == 'ultimate' :
                    self.active_attack = 'spike'

                self.can_attack = True
            elif self.timers['cycle_attacks'].time_passed() > self.cycle - 200:
                if not special_attack:
                    self.active_attack = 'cooldown'
                    self.state = 'cooldown'

            
            # Atualizar estado baseado no ataque ativo
            if self.active_attack != 'cooldown' and self.can_attack:
                self.can_attack = False
                self.last_attack = self.active_attack
                self.state = self.active_attack
                if self.active_attack == 'dash':
                    self.audio_manager.play_with_pitch(self.audio_files['attack'], min_pitch=70, max_pitch=130)
                    self.dash_progress = 0
                elif self.active_attack == 'air':
                    self.audio_manager.play_with_pitch(self.audio_files['attack'], min_pitch=70, max_pitch=130)
                    self.jump_progress = 0
                elif self.active_attack == 'spike':
                    self.audio_files['teleport_out'].play()
                    self.timers['spike'].activate()
                    self.timers['spike_cooldown'].activate()
                    self.frame_index = 0
                    self.spike_sound_played = False
                elif self.active_attack == 'parry':
                    self.audio_files['parry'].play()
                    self.timers['parry_cooldown'].activate()
                    self.frame_index = 0
                    self.parry_created = False
                elif self.active_attack == 'ultimate':
                    self.audio_files['teleport_out'].play()
                    self.timers['ultimate'].activate()
                    self.timers['ultimate_cooldown'].activate()
                    self.shockwave_created = False

        self.spike(dt)
        self.ultimate(dt)
        self.parry(dt)

    def parry(self, dt):
        if self.active_attack == 'parry' and not self.timers['parry'].active:
            self.frame_index = 0
            player_pos, lace_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
            self.facing_side = 'left' if player_pos.x <= lace_pos.x else 'right'
        if self.timers['parry'].active:
            self.audio_manager.play_with_pitch(self.audio_files['attack'], min_pitch=50, max_pitch=90)
            self.frame_index += ANIMATION_SPEED * dt
            if int(self.frame_index) == 4:
                self.frame_index = 1
            self.image = self.frames[self.state][int(self.frame_index % len(self.frames[self.state]))]
            self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)
            if not self.parry_created:
                self.parry_created = True
                Lace_parry(
                    pos = self.rect.center, 
                    groups = self.shockwave_groups, 
                    frames = self.frames['parry_attack'],
                    facing_side = self.facing_side, 
                )

    def spike(self, dt):
        if self.timers['spike'].active:
            time_elapsed = self.timers['spike'].time_passed()

            if time_elapsed <= 2000:
                if self.frame_index == 5:
                    if self.on_ground:
                        self.hitbox_rect.y -= 350
                    self.hitbox_rect.x = self.player.hitbox_rect.x
                
                self.frame_index += ANIMATION_SPEED * dt * 1.2
                if self.frame_index > 5:
                    self.frame_index = 5
                self.image = self.frames[self.state][int(self.frame_index)]
                self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)
            else:
                if not self.spike_sound_played:
                    self.spike_sound_played = True
                    self.audio_manager.play_with_pitch(self.audio_files['teleport_in'], volume_change=-3.0)
                    self.audio_manager.play_with_pitch(self.audio_files['attack'], min_pitch=70, max_pitch=130)
                player_pos, lace_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
                self.facing_side = 'left' if player_pos.x <= lace_pos.x else 'right'
                if self.frame_index != 6:
                    self.frame_index = 6
                self.image = self.frames[self.state][int(self.frame_index)]
                self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)

                # Objeto começa a descer
                self.hitbox_rect.y += 1000 * dt

    def ultimate(self, dt):
        if self.timers['ultimate'].active:
            time_elapsed = self.timers['ultimate'].time_passed()

            if time_elapsed > 2000:
                self.frame_index += ANIMATION_SPEED * dt
                if self.frame_index < 6:
                    self.frame_index = 6
                elif self.frame_index > 8: 
                    self.frame_index = 8

                self.image = self.frames[self.state][int(self.frame_index)]
                self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)

                self.hitbox_rect.y += 250 * dt
            else:
                if self.on_ground:
                    self.hitbox_rect.y -= 150
                self.audio_manager.play_with_pitch(self.audio_files['attack'], min_pitch=100, max_pitch=130 , volume_change=-2.0)
                self.frame_index += ANIMATION_SPEED * dt
                if int(self.frame_index % len(self.frames[self.state])) > len(self.frames[self.state]) - 4:
                    self.frame_index = 0
                self.image = self.frames[self.state][int(self.frame_index % len(self.frames[self.state]))]
                self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)

            if time_elapsed > 2400 and not self.shockwave_created:
                self.shockwave_created = True
                self.audio_files['ultimate'].play()
                self.screen_shake(500, 5)
                Lace_shockwave(
                    pos = self.rect.center, 
                    groups = self.shockwave_groups, 
                    frames = self.frames['shockwave'][0],
                    facing_side = 'right', 
                    speed = 900,
                    collision_sprites = self.collision_rects
                )
                Lace_shockwave(
                    pos = self.rect.center, 
                    groups = self.shockwave_groups, 
                    frames = self.frames['shockwave'][0],
                    facing_side = 'left', 
                    speed = 900,
                    collision_sprites = self.collision_rects
                )

    def state_management(self):
        player_pos, lace_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        player_near = lace_pos.distance_to(player_pos) < 900
        player_level = abs(lace_pos.y - player_pos.y) < 200 if self.state != 'idle' else abs(lace_pos.y - player_pos.y) <= 20

        if player_near and player_level and self.active_attack == 'cooldown' and self.on_ground:
            self.facing_side = 'left' if player_pos.x <= lace_pos.x else 'right'
            if self.state == 'idle':
                self.timers['spike_cooldown'].activate()
                self.timers['parry_cooldown'].activate()
                self.state = 'start_attacking'

    def dash(self, dt):
        if self.active_attack == 'dash':
            # Movimento Horizontal (Dash)
            if self.dash_progress < self.dash_distance:
                dash_increment = self.dash_speed * dt
                if self.dash_progress + dash_increment > self.dash_distance:
                    dash_increment = self.dash_distance - self.dash_progress
                self.hitbox_rect.x += dash_increment if self.facing_side == 'right' else -dash_increment
                self.dash_progress += dash_increment
            else:
                self.dash_progress = self.dash_distance
                self.active_attack = 'cooldown'
        
        elif self.active_attack == 'air':
            # Movimento Vertical (Air Jump)
            if self.jump_progress < self.jump_distance:
                jump_increment = self.jump_speed * dt
                if self.jump_progress + jump_increment > self.jump_distance:
                    jump_increment = self.jump_distance - self.jump_progress
                self.hitbox_rect.y -= jump_increment
                self.jump_progress += jump_increment
            else:
                self.active_attack = 'cooldown'
                self.jump_progress = self.jump_distance
                self.direction.y = 0

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            if self.active_attack == 'parry':
                if not self.timers['parry'].active:
                    self.timers['parry'].activate()
                    self.timers['parry_cooldown'].activate()
            elif not self.timers['ultimate'].active:
                self.lace_heath -= 1

    def is_alive(self):
        if self.lace_heath <= 0:
            self.on_final_animation = True
            self.is_dead = True

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def update_timers(self):
        # Atualiza todos os temporizadores estabelicidos
        for timer in self.timers.values():
            timer.update()
        self.hit_timer.update()
        self.during_knockback.update()

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        self.image = self.frames[self.state][int(self.frame_index % len(self.frames[self.state]))]
        self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)

    def final_animation(self, dt):
        self.direction.y += self.gravity / 2 * dt
        if self.direction.y > 800:
            self.direction.y = 800
        self.hitbox_rect.y += self.direction.y * dt
        self.direction.y += self.gravity / 2 * dt

    def update(self, dt):
        if not self.on_final_animation:
            self.update_timers()
            self.state_management()
            self.attack(dt)
            self.knockback(dt)

            animation_block = self.timers['ultimate'].active or self.timers['spike'].active or self.timers['parry'].active
            if not animation_block:
                self.animate(dt)
                self.flicker()

            self.move(dt)
        else:
            self.final_animation(dt)
            self.animate
            self.move(dt)