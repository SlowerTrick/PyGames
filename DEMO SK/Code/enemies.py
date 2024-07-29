from settings import *
from timecount import Timer
from random import choice
from math import sin

class Tooth(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, collision_sprites):
        super().__init__(groups)
        self.is_enemy = True
        self.frames, self.frame_index = frames, 0
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_frect(topleft = pos)
        self.z = Z_LAYERS['main']
        self.tooth_health = 3

        self.direction = choice((-1,1))
        self.collision_rects = [sprite.rect for sprite in collision_sprites]
        self.speed = 200

        self.hit_timer = Timer(300)

    def get_damage(self):
        if not self.hit_timer.active:
            self.direction *= -1
            self.hit_timer.activate()
            self.tooth_health -= 1

    def is_alive(self):
        if self.tooth_health <= 0:
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

    def is_alive(self):
        if self.wall_health <= 0:
            self.kill()

    def get_damage(self):
        if not self.hit_timer.active:
            self.hit_timer.activate()
            self.wall_health -= 1

    def update(self, dt):
        self.hit_timer.update()
        self.is_alive()

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
        self.during_knockback = Timer(500)

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
            self.kill()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def update(self, dt):
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
                    self.hitbox_rect.bottom = sprite.top
                    break
                if top_rect.colliderect(sprite):
                    self.hitbox_rect.top = sprite.bottom
                    break                 

    def move(self, dt):
        # Movimentação Horizontal
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collisions('horizontal')
        self.collisions('vertical')

        # Movimentação Vertical
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collisions('horizontal')
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
            self.kill()

    def flicker(self):
        if self.hit_timer.active and sin(pygame.time.get_ticks() * 100) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def update(self, dt):
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