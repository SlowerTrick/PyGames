from settings import *
from timecount import Timer
from math import sin
from audio import AudioManager

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites, semi_collision_sprites, frames, data, audio_files, screen_shake):
        # Setup Geral
        super().__init__(groups)
        self.audio_manager = AudioManager()

        # Imagem
        self.frames, self.frame_index = frames, 0
        self.state, self.facing_side = 'idle', 'right'
        self.vertical_sight = 'none'
        self.image = self.frames[self.state][self.frame_index]
        self.neutral_attack_direction = 'none'
        self.on_final_animation = False

        # Retângulos
        self.rect = self.image.get_frect(topleft = pos)
        self.hitbox_rect = self.rect.inflate(-76, -36) # Acrescenta um offset no retangulo (numeros negativos)
        self.old_rect = self.hitbox_rect.copy()

        # Inicialização do controle
        self.joysticks = []
        for joystick in range(pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(joystick))
        self.controller_type = self.detect_controller_type()
        self.control_mapping = self.get_control_mapping(self.controller_type)

        # Movimento
        self.direction = vector()
        self.speed = 220
        self.gravity = 1300
        self.jump_height = 720
        self.keys_pressed = {
            'jump': True, 
            'neutral_attack': True, 
            'special_attack': True,
            'switch_weapons': True,
            'use_weapon': True, 
            'dash': True
        }

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
        self.spin_attacking = False
        self.parrying = False
        self.vertical_knockback_value = 450
        self.horizontal_knockback_value = 350
        self.knockback_direction = 'none'
        self.healing = False
        self.neutral_attack_direction = 'none'
        self.using_weapon = False

        # Colisão
        self.collision_sprites = collision_sprites
        self.semi_collision_sprites = semi_collision_sprites
        self.collide_rects = [sprite.rect for sprite in self.collision_sprites]
        self.semi_collide_rects = [sprite.rect for sprite in self.semi_collision_sprites]
        self.on_surface = {'floor': False, 'left_wall': False, 'right_wall': False, 'bench': False}
        self.platform = None
        self.skippable_platform = True

        # Temporizadores
        self.timers = {
            'wall_jump': Timer(200),
            'wall_slide_block': Timer(250),
            'jump_buffer': Timer(100),
            'platform_skip': Timer(100),
            'neutral_attack_block': Timer(400),
            'parry': Timer(400),
            'parry_attack': Timer(250),
            'spin_attack_block': Timer(3000), 
            'dash_block': Timer(500),
            'invincibility_frames': Timer(500),
            'jump_sound': Timer(100),
            'hit_knockback': Timer(150),
            'heal_init': Timer(150),
            'healing': Timer(1400),
            'sitting_down': Timer(300),
        }
        # Áudio, data e etc
        self.data = data
        self.audio_files = audio_files
        self.audio_files['neutral_attack'].set_volume(0.5)
        self.audio_files['switch_weapons'].set_volume(0.5)
        self.z = Z_LAYERS['main']
        self.screen_shake = screen_shake
        
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

        if not self.throw_attacking and not self.spin_attacking and not self.timers['sitting_down'].active and not self.timers['parry'].active and not self.timers['parry_attack'].active:
            # Movimento Horizontal
            if not self.timers['wall_jump'].active and not self.dashing:
                # Movimentação Horizontal
                if (keys[pygame.K_d] or self.get_input_action("move_right")):
                    input_vector.x += 1
                    self.facing_side = 'right'
                    self.on_surface['bench'] = False
                if (keys[pygame.K_a] or self.get_input_action("move_left")):
                    input_vector.x -= 1
                    self.facing_side = 'left'
                    self.on_surface['bench'] = False

                # Mantém a distância do vetor e mantém o seu tamanho uniforme
                self.direction.x = input_vector.normalize().x if input_vector else 0
            
            # Visão vertical
            if (keys[pygame.K_w] or self.get_input_action("move_up")):
                self.vertical_sight = 'up' 
            elif (keys[pygame.K_s] or self.get_input_action("move_down")):
                self.timers['platform_skip'].activate()
                self.vertical_sight = 'down'
                self.on_surface['bench'] = False

            # Ataque Neutro
            if (keys[pygame.K_p] or self.get_input_action("neutral_attack")) and not self.throw_attacking:
                if not self.keys_pressed['neutral_attack']:
                    self.neutral_attack()
                    self.keys_pressed['neutral_attack'] = True
                    self.on_surface['bench'] = False
            else:
                self.keys_pressed['neutral_attack'] = False

            # Botão Especial
            if (keys[pygame.K_o] or self.get_input_action("special_attack")):
                if not self.keys_pressed['special_attack']:
                    self.timers['heal_init'].activate()
                    self.keys_pressed['special_attack'] = True
                if not self.timers['heal_init'].active and self.data.health_regen and self.on_surface['floor']:
                    if not self.timers['healing'].active:
                        self.timers['healing'].activate()
                        self.audio_files['focus_charge'].play()
                        self.frame_index = 0
                        self.state = 'healing'
                        self.healing = True
                        self.dash_progress = self.dash_distance
                    if self.timers['healing'].active:
                            self.screen_shake(100, 1)
                    if self.timers['healing'].time_passed() >= 1300:
                        self.heal()
                        self.timers['healing'].deactivate()
                        self.healing = False
                        self.audio_files['focus_charge'].stop()
                        self.timers['healing'].deactivate()
            else:
                if self.healing:
                    self.healing = False
                    self.audio_files['focus_charge'].stop()
                    self.timers['healing'].deactivate()
                    
                self.keys_pressed['special_attack'] = False

                if self.timers['heal_init'].active:
                    if self.throw_attack_is_available and self.data.string_bar >= 1 and self.data.unlocked_throw_attack and self.vertical_sight == 'none':
                        self.throw_attack()
                    elif self.data.string_bar >= 3 and self.vertical_sight == 'up':
                        self.spin_attack()
                    elif self.data.string_bar >= 2 and self.vertical_sight == 'down' and not self.timers['parry'].active:
                        self.parry()

            # Botões das Ferramentas
            if (keys[pygame.K_y] or self.get_input_action("switch_weapons")):
                if not self.keys_pressed['switch_weapons'] and self.data.unlocked_weapons:
                    self.keys_pressed['switch_weapons'] = True
                    self.switch_weapon()
            else:
                self.keys_pressed['switch_weapons'] = False
            
            if (keys[pygame.K_u] or self.get_input_action("use_weapon")):
                if not self.keys_pressed['use_weapon'] and self.data.string_bar >= 1 and self.data.unlocked_weapons:
                    self.keys_pressed['use_weapon'] = True
                    self.on_surface['bench'] = False
                    self.use_weapon()
            else:
                self.keys_pressed['use_weapon'] = False

            # Dash
            if (keys[pygame.K_i] or self.get_input_action("dash")):
                if not self.keys_pressed['dash']:
                    if self.dash_is_available and self.data.unlocked_dash:
                        self.dash()
                        self.keys_pressed['dash'] = True
            else:
                self.keys_pressed['dash'] = False

            # Movimentação vertical
            if (keys[pygame.K_SPACE] or self.get_input_action("jump")) and not self.dashing:
                self.jump_key_held = True
                self.on_surface['bench'] = False
                if not self.keys_pressed['jump']:
                    self.jump = True
                    if not self.timers['jump_buffer'].active:
                        self.timers['jump_buffer'].activate()
                    self.keys_pressed['jump'] = True
            else:
                self.keys_pressed['jump'] = False
                self.jump_key_held = False
    
    def detect_controller_type(self):
    # Detecta se o controle é um Xbox ou PS4 com base no nome do dispositivo.
        if pygame.joystick.get_count() > 0:
            joystick_name = self.joysticks[0].get_name().lower()
            
            xbox_keywords = ['xbox', '360', 'one', 'series']
            ps_keywords = ['ps', 'play', 'ps4', 'ds', 'dualshock', 'wireless', 'controller']

            # Verifica se qualquer palavra-chave está no nome do joystick
            if any(keyword in joystick_name for keyword in xbox_keywords):
                return 'Xbox'
            elif any(keyword in joystick_name for keyword in ps_keywords):
                return 'PS4'
        return 'Unknown'

    def get_control_mapping(self, controller_type):
        # Retorna o mapeamento de controles com base no tipo de controle (Xbox ou PS4).
        if controller_type == 'Xbox':
            return {
                # Notação: ("Eixo, Direção, Botão")
                "move_right": (0, 1),  # Eixo 0 positivo (Movimento para a direita no joystick esquerdo)
                "move_left": (0, -1),  # Eixo 0 negativo (Movimento para a esquerda no joystick esquerdo)
                "move_up": (1, -1),    # Eixo 1 negativo (Movimento para cima no joystick esquerdo)
                "move_down": (1, 1),   # Eixo 1 positivo (Movimento para baixo no joystick esquerdo)
                "jump": (0, None, 0),  # Botão 0 (Botão A no Xbox, para pulo)
                "neutral_attack": (0, None, 2),  # Botão 2 (Botão X no Xbox, para ataque neutro)
                "special_attack": (0, None, 1),  # Botão 1 (Botão B no Xbox, para ataque especial)
                "use_weapon": (0, None, 4),  # Eixo 4 positivo (Left Trigger - RA, para usar armas)
                "switch_weapons": (0, None, 5),  # Botão 5 (Right Bumper - RB, para alternar armas)
                "dash": (0, None, 3),  # Botão 3 (Botão Y no Xbox, para dash)
            }
        if controller_type == 'PS4':
            return {
                "move_right": (0, 1),  # Eixo 0 positivo (Movimento para a direita no joystick esquerdo)
                "move_left": (0, -1),  # Eixo 0 negativo (Movimento para a esquerda no joystick esquerdo)
                "move_up": (1, -1),    # Eixo 1 negativo (Movimento para cima no joystick esquerdo)
                "move_down": (1, 1),   # Eixo 1 positivo (Movimento para baixo no joystick esquerdo)
                "jump": (0, None, 0),  # Botão 0 (Botão X no PS4, para pulo)
                "neutral_attack": (0, None, 2),  # Botão 2 (Botão Square no PS4, para ataque neutro)
                "special_attack": (0, None, 1),  # Botão 1 (Botão Circle no PS4, para ataque especial)
                "use_weapon": (0, None, 9),  # Eixo 9 positivo (Left Trigger - R1, para usar armas)
                "switch_weapons": (0, None, 10),  # Eixo 10 positivo (Right Trigger - R2, para alternar armas)
                "dash": (0, None, 3),  # Botão 3 (Botão Triangle no PS4, para dash)
            }    
        else:
            return {}

    def get_input_action(self, action):
        if self.control_mapping:
            #Verifica se uma ação mapeada está ativa (eixo ou botão).
            mapping = self.control_mapping[action]
            if len(mapping) == 3:  # Botão
                return any(joystick.get_button(mapping[2]) for joystick in self.joysticks)
            elif len(mapping) == 2:  # Eixo
                axis, direction = mapping
                return any((joystick.get_axis(axis) > 0.5 if direction == 1 else joystick.get_axis(axis) < -0.5) for joystick in self.joysticks)

    def neutral_attack(self):
        if not self.timers['neutral_attack_block'].active:
            self.neutral_attacking = True
            self.frame_index = 0 # Reseta os frames para dar prioridade ao ataque
            self.timers['neutral_attack_block'].activate()
            #self.audio_files['neutral_attack'].play()
            self.audio_manager.play_with_pitch(self.audio_files['neutral_attack'], volume_change=-6.0)
    
    def throw_attack(self):
        if not self.throw_attacking:
            self.timers['heal_init'].deactivate()
            self.data.string_bar -= 1
            self.throw_attacking = True
            self.throw_attack_is_available = False
            self.frame_index = 0
            self.audio_files['throw'].play()
            self.dashing = False
            self.on_surface['bench'] = False
    
    def spin_attack(self):
        if not self.spin_attacking:
            self.timers['heal_init'].deactivate()
            self.data.string_bar -= 3
            self.spin_attacking = True
            self.frame_index = 0
            self.audio_files['throw'].play()
            self.dashing = False

    def parry(self):
        self.timers['parry'].activate()
        self.timers['heal_init'].deactivate()
        self.data.string_bar -= 2
        self.dashing = False
        self.audio_files['parry_prepare'].play()

    def knockback(self, delta_time):
        keys = pygame.key.get_pressed()
        if self.timers['hit_knockback'].active:

            # Horizontal
            if self.knockback_direction == 'left':
                self.hitbox_rect.x += -1 * self.horizontal_knockback_value * delta_time
                self.collision('horizontal')
            elif self.knockback_direction == 'right':
                self.hitbox_rect.x += 1 * self.horizontal_knockback_value * delta_time
                self.collision('horizontal')
            
            # Vertical
            elif self.knockback_direction == 'up':
                self.direction.y = 0
                self.hitbox_rect.y += -1 * self.vertical_knockback_value * delta_time * 2
                self.collision('vertical')
            elif self.knockback_direction == 'down' and not self.on_surface['floor']:
                self.hitbox_rect.y += 1 * self.vertical_knockback_value * delta_time
                self.collision('vertical')

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
            self.audio_manager.play_with_pitch(self.audio_files['dash'])

    def heal(self):
        self.audio_files['focus_heal'].play()
        self.screen_shake(100, 1)
        self.data.health_regen = False
        self.data.player_health += 3
        self.state = 'idle'
    
    def switch_weapon(self):
        self.audio_files['switch_weapons'].play()
        self.data.actual_weapon += 1

    def use_weapon(self):
        if self.data.actual_weapon == 1 and self.data.string_bar >= 1:
            self.audio_manager.play_with_pitch(self.audio_files['use_weapon'], min_pitch=90, max_pitch=110, volume_change=-3.0)
            self.using_weapon = True
            self.data.string_bar -= 1
        elif self.data.actual_weapon == 2 and self.on_surface['floor'] and self.data.string_bar >= 2:
            self.audio_manager.play_with_pitch(self.audio_files['use_weapon'], min_pitch=90, max_pitch=110, volume_change=-3.0)
            self.using_weapon = True
            self.data.string_bar -= 2

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
                self.dash_progress = self.dash_distance
        
        # Horizontal 
        self.hitbox_rect.x += self.direction.x * self.speed * delta_time
        self.collision('horizontal')

        # Vertical 

        # Gravidade Paredes
        if not self.on_surface['floor'] and any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active and self.data.unlocked_wall_jump:
            self.throw_attack_is_available = True
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
                    self.timers['jump_sound'].activate()
                    self.audio_manager.play_with_pitch(self.audio_files['jump'])

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

        # collisions
        self.on_surface['floor'] = True if floor_rect.collidelist(self.collide_rects) >= 0 or floor_rect.collidelist(self.semi_collide_rects) >= 0 and self.direction.y >= 0 else False
        self.on_surface['right_wall'] = True if right_rect.collidelist(self.collide_rects) >= 0 else False
        self.on_surface['left_wall']  = True if left_rect.collidelist(self.collide_rects) >= 0 else False

        self.platform = None
        sprites = self.collision_sprites.sprites() + self.semi_collision_sprites.sprites()
        for sprite in [sprite for sprite in sprites if hasattr(sprite, 'moving')]:
            if sprite.rect.colliderect(floor_rect):
                self.platform = sprite

        # Evitar que o player fique preso durante o ataque de lançar
        if self.throw_attacking:
            top_left_square = pygame.Rect(self.hitbox_rect.topleft + vector(-2, 0), (2, 2))
            top_right_square = pygame.Rect(self.hitbox_rect.topright, (2, 2))

            if top_right_square.collidelist(self.collide_rects) >= 0 and not self.on_surface['right_wall']:
                self.hitbox_rect.y += 1

            if top_left_square.collidelist(self.collide_rects) >= 0 and not self.on_surface['left_wall']:
                self.hitbox_rect.y += 1
    
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
        check_collision = (
            not self.timers['platform_skip'].active or 
            (self.timers['platform_skip'].active and not self.skippable_platform)
        )

        if check_collision:
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
        if not self.state == 'attack':
            self.frame_index += ANIMATION_SPEED * dt
        else:
            self.frame_index += ANIMATION_SPEED * dt * 3
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
                self.state = 'attack' if not self.vertical_sight == 'up' else 'up_attack'
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
        if self.dashing:
            self.state = 'dashing'
        if self.healing:
            self.state = 'healing'
        if self.timers['invincibility_frames'].active and not self.timers['parry'].active and not self.timers['parry_attack'].active:
            self.state = 'hit'
        if self.timers['parry'].active or self.timers['parry_attack'].active:
            self.state = 'parry' if self.timers['parry'].active else self.state
            self.state = 'parry_attack' if self.timers['parry_attack'].active else self.state
        else:
            self.parrying = False
        if self.throw_attacking or self.spin_attacking:
            self.state = 'throw_attack_animation'
        if self.on_surface['bench']:
            self.state = 'on_bench'

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
        if not self.on_final_animation:
            self.input()
        if not self.throw_attacking and not self.healing and not self.spin_attacking and not self.timers['parry'].active and not self.timers['parry_attack'].active and not self.on_surface['bench']:
            self.move(delta_time)
        self.platform_move(delta_time)
        if self.throw_attacking and not self.on_surface['floor']:
            self.check_contact(1.1)
        else:
            self.check_contact(2)

        # Animação
        self.get_state()
        self.flicker()
        if not self.on_final_animation:
            self.animate(delta_time)