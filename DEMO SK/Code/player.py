from settings import *
from timecount import Timer
from math import sin

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, semi_collision_sprites, frames, data, audio_files):
        # Setup Geral
        super().__init__(groups)

        # Imagem
        self.frames, self.frame_index = frames, 0
        self.state, self.facing_side = 'idle', 'right'
        self.vertical_sight = 'none'
        self.image = self.frames[self.state][self.frame_index]
        self.neutral_attack_direction = 'none'

        # Retângulos
        self.rect = self.image.get_frect(topleft = pos)
        self.hitbox_rect = self.rect.inflate(-76, -36) # Acrescenta um offset no retangulo (numeros negativos)
        self.old_rect = self.hitbox_rect.copy()

        # Movimento
        self.direction = vector()
        self.speed = 200
        self.gravity = 1300
        self.jump_height = 720
        self.keys_pressed = {'jump': True, 'neutral_attack': True, 'throw_attack': True, 'dash': True}

        # Dash
        self.dash_speed = 700
        self.dash_distance = 150
        self.dash_progress = self.dash_distance
        self.dash_is_available = True
        self.dashing = False

        # Pulo
        self.jumping = False
        self.jump_key_held = False
        self.jump = False

        # Combate
        self.neutral_attacking = False
        self.throw_attacking = False
        self.throw_attack_is_available = True
        self.knockback_value = 350
        self.knockback_direction = 'none'
        self.healing = True
        self.neutral_attack_direction = 'none'

        # Colisão
        self.collision_sprites = collision_sprites
        self.semi_collision_sprites = semi_collision_sprites
        self.on_surface = {'floor': False, 'left_wall': False, 'right_wall': False}
        self.platform = None

        # Temporizadores
        self.timers = {
            'wall_jump': Timer(200),
            'wall_slide_block': Timer(250),
            'jump_buffer': Timer(100),
            'platform_skip': Timer(100),
            'neutral_attack_block': Timer(400),
            'dash_block': Timer(500),
            'invincibility_frames': Timer(500),
            'jump_sound': Timer(100),
            'hit_knockback': Timer(150),
            'attack_knockback': Timer(150),
            'healing_timer': Timer (1500),
        }
        # Áudio, data e etc
        self.data = data
        self.audio_files = audio_files
        self.audio_files['neutral_attack'].set_volume(0.5)
        self.z = Z_LAYERS['main']
        
        self.display_surface = pygame.display.get_surface()

        # Debug, caso necessário
        # self.display_surface = pygame.display.get_surface() #para mostrar possiveis caixas de colisão
        """ pygame.draw.rect(self.display_surface, 'red', floor_rect)
        pygame.draw.rect(self.display_surface, 'red', right_rect)
        pygame.draw.rect(self.display_surface, 'red', left_rect) """

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = vector(0, 0)
        self.vertical_sight = 'none'

        if not self.throw_attacking and not self.healing:
            if not self.timers['wall_jump'].active and not self.dashing:
                # Movimentação Horizontal
                if keys[pygame.K_d]:
                    input_vector.x += 1
                    self.facing_side = 'right'
                if keys[pygame.K_a]:
                    input_vector.x -= 1
                    self.facing_side = 'left'

                # Mantém a distancia do vetor e mantém o seu tamanho uniforme
                self.direction.x = input_vector.normalize().x if input_vector else 0
            
            if keys[pygame.K_w]:
                self.vertical_sight = 'up'
            elif keys[pygame.K_s]:
                self.timers['platform_skip'].activate()
                self.vertical_sight = 'down'

            # Ataque e Dash
            if keys[pygame.K_p] and not self.throw_attacking:
                if not self.keys_pressed['neutral_attack']:
                    self.neutral_attack()
                    self.keys_pressed['neutral_attack'] = True
            else:
                self.keys_pressed['neutral_attack'] = False

            if keys[pygame.K_o] and not self.neutral_attacking and self.data.unlocked_throw_attack:
                if not self.keys_pressed['throw_attack']:
                    if self.throw_attack_is_available and self.data.string_bar > 0:
                        self.data.string_bar -= 1
                        self.throw_attack()
                        self.keys_pressed['throw_attack'] = True
            else:
                self.keys_pressed['throw_attack'] = False

            if keys[pygame.K_i]:
                if not self.keys_pressed['dash']:
                    if self.dash_is_available and self.data.unlocked_dash:
                        self.dash()
                        self.keys_pressed['dash'] = True
            else:
                self.keys_pressed['dash'] = False

            # Movimentação vertical
            if keys[pygame.K_SPACE] and not self.dashing:
                self.jump_key_held = True
                if not self.keys_pressed['jump']:
                    self.jump = True
                    if not self.timers['jump_buffer'].active:
                        self.timers['jump_buffer'].activate()
                    self.keys_pressed['jump'] = True
            else:
                self.keys_pressed['jump'] = False
                self.jump_key_held = False

        if not self.throw_attacking:
            if keys[pygame.K_u] and self.data.health_regen == True and self.on_surface['floor']:
                if not self.timers['healing_timer'].active:
                    self.timers['healing_timer'].activate()
                    self.audio_files['focus_charge'].play()
                    self.frame_index = 0
                    self.state = 'healing'
                    self.healing = True
                    self.dash_progress = self.dash_distance
                if self.timers['healing_timer'].time_passed() >= 1400:
                    self.heal()
                    self.timers['healing_timer'].deactivate()
            else:
                self.healing = False
                self.audio_files['focus_charge'].stop()
                self.timers['healing_timer'].deactivate()
    
    def neutral_attack(self):
        if not self.timers['neutral_attack_block'].active:
            self.neutral_attacking = True
            self.frame_index = 0 # Reseta os frames para dar prioridade ao ataque
            self.timers['neutral_attack_block'].activate()
            self.audio_files['neutral_attack'].play()
    
    def throw_attack(self):
        if not self.throw_attacking:
            self.throw_attacking = True
            self.throw_attack_is_available = False
            self.frame_index = 0
            self.audio_files['throw'].play()
    
    def knockback(self, delta_time):
        keys = pygame.key.get_pressed()
        if self.timers['hit_knockback'].active:
            # Horizontal
            if self.knockback_direction == 'left':
                self.hitbox_rect.x += -1 * self.knockback_value * delta_time
                self.collision('horizontal')
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += 1 * self.knockback_value * delta_time
                self.collision('horizontal')
            
            # Vertical
            elif self.knockback_direction == 'up':
                self.direction.y = 0
                self.hitbox_rect.y += -1 * self.knockback_value * delta_time * 2
                self.collision('vertical')
            elif self.knockback_direction == 'down':
                self.hitbox_rect.y += 1 * self.knockback_value * delta_time
                self.collision('vertical')
            self.timers['attack_knockback'].deactivate()

        if self.timers['attack_knockback'].active:
            if self.knockback_direction == 'left' and keys[pygame.K_a]:
                self.hitbox_rect.x += -1 * self.knockback_value * delta_time
                self.collision('horizontal')
            elif self.knockback_direction == 'right' and keys[pygame.K_d]:
                self.hitbox_rect.x += 1 * self.knockback_value * delta_time
                self.collision('horizontal')

    def dash(self):
        if not self.timers['dash_block'].active:
            self.direction.x = 0
            self.direction.y = 0
            self.frame_index = 0
            self.dashing = True
            self.dash_is_available = False
            self.start_dash_on_wall = any((self.on_surface['left_wall'], self.on_surface['right_wall']))
            self.dash_progress = 0
            self.timers['dash_block'].activate()
            self.audio_files['dash'].play()

    def heal(self):
        self.audio_files['focus_heal'].play()
        self.data.health_regen = False
        self.data.player_health += 3
        self.data.string_bar -= 3
        self.state = 'idle'

    def move(self, delta_time):
        # Dash
        if self.dashing:
            if self.dash_progress < self.dash_distance:
                dash_increment = self.dash_speed * delta_time
                if self.dash_progress + dash_increment > self.dash_distance:
                    dash_increment = self.dash_distance - self.dash_progress
                elif any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and self.timers['dash_block'].time_passed() > 10:
                    self.dashing = False
                    self.dash_progress = self.dash_distance
                else:
                    self.hitbox_rect.x += dash_increment if self.facing_side == 'right' else -dash_increment
                self.dash_progress += dash_increment
            else:
                self.dashing = False
        
        # Horizontal 
        self.hitbox_rect.x += self.direction.x * self.speed * delta_time
        self.collision('horizontal')

        # Vertical 

        # Gravidade Paredes
        if not self.on_surface['floor'] and any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active and self.data.unlocked_wall_jump:
            self.dash_is_available = True
            self.direction.y = 0
            self.hitbox_rect.y += self.gravity / 10 * delta_time
        else:
            # Gravidade aerea
            if not self.dashing:
                self.direction.y += self.gravity / 2 * delta_time
                if self.direction.y > 800:
                    self.direction.y = 800
                self.hitbox_rect.y += self.direction.y * delta_time
                self.direction.y += self.gravity / 2 * delta_time
                if self.on_surface['floor']:
                    self.dash_is_available = True
                    self.throw_attack_is_available = True

        # Pulo do jogador
        if self.jump or self.timers['jump_buffer'].active:
            # Pulo normal
            if self.on_surface['floor']:
                self.jumping = True
                self.direction.y = -self.jump_height
                self.timers['wall_slide_block'].activate()
                self.hitbox_rect.bottom -= 1
                if not self.timers['jump_sound'].active:
                    self.audio_files['jump'].play()
                    self.timers['jump_sound'].activate()

            # Pulo na parede
            elif any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active and self.data.unlocked_wall_jump:
                self.timers['wall_jump'].activate()
                self.direction.y = -self.jump_height
                if self.on_surface['left_wall']:
                    self.direction.x = 1
                else:
                    self.direction.x = -1
                
                if not self.timers['jump_sound'].active:
                    self.audio_files['wall_jump'].play()
                    self.timers['jump_sound'].activate()
            self.jump = False
        
        # Verifique se a tecla de pulo foi solta para parar a subida
        if self.jumping and not self.jump_key_held:
            if self.direction.y < 0:
                self.direction.y += self.gravity * delta_time * 4
            else:
                self.jumping = False

        # Verificação para posicionar no lado correto em relação a parede
        if any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.on_surface['floor'] and self.data.unlocked_wall_jump:
            self.facing_side = 'right' if self.on_surface['left_wall'] else 'left'

        self.collision('vertical')
        self.semi_collision()
        self.knockback(delta_time)
        self.rect.center = self.hitbox_rect.center

    def platform_move(self, delta_time):
        if self.platform:
            self.hitbox_rect.topleft += self.platform.direction * self.platform.speed * delta_time
            self.rect.center = self.hitbox_rect.center

    def check_contact(self, wall_rect_size):
        # Wall rect size para evitar bugs com o ataque de lançar
        floor_rect = pygame.Rect(self.hitbox_rect.bottomleft,(self.hitbox_rect.width,2))
        right_rect = pygame.Rect(self.hitbox_rect.topright + vector(0, self.hitbox_rect.height / 4),(2,self.hitbox_rect.height / wall_rect_size))
        left_rect = pygame.Rect(self.hitbox_rect.topleft + vector(-2, self.hitbox_rect.height / 4),(2,self.hitbox_rect.height / wall_rect_size))
        collide_rects = [sprite.rect for sprite in self.collision_sprites]
        semi_collide_rects = [sprite.rect for sprite in self.semi_collision_sprites]

        # collisions
        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 or floor_rect.collidelist(semi_collide_rects) >= 0 and self.direction.y >= 0 else False
        self.on_surface['right_wall'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left_wall']  = True if left_rect.collidelist(collide_rects) >= 0 else False

        self.platform = None
        sprites = self.collision_sprites.sprites() + self.semi_collision_sprites.sprites()
        for sprite in [sprite for sprite in sprites if hasattr(sprite, 'moving')]:
            if sprite.rect.colliderect(floor_rect):
                self.platform = sprite
    
    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if axis == 'horizontal':
                    # Colisão à esquerda
                    if self.hitbox_rect.left <= sprite.rect.right and int(self.old_rect.left) >= int(sprite.old_rect.right):
                        self.hitbox_rect.left = sprite.rect.right
                    
                    # Colisão à direita
                    if self.hitbox_rect.right >= sprite.rect.left and int(self.old_rect.right) <= int(sprite.old_rect.left):
                        self.hitbox_rect.right = sprite.rect.left

                if axis == 'vertical':
                    # Colisão com o chão
                    if self.hitbox_rect.bottom >= sprite.rect.top and int(self.old_rect.bottom) <= int(sprite.old_rect.top):
                        self.hitbox_rect.bottom = sprite.rect.top
                    
                    # Colisão com o teto
                    if self.hitbox_rect.top <= sprite.rect.bottom and int(self.old_rect.top) >= int(sprite.old_rect.bottom):
                        self.hitbox_rect.top = sprite.rect.bottom
                        if hasattr(sprite, 'moving'):
                            self.hitbox_rect.top += 6

                    self.direction.y = 0
                    break

    def semi_collision(self):
        if not self.timers['platform_skip'].active:
            for sprite in self.semi_collision_sprites:
                if sprite.rect.colliderect(self.hitbox_rect):
                    if self.hitbox_rect.bottom >= sprite.rect.top and int(self.old_rect.bottom) <= sprite.old_rect.top:
                            self.hitbox_rect.bottom = sprite.rect.top
                            if self.direction.y > 0:
                                self.direction.y = 0

    def update_timers(self):
        # Atualiza todos os temporizadores estabelicidos
        for timer in self.timers.values():
            timer.update()

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.state == 'attack' and self.frame_index >= len(self.frames[self.state]):
            self.state = 'idle'
        self.image = self.frames[self.state][int(self.frame_index % len(self.frames[self.state]))]
        self.image = self.image if self.facing_side == 'right' else pygame.transform.flip(self.image, True, False)

        if self.neutral_attacking and not self.timers['neutral_attack_block'].active:
            self.neutral_attacking = False
            self.neutral_attack_direction = 'none'

    def get_state(self):
        if self.on_surface['floor']:
            if self.neutral_attacking:
                self.state = 'attack'
            else:
                self.state = 'idle' if self.direction.x == 0 else 'run'
        else:
            if self.neutral_attacking:
                self.state = 'down_attack' if self.vertical_sight == 'down' else 'up_attack'
            else:
                if any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and self.data.unlocked_wall_jump:
                    self.state = 'wall'
                else:
                    self.state = 'jump' if self.direction.y < 0 else 'fall'
        if self.healing:
            self.state = 'healing'
        if self.timers['invincibility_frames'].active:
            self.state = 'hit'
        if self.throw_attacking:
            self.state = 'throw_attack_animation'

    def get_damage(self):
        self.data.player_health -= 1
        self.timers['invincibility_frames'].activate()
    
    def flicker(self):
        if self.timers['invincibility_frames'].active and sin(pygame.time.get_ticks() * 200) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf
            self.state = 'hit'

    def update(self, delta_time):
        # Updates de hitbox e temporizadores
        self.old_rect = self.hitbox_rect.copy()
        self.update_timers()

        # Movimento do jogo e colisão
        self.input()
        if not self.throw_attacking and not self.healing:
            self.move(delta_time)
        self.platform_move(delta_time)
        if self.throw_attacking and not self.on_surface['floor']:
            self.check_contact(1.1)
        else:
            self.check_contact(2)

        # Animação
        self.get_state()
        self.animate(delta_time)
        self.flicker()