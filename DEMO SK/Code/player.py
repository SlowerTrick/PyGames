from settings import *
from timecount import Timer
from os.path import join
from math import sin

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, semi_collision_sprites, frames, data, audio_files):
        # Setup Geral
        super().__init__(groups)
        self.z = Z_LAYERS['main']
        self.data = data

        # Imagem
        self.frames, self.frame_index = frames, 0
        self.state, self.facing_side = 'idle', 'right'
        self.image = self.frames[self.state][self.frame_index]

        # Retângulos
        self.rect = self.image.get_frect(topleft = pos)
        self.hitbox_rect = self.rect.inflate(-76, -36) # Acrescenta um offset no retangulo (numeros negativos)
        self.old_rect = self.hitbox_rect.copy()

        # Movimento
        self.direction = vector()
        self.speed = 200
        self.gravity = 1300
        self.jump = False
        self.jump_height = 700
        self.attacking = False

        # Colisão
        self.collision_sprites = collision_sprites
        self.semi_collision_sprites = semi_collision_sprites
        self.on_surface = {'floor': False, 'left_wall': False, 'right_wall': False}
        self.platform = None

        # Temporizador
        self.timers = {
            'wall_jump': Timer(400),
            'wall_slide_block': Timer(250),
            'platform_skip': Timer(100),
            'attack_block': Timer(500),
            'invincibility_frames': Timer(500),
            'jump_sound': Timer(100)
        }

        # Áudio
        self.audio_files = audio_files
        self.audio_files['attack'].set_volume(0.5)

        # self.display_surface = pygame.display.get_surface() para mostrar possiveis caixas de colisão
        # pygame.draw.rect(self.display_surface, 'red', floor_rect)
        # pygame.draw.rect(self.display_surface, 'red', right_rect)
        #pygame.draw.rect(self.display_surface, 'red', left_rect)

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = vector(0,0)

        if not self.timers['wall_jump'].active:

            if keys[pygame.K_RIGHT]:
                input_vector.x += 1
                self.facing_side = 'right'

            if keys[pygame.K_LEFT]: 
                input_vector.x -= 1
                self.facing_side = 'left'

            if keys[pygame.K_DOWN]: 
                self.timers['platform_skip'].activate()
            
            if keys[pygame.K_z]:
                self.attack()

            # Mantém a distancia do vetor e mantém o seu tamanho uniforme
            self.direction.x = input_vector.normalize().x if input_vector else 0
        
        if keys[pygame.K_SPACE]:
            self.jump = True
    
    def attack(self):
        if not self.timers['attack_block'].active:
            self.attacking = True
            self.frame_index = 0 # Reseta os frames para dar prioridade ao ataque
            self.timers['attack_block'].activate()
            self.audio_files['attack'].play()

    def move(self, delta_time):
        # Horizontal 
        self.hitbox_rect.x += self.direction.x * self.speed * delta_time
        self.collision('horizontal')

        # Vertical 
        if not self.on_surface['floor'] and any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active:
            self.direction.y = 0
            self.hitbox_rect.y += self.gravity / 10 * delta_time
        else:
            self.direction.y += self.gravity / 2 * delta_time
            self.hitbox_rect.y += self.direction.y * delta_time
            self.direction.y += self.gravity / 2 * delta_time

        if self.jump:
            if self.on_surface['floor']:
                self.direction.y = -self.jump_height
                self.timers['wall_slide_block'].activate()
                self.hitbox_rect.bottom -= 1
                if not self.timers['jump_sound'].active:
                    self.audio_files['jump'].play()
                    self.timers['jump_sound'].activate()

            elif any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active:
                self.timers['wall_jump'].activate()
                self.direction.y = -self.jump_height
                self.direction.x = 1 if self.on_surface['left_wall'] else -1
                
                if not self.timers['jump_sound'].active:
                    self.audio_files['wall_jump'].play()
                    self.timers['jump_sound'].activate()

            self.jump = False
            
        self.collision('vertical')
        self.semi_collision()
        self.rect.center = self.hitbox_rect.center

    def platform_move(self, delta_time):
        if self.platform:
            self.hitbox_rect.topleft += self.platform.direction * self.platform.speed * delta_time
            self.rect.center = self.hitbox_rect.center

    def check_contact(self):
        floor_rect = pygame.Rect(self.hitbox_rect.bottomleft,(self.hitbox_rect.width,2))
        right_rect = pygame.Rect(self.hitbox_rect.topright + vector(0, self.hitbox_rect.height / 4),(2,self.hitbox_rect.height / 2))
        left_rect = pygame.Rect(self.hitbox_rect.topleft + vector(-2, self.hitbox_rect.height / 4),(2,self.hitbox_rect.height / 2))
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

        if self.attacking and self.frame_index > len(self.frames[self.state]):
            self.attacking = False

    def get_state(self):
        if self.on_surface['floor']:
            if self.attacking:
                self.state = 'attack'
            else:
                self.state = 'idle' if self.direction.x == 0 else 'run'
        else:
            if self.attacking:
                self.state = 'air_attack'
            else:
                if any((self.on_surface['left_wall'], self.on_surface['right_wall'])):
                    self.state = 'wall'
                else:
                    self.state = 'jump' if self.direction.y < 0 else 'fall'

    def get_damage(self):
        self.data.health -= 1
        self.timers['invincibility_frames'].activate()
    
    def flicker(self):
        if self.timers['invincibility_frames'].active and sin(pygame.time.get_ticks() * 200) >= 0:
            white_mask = pygame.mask.from_surface(self.image)
            white_surf = white_mask.to_surface()
            white_surf.set_colorkey('black')
            self.image = white_surf

    def update(self, delta_time):
        # Updates de hitbox e temporizadores
        self.old_rect = self.hitbox_rect.copy()
        self.update_timers()

        # Movimento do jogo e colisão
        self.input()
        self.move(delta_time)
        self.platform_move(delta_time)
        self.check_contact()

        # Animação
        self.get_state()
        self.animate(delta_time)
        self.flicker()