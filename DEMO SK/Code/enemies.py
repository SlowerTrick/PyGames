from settings import *
from timecount import Timer
from random import choice, randint, uniform
from sprites import Item 
from math import sin

class Runner(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, collision_sprites):
        super().__init__(groups)
        self.is_enemy = True
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.image = pygame.transform.scale_by(self.image, 1.2)
        self.rect = self.image.get_frect(topleft = pos)
        self.z = Z_LAYERS['main']
        self.runner_health = 3

        self.direction = choice((-1,1))
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.speed = 200

        self.hit_timer = Timer(600)

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
        self.image = pygame.transform.scale_by(self.image, 1.2)
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

class Shell(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, reverse, player, create_pearl):
        # self.pearl = True "Caso algo de errado, vc tirou isso"
        super().__init__(groups)
        self.is_enemy = True

        if reverse:
            self.frames = {}
            for key, surfs in frames.items():
                self.frames[key] = [pygame.transform.flip(surf, True, False) for surf in surfs]
            self.bullet_direction = -1
        else:
            self.frames = frames 
            self.bullet_direction = 1

        self.frame_index = 0
        self.state = 'idle'
        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player
        self.shoot_timer = Timer(3000)
        self.hit_timer = Timer(500)
        self.has_fired = False
        self.create_pearl = create_pearl
        self.shell_health = 5
    
    def state_management(self):
        player_pos, shell_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        player_near = shell_pos.distance_to(player_pos) < 750
        player_front = shell_pos.x < player_pos.x if self.bullet_direction > 0 else shell_pos.x > player_pos.x
        player_level = abs(shell_pos.y - player_pos.y) < 30

        if player_near and player_front and player_level and not self.shoot_timer.active:
            self.state = 'fire'
            self.frame_index = 0
            self.shoot_timer.activate()

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.shell_health -= 1

    def is_alive(self):
        if self.shell_health <= 0:
            self.kill()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 300) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def update(self, dt):
        self.shoot_timer.update()
        self.hit_timer.update()
        self.state_management()

        # Animação e Ataque
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index < len(self.frames[self.state]):
            self.image = self.frames[self.state][int(self.frame_index)]

            # Disparo do projetil no frame exato desejado
            if self.state == 'fire' and int(self.frame_index) == 3 and not self.has_fired:
                self.create_pearl(self.rect.center, self.bullet_direction)
                self.has_fired = True 

        else:
            self.frame_index = 0
            if self.state == 'fire':
                self.state = 'idle'
                self.has_fired = False
        self.flicker()

class Pearl(pygame.sprite.Sprite):
    def __init__(self, pos, groups, surf, direction, speed):
        self.is_enemy = True
        self.pearl = True
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(center = pos + vector(50 * direction,8))
        self.direction = direction
        self.speed = speed
        self.z = Z_LAYERS['main']
        self.timers = {'lifetime': Timer(5000), 'reverse': Timer(500)}
        self.timers['lifetime'].activate()

    def get_damage(self):
        if not self.timers['reverse'].active:
            self.direction *= -1 
            self.timers['reverse'].activate()

    def update(self, dt):
        for timer in self.timers.values():
            timer.update()

        self.rect.x += self.direction * self.speed * dt
        if not self.timers['lifetime'].active:
            self.kill()

class Breakable_wall(pygame.sprite.Sprite):
    def __init__(self, pos, groups, surf):
        self.is_enemy = True
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect
        self.z = Z_LAYERS['main']
        self.wall_health = 3
        self.hit_timer = Timer(1000)

        # Controle do tremor
        self.shake_magnitude = 60  # Intensidade do tremor
        self.shake_timer = Timer(500, self.stop_shaking, repeat=False)   # Duração do tremor
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
    def __init__(self, pos, groups, frames, item_name, all_sprites, item_frames, item_sprite_group, data, reverse=False):
        super().__init__(groups)
        # Bools
        self.is_dead = False
        self.open_chest = True
        self.is_enemy = True

        # Sprite
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.image = pygame.transform.scale_by(self.image, 2.5)
        self.reverse = reverse
        self.all_sprites = all_sprites
        self.image = pygame.transform.flip(self.image, True, False) if self.reverse else self.image
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect

        # Item do baú
        self.item_name = item_name
        self.item_frames = item_frames
        self.item_group = item_sprite_group

        # Setup geral
        self.z = Z_LAYERS['main']
        self.chest_health = 3
        self.hit_timer = Timer(600)
        self.data = data

        # Controle do tremor
        self.shake_magnitude = 60  # Intensidade do tremor
        self.shake_timer = Timer(500, self.stop_shaking, repeat=False)   # Duração do tremor
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
    
    def is_alive(self):
        if self.chest_health <= 0 and not self.is_dead:
            self.is_dead = True
            self.create_item()
    
    def create_item(self):
        Item(
            item_type = self.item_name, 
            pos = (self.rect.centerx, self.rect.centery), 
            frames = self.item_frames, 
            groups = self.item_group, 
            data = self.data,
        )
  
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
            self.image = pygame.transform.scale_by(self.image, 2.5)
            self.image = pygame.transform.flip(self.image, True, False) if self.reverse else self.image

    def update(self, dt):
        self.hit_timer.update()
        self.shake_timer.update()
        self.is_alive()
        self.apply_shake(dt)
        self.open_chest_animation(dt)

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
            target_direction = (player_pos - fly_pos).normalize()
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
        player_near = butterfly_pos.distance_to(player_pos) < 400
        player_level = abs(butterfly_pos.y - player_pos.y) < 200

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
        self.hitbox_rect = self.rect.inflate(-75, 0)
        self.old_rect = self.hitbox_rect.copy()
        self.z = Z_LAYERS['main']
        self.player = player

        # Status
        self.direction = vector()
        self.facing_side = 'left'
        self.lace_heath = 99
        self.gravity = 1300
        self.on_ground = False
        self.player_near = False
        self.active_attack = 'none'
        self.can_move = True
        self.can_attack = True

        # Dash Vertical
        self.dash_speed = 650
        self.dash_distance = 400
        self.dash_progress = self.dash_distance

        # Jump
        self.jump_speed = 700
        self.jump_distance = 280
        self.jump_progress = self.jump_distance
        self.spike_speed = 650

        # Colisões e timers
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.hit_timer = Timer(500)
        self.cycle = 1300
        self.timers = {
            'cycle_attacks': Timer(self.cycle)
        }

    def collisions(self, axis):
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
            if not self.on_ground and not self.active_attack == 'air':
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

    def attack(self, dt):
        if not self.timers['cycle_attacks'].active:
            self.timers['cycle_attacks'].activate()
            attack = randint(0, 2)
            self.active_attack = ['dash', 'multi', 'air'][attack]
            self.can_attack = True
        elif self.timers['cycle_attacks'].time_passed() > self.cycle - 200:
            self.active_attack = 'cooldown'
        
        # Atualizar estado baseado no ataque ativo
        if self.active_attack != 'cooldown' and self.can_attack:
            self.can_attack = False
            self.state = self.active_attack
            if self.active_attack == 'dash':
                self.dash_progress = 0
            elif self.active_attack == 'air':
                self.jump_progress = 0

    def state_management(self):
        player_pos, lace_pos = vector(self.player.hitbox_rect.center), vector(self.rect.center)
        self.player_near = lace_pos.distance_to(player_pos) < 2000
        player_level = abs(lace_pos.y - player_pos.y) < 500

        if self.player_near and self.active_attack == 'cooldown' and self.on_ground:
            self.facing_side = 'left' if player_pos.x <= lace_pos.x else 'right'

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
            self.lace_heath -= 1

    def is_alive(self):
        if self.lace_heath <= 0:
            self.kill()

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

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        self.image = self.frames[self.state][int(self.frame_index % len(self.frames[self.state]))]
        self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)

    def update(self, dt):
        self.update_timers()
        self.state_management()
        self.attack(dt)

        self.animate(dt)
        self.flicker()

        self.move(dt)