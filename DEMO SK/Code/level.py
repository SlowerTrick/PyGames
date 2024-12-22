from settings import *
from sprites import Sprite, AnimatedSprite, MovingSprite, Spike, Item, ParticleEffectSprite
from timecount import Timer
from player import Player
from groups import AllSprites
from debug import debug
from enemies import Runner, Shell, Breakable_wall, Chest, Pearl, Slime, Fly, Butterfly, Lace
from attack import Neutral_Attack, Throw_Attack, Spin_Attack, Parry_Attack, Knive, Saw
from random import uniform
from os.path import join
from audio import AudioManager

class Level:
    def __init__(self, tmx_map, level_frames, audio_files, data, switch_screen, current_stage, player_spawn):
        # Setup geral
        self.display_surface = pygame.display.get_surface() # Inicializa a partir da tela em main
        self.data = data
        self.switch_screen = switch_screen
        self.audio_manager = AudioManager()

        # Ataques
        self.during_neutral_attack = False
        self.during_throw_attack = False
        self.during_spin_attack = False
        self.player_neutral_attack_sprite = None
        self.player_throw_attack_sprite = None
        self.player_spin_attack_sprite = None
        self.player_parry_attack_sprite = None

        # Informações da fase
        self.level_width = tmx_map.width * TILE_SIZE
        self.level_bottom = tmx_map.height * TILE_SIZE
        tmx_level_properties = tmx_map.get_layer_by_name('Data')[0].properties
        if tmx_level_properties['bg']:
            bg_tile = level_frames['bg_tiles'][tmx_level_properties['bg']]
        else:
            bg_tile = None

        # Caso vc consiga implementar o banco, basta mudar player_spawn para "bench"
        self.current_stage = current_stage
        self.player_spawn = player_spawn
        self.adjacent_stage = {
            'top': tmx_level_properties['next_room_up'], 
            'left': tmx_level_properties['next_room_left'], 
            'right': tmx_level_properties['next_room_right'], 
            'down': tmx_level_properties['next_room_down']
        }

        # Grupos
        self.all_sprites = AllSprites(
            width = tmx_map.width, 
            height = tmx_map.height,
            bg_tile = bg_tile,
            top_limit = tmx_level_properties['top_limit'],
            clouds = {'large': level_frames['cloud_large'], 'small': level_frames['cloud_small']},
            horizon_line = tmx_level_properties['horizon_line']) 
        
        self.collision_sprites = pygame.sprite.Group()
        self.semi_collision_sprites = pygame.sprite.Group()
        self.damage_sprites = pygame.sprite.Group()
        self.attack_sprites = pygame.sprite.Group()
        self.weapon_sprites = pygame.sprite.Group()
        self.bench_sprites = pygame.sprite.Group()

        # Inicialização do grupo de sprites dos inimigos que causam dano
        self.runner_sprites = pygame.sprite.Group()
        self.shell_sprites = pygame.sprite.Group()
        self.pearl_sprites = pygame.sprite.Group()
        self.slime_sprites = pygame.sprite.Group()
        self.fly_sprites = pygame.sprite.Group()
        self.lace_sprites = pygame.sprite.Group()
        self.thorn_sprites = pygame.sprite.Group()
        self.all_enemies = pygame.sprite.Group()

        # Inicialização do grupo de sprites dos itens
        self.item_sprites = pygame.sprite.Group()

        # Superficie separadas para facilitar o acesso
        self.pearl_surface = level_frames['pearl']
        self.particle_frames = level_frames['particle']
        self.neutral_attack_frames = level_frames['player_neutral_attack']
        self.throw_attack_frames = level_frames['player_throw_attack']
        self.spin_attack_frames = level_frames['player_spin_attack']
        self.parry_attack_frames = level_frames['player_parry_attack']
        self.weapon_frames = level_frames['weapons']

        # Sons
        self.audio_files = audio_files
        self.audio_files['geo'].set_volume(3)

        self.setup(tmx_map, level_frames, audio_files)
        self.timers = {
            'loading_time': Timer(50),
            'hit_stop_long': Timer(100),
            'hit_stop_short': Timer(50),
        }
        self.hit_stop_cooldown = Timer(100)

        # Screen effects
        self.fade_alpha = 255  # Nível de opacidade inicial (0-255)
        self.damage_alpha = 0 # Nível de opacidade inicial (0-255)
        # Para tirar, os codigos estão em player_collisions e screen effects
        self.fade_speed = 5   # Velocidade do fade 
        self.damage_fade_speed = 3 # Velocidade do fade de dano

    def setup(self, tmx_map, level_frames, audio_files):
        def get_layer(tmx_map, layer_name):
            try:
                return tmx_map.get_layer_by_name(layer_name)
            except ValueError:
                return None

        # Tiles
        for layer in ['BG', 'Terrain', 'FG', 'Platforms']:
            tile_layer = get_layer(tmx_map, layer)
            if tile_layer:
                for x, y, surf in tile_layer.tiles():
                    groups = [self.all_sprites]
                    if layer == 'Terrain': groups.append(self.collision_sprites)
                    if layer == 'Platforms': groups.append(self.semi_collision_sprites)
                    match layer:
                        case 'BG': z = Z_LAYERS['bg tiles']
                        case 'FG': z = Z_LAYERS['bg tiles']
                        case _: z = Z_LAYERS['main']  # Default
                    Sprite((x * TILE_SIZE, y * TILE_SIZE), surf, groups, z)

        # Detalhes do background
        bg_details_layer = get_layer(tmx_map, 'BG details')
        if bg_details_layer:
            for obj in bg_details_layer:
                if obj.name == 'static':
                    Sprite((int(obj.x), int(obj.y)), obj.image, self.all_sprites, z=Z_LAYERS['bg tiles'])
                else:
                    AnimatedSprite((int(obj.x), int(obj.y)), level_frames[obj.name], self.all_sprites, Z_LAYERS['bg tiles'])
                    if obj.name == 'candle':
                        AnimatedSprite((int(obj.x), int(obj.y)) + vector(-20, -20), level_frames['candle_light'], self.all_sprites, Z_LAYERS['bg tiles'])

        # Player e objetos normais
        objects_layer = get_layer(tmx_map, 'Objects')
        if objects_layer:
            for obj in objects_layer:
                if obj.name == 'player' and obj.properties['spawn'] == self.player_spawn:
                    self.player = Player(
                        pos = (int(obj.x), int(obj.y)),
                        groups = self.all_sprites,
                        collision_sprites = self.collision_sprites,
                        semi_collision_sprites = self.semi_collision_sprites,
                        frames = level_frames['player'],
                        data = self.data,
                        audio_files = audio_files,
                        screen_shake = self.all_sprites.start_shaking)
                else:
                    if obj.name in ('chest'):
                        Chest(
                            pos = (int(obj.x), int(obj.y)), 
                            groups = (self.all_sprites, self.collision_sprites, self.slime_sprites, self.all_enemies), 
                            frames = level_frames['chest'], 
                            item_name = obj.properties['item'], 
                            all_sprites = self.all_sprites, 
                            item_frames = level_frames['items'][obj.properties['item']],
                            item_sprite_group = (self.all_sprites, self.item_sprites),
                            reverse = obj.properties['reverse'],
                            data = self.data,
                        )
                    elif obj.name == 'bench':
                        bench_image = obj.image
                        bench_image = pygame.transform.scale_by(bench_image, (1.2, 1.3))
                        Sprite((int(obj.x), int(obj.y)), bench_image, (self.all_sprites, self.bench_sprites), z = Z_LAYERS['bg details'])
                    else:
                        if obj.name in level_frames and obj.name != 'player':
                            frames = level_frames[obj.name] if not 'palm' in obj.name else level_frames['palms'][obj.name]
                            if obj.name == 'floor_spike':
                                frames = level_frames['floor_spike'][obj.properties['direction']]

                            groups = [self.all_sprites]
                            if obj.name in ('palm_small', 'palm_large'): groups.append(self.semi_collision_sprites)
                            if obj.name in ('saw'): groups.append(self.damage_sprites)
                            if obj.name in ('floor_spike'): 
                                groups.append(self.damage_sprites)
                                groups.append(self.thorn_sprites)

                            z = Z_LAYERS['main'] if not 'bg' in obj.name else Z_LAYERS['bg details']

                            animation_speed = ANIMATION_SPEED if not 'palm' in obj.name else ANIMATION_SPEED + uniform(-1, 1)

                            AnimatedSprite((int(obj.x), int(obj.y)), frames, groups, z, animation_speed)

                if obj.name == 'flag':
                    self.level_finish_rect = pygame.FRect((int(obj.x), int(obj.y)), (int(obj.width), int(obj.height)))

        # Objetos moveis / Objetos com dano
        moving_objects_layer = get_layer(tmx_map, 'Moving Objects')
        if moving_objects_layer:
            for obj in moving_objects_layer:
                if obj.name == 'spike':
                    Spike(
                        pos=(int(obj.x) + int(obj.width) / 2, int(obj.y) + int(obj.height) / 2),
                        surface=level_frames['spike'],
                        radius=obj.properties['radius'],
                        speed=obj.properties['speed'],
                        start_angle=obj.properties['start_angle'],
                        end_angle=obj.properties['end_angle'],
                        groups=(self.all_sprites, self.damage_sprites))
                    for radius in range(0, obj.properties['radius'], 20):
                        Spike(
                            pos=(int(obj.x) + int(obj.width) / 2, int(obj.y) + int(obj.height) / 2),
                            surface=level_frames['spike_chain'],
                            radius=radius,
                            speed=obj.properties['speed'],
                            start_angle=obj.properties['start_angle'],
                            end_angle=obj.properties['end_angle'],
                            groups=self.all_sprites,
                            z=Z_LAYERS['bg details'])

                else:
                    if obj.name in level_frames:
                        frames = level_frames[obj.name]
                        groups = (self.all_sprites, self.semi_collision_sprites) if obj.properties['platform'] else (self.all_sprites, self.damage_sprites)
                        if obj.width > obj.height:  # Horizontal
                            move_dir = 'x'
                            start_pos = (int(obj.x), int(obj.y) + int(obj.height) / 2)
                            end_pos = (int(obj.x) + int(obj.width), int(obj.y) + int(obj.height) / 2)
                        else:  # Vertical
                            move_dir = 'y'
                            start_pos = (int(obj.x) + int(obj.width) / 2, int(obj.y))
                            end_pos = (int(obj.x) + int(obj.width) / 2, int(obj.y) + int(obj.height))
                        speed = obj.properties['speed']
                        MovingSprite(frames, groups, start_pos, end_pos, move_dir, speed, obj.properties['flip'])

                        if obj.name == 'saw':
                            if move_dir == 'x':
                                y = start_pos[1] - level_frames['saw_chain'].get_height() / 2
                                left_side, right_side = int(start_pos[0]), int(end_pos[0])
                                for x in range(left_side, right_side, 20):
                                    Sprite((x, y), level_frames['saw_chain'], (self.all_sprites), Z_LAYERS['bg details'])
                            else:
                                x = start_pos[0] - level_frames['saw_chain'].get_width() / 2
                                top, bottom = int(start_pos[1]), int(end_pos[1])
                                for y in range(top, bottom, 20):
                                    Sprite((x, y), level_frames['saw_chain'], (self.all_sprites), Z_LAYERS['bg details'])

        # Inimigos
        enemies_layer = get_layer(tmx_map, 'Enemies')
        if enemies_layer:
            for obj in enemies_layer:
                if obj.name == 'tooth':
                    Runner(
                        pos = (int(obj.x), int(obj.y)), 
                        frames = level_frames['runner'], 
                        groups = (self.all_sprites, self.damage_sprites, self.runner_sprites, self.all_enemies), 
                        collision_sprites = self.collision_sprites)
                    
                if obj.name == 'shell':
                    Shell(
                        pos = (int(obj.x), int(obj.y)),
                        frames = level_frames['shell'],
                        groups = (self.all_sprites, self.collision_sprites, self.shell_sprites, self.all_enemies),
                        reverse = obj.properties['reverse'],
                        player = self.player,
                        create_pearl = self.create_pearl)
            
                if obj.name == 'breakable_wall':
                    Breakable_wall(
                        pos = (int(obj.x), int(obj.y)),
                        surf = level_frames['breakable_wall'],
                        groups = (self.all_sprites, self.collision_sprites, self.runner_sprites, self.all_enemies),
                    )
    
                if obj.name == 'slime':
                    Slime(
                        pos = (int(obj.x), int(obj.y)),
                        frames = level_frames['slime'],
                        groups = (self.all_sprites, self.damage_sprites, self.slime_sprites, self.all_enemies),
                        player = self.player,
                        collision_sprites = self.collision_sprites)
                
                if obj.name == 'fly':
                    Fly(
                        pos = (int(obj.x), int(obj.y)),
                        frames = level_frames['fly'],
                        groups = (self.all_sprites, self.damage_sprites, self.fly_sprites, self.all_enemies),
                        player = self.player,
                        collision_sprites = self.collision_sprites)

                if obj.name == 'butterfly':
                    Butterfly(
                        pos = (int(obj.x), int(obj.y)), 
                        frames = level_frames['butterfly'], 
                        groups = (self.all_sprites),
                        player = self.player)

                if obj.name == 'lace':
                    self.lace = Lace(
                        pos = (int(obj.x), int(obj.y)),
                        frames = level_frames['lace'],
                        groups = (self.all_sprites, self.damage_sprites, self.lace_sprites, self.all_enemies),
                        player = self.player,
                        collision_sprites = self.collision_sprites)
                    
        # Espinhos Normais
        thorns_layer = get_layer(tmx_map, 'Thorns')
        if thorns_layer:
            for x, y, surf in thorns_layer.tiles():
                frames = level_frames['floor_spike']['up']
                groups = [self.all_sprites, self.damage_sprites, self.thorn_sprites]
                z = Z_LAYERS['main']
                AnimatedSprite((x * TILE_SIZE, (y+0.8) * TILE_SIZE), frames, groups, z, ANIMATION_SPEED)
        
        # Espinhos Reversos
        reverse_thorns_layer = get_layer(tmx_map, 'Reverse Thorns')
        if reverse_thorns_layer:
            for x, y, surf in reverse_thorns_layer.tiles():
                frames = level_frames['floor_spike']['down']
                groups = [self.all_sprites, self.damage_sprites, self.thorn_sprites]
                z = Z_LAYERS['main']
                AnimatedSprite((x * TILE_SIZE, (y) * TILE_SIZE), frames, groups, z, ANIMATION_SPEED)

        # Itens
        items_layer = get_layer(tmx_map, 'Items')
        if items_layer:
            for obj in items_layer:
                if obj.name in level_frames['items']:
                    Item(obj.name, (int(obj.x) + TILE_SIZE / 2, int(obj.y) + TILE_SIZE / 2), level_frames['items'][obj.name], (self.all_sprites, self.item_sprites), self.data)

        # Água
        water_layer = get_layer(tmx_map, 'Water')
        if water_layer:
            for obj in water_layer:
                rows = int(obj.height / TILE_SIZE)
                cols = int(obj.width / TILE_SIZE)
                for row in range(rows):
                    for col in range(cols):
                        x = int(obj.x) + col * TILE_SIZE
                        y = int(obj.y) + row * TILE_SIZE
                        if row == 0:
                            AnimatedSprite((x, y), level_frames['water_top'], self.all_sprites, Z_LAYERS['water'])
                        else:
                            Sprite((x, y), level_frames['water_body'], self.all_sprites, Z_LAYERS['water'])
    
    def update_timers(self):
        # Atualiza todos os temporizadores estabelicidos
        for timer in self.timers.values():
            timer.update()

    def create_pearl(self, pos, direction):
        Pearl(pos, (self.all_sprites, self.damage_sprites, self.pearl_sprites), self.pearl_surface, direction, 350)
        self.audio_files['pearl'].play()

    def pearl_collision(self):
        if self.pearl_sprites:
            for sprite in self.collision_sprites:
                sprite = pygame.sprite.spritecollide(sprite, self.pearl_sprites, True)
                if sprite:
                    ParticleEffectSprite((sprite[0].rect.center), self.particle_frames, self.all_sprites)

    def player_collisions(self, dt):
        # Hit no jogador
        for sprite in self.damage_sprites:
            if sprite.rect.colliderect(self.player.hitbox_rect):
                if hasattr(sprite, 'is_dead'):
                    if getattr(sprite, 'is_dead') == True:
                        continue
                if not self.player.timers['invincibility_frames'].active:
                    if (not self.player.timers['parry'].active and not self.player.timers['parry_attack'].active) or sprite in self.thorn_sprites:
                        self.all_sprites.start_shaking(500, 2)
                        self.timers['hit_stop_long'].activate()
                        self.damage_alpha = 80
                        self.player.get_damage()
                        self.audio_files['damage'].play()

                # Cria o ataque parry  
                if self.player.state == 'parry' and hasattr(sprite, 'is_enemy'):
                    self.player.timers['parry'].deactivate()
                    self.player.timers['parry_attack'].activate()
                    self.player.parrying = True
                    self.player_parry_attack_sprite = Parry_Attack(
                    pos = (self.player.hitbox_rect.centerx, self.player.hitbox_rect.centery),
                    groups = (self.all_sprites, self.attack_sprites),
                    frames = self.parry_attack_frames,
                    facing_side = self.player.facing_side,
                    audio_files = self.audio_files
                )
                    
                if hasattr(sprite, 'pearl'):
                    sprite.kill()
                    ParticleEffectSprite((sprite.rect.center), self.particle_frames, self.all_sprites)
                if self.data.player_health <= 0:
                    self.data.player_health = BASE_HEALTH
                    self.data.string_bar = 0
                    self.switch_screen(int(self.current_stage), self.player_spawn)
        
        # Banco
        for sprite in self.bench_sprites:
            if sprite.rect.colliderect(self.player.hitbox_rect) and self.player.vertical_sight == 'up':
                self.player.on_surface['bench'] = True
                self.player.timers['sitting_down'].activate()
            
            if self.player.on_surface['bench']:
                target_center = (sprite.rect.centerx, sprite.rect.centery - 15)
                
                if self.player.hitbox_rect.center != target_center:
                    distance_x = target_center[0] - self.player.hitbox_rect.centerx
                    distance_y = target_center[1] - self.player.hitbox_rect.centery

                    speed_x = max(1, min(300 * dt, abs(distance_x)))
                    speed_y = max(1, min(300 * dt, abs(distance_y)))

                    # Movimenta o jogador no eixo X e Y
                    self.player.hitbox_rect.centerx += speed_x if distance_x > 0 else -speed_x
                    self.player.hitbox_rect.centery += speed_y if distance_y > 0 else -speed_y

                    # Mantém o rect do jogador alinhado com a hitbox
                    self.player.rect.center = self.player.hitbox_rect.center

                    # Verifica se o jogador está próximo o suficiente do centro ajustado
                    if abs(distance_x) < speed_x and abs(distance_y) < speed_y:
                        self.data.player_health = BASE_HEALTH
                        self.player.hitbox_rect.center = target_center
                        self.player.rect.center = target_center
                        self.audio_files['bench_rest'].play()
                        self.player.timers['sitting_down'].activate()
                        self.player.dashing = False
    
    def item_collision(self):
        if self.item_sprites:
            item_sprites = pygame.sprite.spritecollide(self.player, self.item_sprites, True)
            if item_sprites:
                item_sprites[0].activate()
                ParticleEffectSprite((item_sprites[0].rect.center), self.particle_frames, self.all_sprites)
                self.audio_files['geo'].play()

    def player_attack(self):
        # Ataque neutro
        if self.player.neutral_attacking and not self.during_neutral_attack:
            self.during_neutral_attack = True
            self.player_neutral_attack_sprite = Neutral_Attack(
                pos = (self.player.hitbox_rect.x, self.player.hitbox_rect.y),
                groups = (self.all_sprites, self.attack_sprites),
                frames = self.neutral_attack_frames,
                facing_side = self.player.facing_side,
                vertical_sight = self.player.vertical_sight,
                jumping = not self.player.on_surface['floor']
            )
        if not self.player.neutral_attacking:
            self.during_neutral_attack = False
        
        # Ataque lançável
        if self.player.throw_attacking and not self.during_throw_attack:
            self.during_throw_attack = True
            self.player_throw_attack_sprite = Throw_Attack(
                pos = (self.player.hitbox_rect.centerx, self.player.hitbox_rect.centery),
                groups = (self.all_sprites, self.attack_sprites),
                frames = self.throw_attack_frames,
                facing_side = self.player.facing_side,
                vertical_sight = self.player.vertical_sight,
                audio_files = self.audio_files
            )
        if self.player_throw_attack_sprite and not self.player_throw_attack_sprite.alive():
            self.during_throw_attack = False
            self.player.throw_attacking = False

        # Ataque giratório
        if self.player.spin_attacking and not self.during_spin_attack:
            self.during_spin_attack = True
            self.player_spin_attack_sprite = Spin_Attack(
                pos = (self.player.hitbox_rect.x, self.player.hitbox_rect.y),
                groups = (self.all_sprites, self.attack_sprites),
                frames = self.spin_attack_frames,
                audio_files = self.audio_files
            )
        if self.player_spin_attack_sprite and not self.player_spin_attack_sprite.alive():
            self.during_spin_attack = False
            self.player.spin_attacking = False
            self.player.spin_attacking = False

        # Equipamentos
        if self.player.using_weapon:
            self.player.using_weapon = False
            if self.data.actual_weapon == 1:
                Knive(
                    pos = (self.player.hitbox_rect.x, self.player.hitbox_rect.y),
                    groups = (self.all_sprites, self.attack_sprites, self.weapon_sprites),
                    frames = self.weapon_frames,
                    facing_side = self.player.facing_side,
                    speed = 900
                )
            elif self.data.actual_weapon == 2: 
                Saw(
                    pos = (self.player.hitbox_rect.x, self.player.hitbox_rect.y),
                    groups = (self.all_sprites, self.attack_sprites, self.weapon_sprites),
                    frames = self.weapon_frames,
                    facing_side = self.player.facing_side,
                    speed = 450,
                    collision_sprites = self.collision_sprites,
                    particle_frames = self.particle_frames,
                    all_sprites = self.all_sprites
                )

    def attack_collision(self):
        if self.player.neutral_attacking:
            for target in self.all_enemies.sprites() + self.damage_sprites.sprites():
                if target.rect.colliderect(self.player_neutral_attack_sprite.rect):
                    self.player.dash_is_available = True
                    is_enemy = hasattr(target, 'is_enemy')
                    is_pearl = hasattr(target, 'pearl')
                    
                    if is_enemy and not is_pearl:
                        if not target.hit_timer.active:
                            self.audio_manager.play_with_pitch(join('..', 'audio', 'enemy_damage.wav'), volume_change=-2.0)
                            if not self.timers['hit_stop_short'].active and not self.hit_stop_cooldown.active:
                                self.timers['hit_stop_short'].activate()
                                self.hit_stop_cooldown.activate()
                            self.player_neutral_attack_sprite.frame_index = 1
                            self.data.string_bar += 1
                        handle_knockback = not self.player.timers['hit_knockback'].active and not target.hit_timer.active
                    else:
                        handle_knockback = not self.player.timers['hit_knockback'].active

                    if handle_knockback:
                        if self.player_neutral_attack_sprite.facing_side in ['right', 'left']:
                            self.player.knockback_direction = 'left' if self.player_neutral_attack_sprite.facing_side == 'right' else 'right'
                            if hasattr(target, 'knockback_direction'):
                                target.knockback_direction = 'left' if self.player.knockback_direction == 'right' else 'right'
                                target.during_knockback.activate()
                        else:
                            self.player.knockback_direction = 'up' if self.player_neutral_attack_sprite.facing_side == 'down' else 'down'
                            if hasattr(target, 'knockback_direction'):
                                target.knockback_direction = 'up' if self.player.knockback_direction == 'down' else 'down'
                                target.during_knockback.activate()

                        if target not in self.thorn_sprites:
                            self.player.timers['hit_knockback'].activate()
                        
                        if not is_enemy:
                            self.player.dash_is_available = True
                        else:
                            target.get_damage()
                            if not is_pearl:
                                target.is_alive()

        if self.player.throw_attacking:
            for target in self.all_enemies.sprites() + self.collision_sprites.sprites():
                if target.rect.colliderect(self.player_throw_attack_sprite.rect):
                    is_pearl = hasattr(target, 'pearl')
                    if hasattr(target, 'is_enemy'):
                        if not target.hit_timer.active and not is_pearl:
                            self.audio_manager.play_with_pitch(join('..', 'audio', 'enemy_damage.wav'), volume_change=-2.0)
                            if not self.timers['hit_stop_short'].active:
                                self.timers['hit_stop_short'].activate()
                        target.get_damage()
                        if not is_pearl:
                            target.is_alive()
                    else:
                        self.player_throw_attack_sprite.on_wall = True
                        self.player_throw_attack_sprite.speed = 0

        if self.player.spin_attacking:
            for target in self.all_enemies:
                if target.rect.colliderect(self.player_spin_attack_sprite.rect):
                    is_enemy = hasattr(target, 'is_enemy')
                    is_pearl = hasattr(target, 'pearl')
                    
                    if is_enemy and not is_pearl:
                        if not target.hit_timer.active:
                            self.audio_manager.play_with_pitch(join('..', 'audio', 'enemy_damage.wav'), volume_change=-2.0)
                            if not self.timers['hit_stop_short'].active:
                                self.timers['hit_stop_short'].activate()
                        target.get_damage()
                        target.is_alive()

        if self.player.parrying:
            for target in self.all_enemies:
                if target.rect.colliderect(self.player_parry_attack_sprite.rect):
                    is_enemy = hasattr(target, 'is_enemy')
                    is_pearl = hasattr(target, 'pearl')

                    if hasattr(target, 'knockback_direction'):
                        # Calcula o centro do player e do inimigo
                        player_center = self.player_parry_attack_sprite.rect.centerx
                        target_center = target.rect.centerx

                        # Define a direção do knockback com base na posição relativa
                        if target_center <= player_center:
                            target.knockback_direction = 'left'
                        else:
                            target.knockback_direction = 'right'

                        target.during_knockback.activate()
                    if is_enemy:
                        if not target.hit_timer.active and not is_pearl:
                                self.audio_manager.play_with_pitch(join('..', 'audio', 'enemy_damage.wav'), volume_change=-2.0)
                                if not self.timers['hit_stop_short'].active:
                                    self.timers['hit_stop_short'].activate()
                        target.get_damage()
                        if not is_pearl:
                            target.is_alive()

        if self.weapon_sprites:
            for sprite in self.collision_sprites:
                collided_sprites = pygame.sprite.spritecollide(sprite, self.weapon_sprites, False)
                if collided_sprites:
                    for weapon in collided_sprites:
                        if hasattr(weapon, 'is_knive'):
                            ParticleEffectSprite((weapon.rect.center), self.particle_frames, self.all_sprites)
                            weapon.kill()
            for target in self.all_enemies:
                collided_sprites = pygame.sprite.spritecollide(target, self.weapon_sprites, False)
                if collided_sprites:
                    for weapon in collided_sprites:
                        is_enemy = hasattr(target, 'is_enemy')
                        is_pearl = hasattr(target, 'pearl')
                        
                        if is_enemy and not is_pearl:
                            if not target.hit_timer.active:
                                self.audio_manager.play_with_pitch(join('..', 'audio', 'enemy_damage.wav'), volume_change=-2.0)
                                if not self.timers['hit_stop_short'].active:
                                    self.timers['hit_stop_short'].activate()
                            target.get_damage()
                            target.is_alive()
                        
                        if hasattr(weapon, 'is_saw'):
                            weapon.speed = 0
                        elif hasattr(weapon, 'is_knive'):
                            ParticleEffectSprite((weapon.rect.center), self.particle_frames, self.all_sprites)
                            weapon.kill()

    def attack_logic(self, delta_time):
        if (self.during_neutral_attack and self.player_neutral_attack_sprite) or (self.during_throw_attack and self.player_throw_attack_sprite) or (self.during_spin_attack and self.player_spin_attack_sprite) or self.player.parrying or self.weapon_sprites:
            if self.during_neutral_attack and self.player_neutral_attack_sprite:
                self.player_neutral_attack_sprite.update_position((self.player.hitbox_rect.x, self.player.hitbox_rect.y))
                """ if self.player_neutral_attack_sprite.facing_side in {'right', 'left'} and not self.player_neutral_attack_sprite.knockback_applied:
                    self.player_neutral_attack_sprite.knockback_applied = True
                    self.player.knockback_direction = 'right' if self.player_neutral_attack_sprite.facing_side == 'right' else 'left'
                    self.player.timers['attack_knockback'].activate() """
                
            elif self.during_throw_attack and self.player_throw_attack_sprite.on_wall:
                self.throw_attack_movement(delta_time)
            self.attack_collision()

    def throw_attack_movement(self, delta_time):
        self.player.hitbox_rect.x += self.player_throw_attack_sprite.direction * 1000 * delta_time
        self.player.rect.center = self.player.hitbox_rect.center
        self.player.collision('horizontal')
        if self.player.on_surface['right_wall'] or self.player.on_surface['left_wall']:
            self.audio_files['catch'].play()
            self.player_throw_attack_sprite.kill()
            self.player.throw_attacking = False
    
    def throw_attack_rope(self):
        if self.during_throw_attack:
            attack_pos = ((self.player_throw_attack_sprite.rect.centerx + self.all_sprites.offset.x, self.player_throw_attack_sprite.rect.centery + self.all_sprites.offset.y))
            player_pos =((self.player.rect.centerx + self.all_sprites.offset.x, self.player.rect.centery + 10 + self.all_sprites.offset.y))
            self.player_throw_attack_sprite.draw_rope(self.display_surface, player_pos, attack_pos)
        
    def check_constraint(self):
        # Metodo para limitar o jogador na tela e mudar a tela
        bottom_limit = self.level_bottom + 200
        top_limit = 0
        right_limit = self.level_width
        left_limit = 0
        # Logica para mudar a fase e posicionar o jogador na posição correta
        if self.player.hitbox_rect.top >= bottom_limit:
            self.switch_screen(int(self.adjacent_stage['down']), 'top')
        if self.player.hitbox_rect.bottom <= top_limit:
            self.switch_screen(int(self.adjacent_stage['top']), 'down')
        elif self.player.hitbox_rect.left >= right_limit:
            self.switch_screen(int(self.adjacent_stage['right']), 'left')
        elif self.player.hitbox_rect.right <= left_limit:
            self.switch_screen(int(self.adjacent_stage['left']), 'right')

    def screen_effects(self):
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(self.display_surface.get_size())
            fade_surface.fill((0, 0, 0))  # Preencher com preto
            fade_surface.set_alpha(self.fade_alpha)  # Definir opacidade
            self.display_surface.blit(fade_surface, (0, 0))  # Aplicar o fade na tela
            self.fade_alpha -= self.fade_speed  # Reduzir opacidade gradualmente
            if self.fade_alpha < 0:
                self.fade_alpha = 0  # Garantir que a opacidade não fique negativa
        if self.damage_alpha > 0:
            damage_surface = pygame.Surface(self.display_surface.get_size())
            damage_surface.fill((10, 10, 10))  # Preencher com preto
            damage_surface.set_alpha(self.damage_alpha)  # Definir opacidade
            self.display_surface.blit(damage_surface, (0, 0))  # Aplicar o fade na tela
            self.damage_alpha -= self.damage_fade_speed  # Reduzir opacidade gradualmente
            if self.damage_alpha < 0:
                self.damage_alpha = 0  # Garantir que a opacidade não fique negativa

    def run(self, delta_time):
        self.update_timers()
        if all(not timer.active for timer in self.timers.values()):
            self.display_surface.fill('black')  # Preenche a tela com a cor preta
            self.all_sprites.update(delta_time)  # Atualiza os sprites da tela
            self.pearl_collision()
            self.player_collisions(delta_time)
            self.item_collision()

            # Ataque do player
            self.player_attack()                  
            self.attack_logic(delta_time)
            self.hit_stop_cooldown.update()

            # Limitação do mapa e desenho dos sprites
            self.check_constraint()
            self.all_sprites.draw(self.player.hitbox_rect.center, delta_time)

            # Desenhar a linha caso exista
            self.throw_attack_rope()

            # Aplicar dos efeitos na tela
            self.screen_effects()