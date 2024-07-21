from settings import *
from sprites import Sprite, AnimatedSprite, MovingSprite, Spike, Item, ParticleEffectSprite
from player import Player
from groups import AllSprites
from debug import debug
from enemies import Tooth, Shell, Pearl
from attack import Neutral_Attack, Throw_Attack

from random import uniform

class Level:
    def __init__(self, tmx_map, level_frames, audio_files, data, switch_screen, current_stage):
        self.display_surface = pygame.display.get_surface() # Inicializa a partir da tela em main
        self.data = data
        self.switch_screen = switch_screen
        self.current_stage = current_stage

        self.during_neutral_attack = False
        self.during_throw_attack = False
        self.player_neutral_attack_sprite = None
        self.player_throw_attack_sprite = None

        # Informações da fase
        self.level_width = tmx_map.width * TILE_SIZE
        self.level_bottom = tmx_map.height * TILE_SIZE
        tmx_level_properties = tmx_map.get_layer_by_name('Data')[0].properties
        if tmx_level_properties['bg']:
            bg_tile = level_frames['bg_tiles'][tmx_level_properties['bg']]
        else:
            bg_tile = None

        # groups 
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

        # Inicialização do grupo de sprites dos inimigos que causam dano
        self.tooth_sprites = pygame.sprite.Group()
        self.shell_sprites = pygame.sprite.Group()
        self.pearl_sprites = pygame.sprite.Group()

        # Inicialização do grupo de sprites dos itens
        self.item_sprites = pygame.sprite.Group()
        self.setup(tmx_map, level_frames, audio_files)

        # Superficie separadas para facilitar o acesso
        self.pearl_surface = level_frames['pearl']
        self.particle_frames = level_frames['particle']
        self.neutral_attack_frames = level_frames['player_neutral_attack']
        self.throw_attack_frames = level_frames['player_throw_attack']

        # Sons
        self.audio_files = audio_files
        self.audio_files['geo'].set_volume(3)

    def setup(self, tmx_map, level_frames, audio_files):
        # Tiles
        for layer in ['BG', 'Terrain', 'FG', 'Platforms']:
            for x, y, surf in tmx_map.get_layer_by_name(layer).tiles():
                groups = [self.all_sprites]
                if layer == 'Terrain': groups.append(self.collision_sprites)
                if layer == 'Platforms': groups.append(self.semi_collision_sprites)
                match layer:
                    case 'BG': z = Z_LAYERS['bg tiles']
                    case 'FG': z = Z_LAYERS['bg tiles']
                    case _: z = Z_LAYERS['main'] # Default
                Sprite((x * TILE_SIZE,y * TILE_SIZE), surf, groups, z)
        
        # Detalhes do background
        for obj in tmx_map.get_layer_by_name('BG details'):
            if obj.name == 'static':
                 Sprite((int(obj.x), int(obj.y)), obj.image, self.all_sprites, z = Z_LAYERS['bg tiles'])
            else:
                AnimatedSprite((int(obj.x), int(obj.y)), level_frames[obj.name], self.all_sprites, Z_LAYERS['bg tiles'])
                if obj.name == 'candle':
                    AnimatedSprite((int(obj.x), int(obj.y)) + vector(-20, -20), level_frames['candle_light'], self.all_sprites, Z_LAYERS['bg tiles'])

        # Player
        for obj in tmx_map.get_layer_by_name('Objects'):
            if obj.name == 'player':
                self.player = Player(
                    pos = (int(obj.x), int(obj.y)), 
                    groups = self.all_sprites, 
                    collision_sprites = self.collision_sprites, 
                    semi_collision_sprites = self.semi_collision_sprites,
                    frames = level_frames['player'],
                    data = self.data,
                    audio_files = audio_files)
            else:
                if obj.name in ('barrel', 'crate'):
                    Sprite((int(obj.x), int(obj.y)), obj.image, (self.all_sprites, self.collision_sprites))
                else:
                    # Frames
                    frames = level_frames[obj.name] if not 'palm' in obj.name else level_frames['palms'][obj.name]
                    if obj.name == 'floor_spike' and obj.properties['inverted']:
                        # Virar o objeto a 180°
                        frames = [pygame.transform.flip(frame, False, True) for frame in frames]

                    # Grupos
                    groups = [self.all_sprites]
                    if obj.name in('palm_small', 'palm_large'): groups.append(self.semi_collision_sprites)
                    if obj.name in('saw', 'floor_spike'): groups.append(self.damage_sprites)

                    # Z index
                    z = Z_LAYERS['main'] if not 'bg' in obj.name else Z_LAYERS['bg details']

                    # Animation speed
                    animation_speed = ANIMATION_SPEED if not 'palm' in obj.name else ANIMATION_SPEED + uniform(-1, 1)

                    # Criar os sprites
                    AnimatedSprite((int(obj.x), int(obj.y)), frames, groups, z, animation_speed)

            if obj.name == 'flag':
                self.level_finish_rect = pygame.FRect((int(obj.x), int(obj.y)), (int(obj.width), int(obj.height)))
              
        # Objetos moveis
        for obj in tmx_map.get_layer_by_name('Moving Objects'):
            if obj.name == 'spike':
                Spike(
                    pos = (int(obj.x) + int(obj.width) / 2, int(obj.y) + int(obj.height) / 2),
                    surface = level_frames['spike'],
                    radius = obj.properties['radius'],
                    speed = obj.properties['speed'],
                    start_angle = obj.properties['start_angle'],
                    end_angle = obj.properties['end_angle'],
                    groups = (self.all_sprites, self.damage_sprites))
                for radius in range(0, obj.properties['radius'], 20):
                    Spike(
                        pos = (int(obj.x) + int(obj.width) / 2, int(obj.y) + int(obj.height) / 2),
                        surface = level_frames['spike_chain'],
                        radius = radius,
                        speed = obj.properties['speed'],
                        start_angle = obj.properties['start_angle'],
                        end_angle = obj.properties['end_angle'],
                        groups = self.all_sprites,
                        z = Z_LAYERS['bg details'])

            else:
                frames = level_frames[obj.name]
                groups = (self.all_sprites, self.semi_collision_sprites) if obj.properties['platform'] else (self.all_sprites, self.damage_sprites)
                if obj.width > obj.height: # Horizontal
                    move_dir = 'x'
                    start_pos = (int(obj.x), int(obj.y) + int(obj.height) / 2)
                    end_pos = (int(obj.x) + int(obj.width), int(obj.y) + int(obj.height) / 2)
                else: # Vertical
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
        for obj in tmx_map.get_layer_by_name('Enemies'):
            if obj.name == 'tooth':
                Tooth((int(obj.x), int(obj.y)), level_frames['tooth'], (self.all_sprites, self.damage_sprites, self.tooth_sprites), self.collision_sprites)
            if obj.name == 'shell':
                Shell(
                    pos = (int(obj.x), int(obj.y)), 
                    frames = level_frames['shell'], 
                    groups = (self.all_sprites, self.collision_sprites, self.shell_sprites), 
                    reverse = obj.properties['reverse'], 
                    player = self.player, 
                    create_pearl = self.create_pearl)
                
        # Itens
        for obj in tmx_map.get_layer_by_name('Items'):
            Item(obj.name, (int(obj.x) + TILE_SIZE / 2, int(obj.y) + TILE_SIZE / 2), level_frames['items'][obj.name], (self.all_sprites, self.item_sprites), self.data)
        
        # Água
        for obj in tmx_map.get_layer_by_name('Water'):
            rows = int(obj.height / TILE_SIZE) 
            cols = int(obj.width / TILE_SIZE) 
            for row in range(rows):
                for col in range(cols):
                    x = int(obj.x) + col * TILE_SIZE
                    y = int(obj.y) + row * TILE_SIZE
                    if row == 0:
                        AnimatedSprite((x,y), level_frames['water_top'], self.all_sprites, Z_LAYERS['water'])
                    else:
                        Sprite((x,y), level_frames['water_body'], self.all_sprites, Z_LAYERS['water'])

    def create_pearl(self, pos, direction):
        Pearl(pos, (self.all_sprites, self.damage_sprites, self.pearl_sprites), self.pearl_surface, direction, 150)
        self.audio_files['pearl'].play()

    def pearl_collision(self):
        for sprite in self.collision_sprites:
            sprite = pygame.sprite.spritecollide(sprite, self.pearl_sprites, True)
            if sprite:
                ParticleEffectSprite((sprite[0].rect.center), self.particle_frames, self.all_sprites)

    def hit_collision(self):
        for sprite in self.damage_sprites:
            if sprite.rect.colliderect(self.player.hitbox_rect):
                if not self.player.timers['invincibility_frames'].active:
                    self.player.get_damage()
                    self.audio_files['damage'].play()
                if hasattr(sprite, 'pearl'):
                    sprite.kill()
                    ParticleEffectSprite((sprite.rect.center), self.particle_frames, self.all_sprites)
                if self.data.player_health <= 0:
                    self.data.player_health = BASE_HEALTH
                    self.switch_screen(int(self.current_stage) + 1)
    
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
                jumping = self.player.jumping
            )
        if not self.player.neutral_attacking:
            self.during_neutral_attack = False
        
        # Ataque lançável
        if self.player.throw_attacking and not self.during_throw_attack:
            self.during_throw_attack = True
            self.player_throw_attack_sprite = Throw_Attack(
                pos = (self.player.hitbox_rect.x, self.player.hitbox_rect.y),
                groups = (self.all_sprites, self.attack_sprites),
                frames = self.throw_attack_frames,
                facing_side = self.player.facing_side,
                vertical_sight = self.player.vertical_sight,
            )
        # Caso o sprite exista e ele deve sumir da tela
        if self.player_throw_attack_sprite and not self.player_throw_attack_sprite.alive():
            self.during_throw_attack = False
            self.player.throw_attacking = False

    def attack_collision(self):
        if self.player.neutral_attacking:
            for target in self.pearl_sprites.sprites() + self.tooth_sprites.sprites() + self.shell_sprites.sprites():
                if target.rect.colliderect(self.player_neutral_attack_sprite.rect):
                    target.get_damage()
                    if not hasattr(target, 'pearl'):
                        target.is_alive()

        if self.player.throw_attacking:
            for target in self.pearl_sprites.sprites() + self.tooth_sprites.sprites() + self.shell_sprites.sprites() + self.collision_sprites.sprites():
                if target.rect.colliderect(self.player_throw_attack_sprite.rect):
                    if hasattr(target, 'is_enemy'):
                        target.get_damage()
                        if not hasattr(target, 'pearl'):
                            target.is_alive()
                    else:
                        self.player_throw_attack_sprite.on_wall = True
                        self.player_throw_attack_sprite.speed = 0

    def throw_attack_movement(self, delta_time):
        self.player.hitbox_rect.x += self.player_throw_attack_sprite.direction * 1000 * delta_time
        self.player.rect.center = self.player.hitbox_rect.center
        self.player.collision('horizontal')
        if self.player.on_surface['right_wall'] or self.player.on_surface['left_wall']:
            self.player_throw_attack_sprite.kill()
            self.player.throw_attacking = False
    
    def check_constraint(self):
        # Método para limitar o jogador dentro da fase específica

        # Limitação à esquerda e à direita
        if self.player.hitbox_rect.left <= 0:
            self.player.hitbox_rect.left = 0

        if self.player.hitbox_rect.right >= self.level_width:
            self.player.hitbox_rect.right = self.level_width

        # Limitação da parte de baixo
        if self.player.hitbox_rect.bottom > self.level_bottom:
            self.switch_screen(int(self.current_stage) + 1)
            self.data.player_health = BASE_HEALTH
        
        # Passou de fase
        if self.player.hitbox_rect.colliderect(self.level_finish_rect):
            self.switch_screen(int(self.current_stage) + 1)
            self.data.player_health = BASE_HEALTH

    def run(self, delta_time):
        self.display_surface.fill('black') # Preenche a tela com a cor preta

        self.all_sprites.update(delta_time) # Atualiza os sprites da tela
        self.pearl_collision()
        self.hit_collision()
        self.item_collision()

        # Ataque do player
        self.player_attack()
        if (self.during_neutral_attack and self.player_neutral_attack_sprite) or (self.during_throw_attack and self.player_throw_attack_sprite):
            if self.during_neutral_attack and self.player_neutral_attack_sprite:
                self.player_neutral_attack_sprite.update_position((self.player.hitbox_rect.x, self.player.hitbox_rect.y))
            elif self.player_throw_attack_sprite.on_wall:
                self.throw_attack_movement(delta_time)
            self.attack_collision()

        # Limitação do mapa e desenho dos sprites
        self.check_constraint()
        self.all_sprites.draw(self.player.hitbox_rect.center, delta_time)