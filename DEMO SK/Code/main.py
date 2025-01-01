from settings import *
from level import Level
from pytmx.util_pygame import load_pygame
from os.path import join
from timecount import Timer
from support import *
from data import Data
from ui import UI
from menu import Menu, Final_screen

class Game:
    def __init__(self):
        pygame.init() # Inicialização do pygame
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN) # Tela
        pygame.display.set_caption('DEMO SilkSong') # Nome do jogo
        self.clock = pygame.time.Clock() # FPS
        self.import_assets()

        # Carregamento das informações do jogo
        self.ui = UI(self.font, self.ui_frames)
        self.data = Data(self.ui)
        self.menu = Menu(self.display_surface, self.font, self.audio_files['ui_button'])
        self.final_screen_menu = Final_screen(self.display_surface, self.font, self.audio_files['ui_button'])
        self.state = "game"
        self.should_show_fps = False

        # Level
        self.start_stage = 9 # 8 para lace
        self.last_bench = 0
        self.player_spawn = 'left'
        self.current_stage = Level(self.tmx_maps[self.start_stage], self.level_frames, self.audio_files, self.data, self.switch_screen, self.start_stage, self.player_spawn, self.last_bench)
        self.current_stage.timers['loading_time'].activate()

        # Musicas
        self.music_channel = pygame.mixer.Channel(1)
        self.actual_bg_music = 'main'
        self.music_channel.play(self.audio_files['main_ost'], loops=-1)

        # Inicializando os joysticks
        self.joysticks = []
        self.controller_type = None  # Será 'Xbox 360' ou 'PS4' ou 'None'

        # Detectando os joysticks conectados
        self.init_joysticks()

        # Animação final    
        self.final_animation_timer = Timer(6000)
        self.slow_motion_active = False
        self.slow_motion_factor = 1.0  # Fator padrão (1.0 = normal, menor que 1 = mais lento)
        self.final_screen_ended = False

    def import_assets(self):
        # Icone do jogo
        icon = pygame.image.load('../graphics/icon/chibi.jpg') # Icone do jogo
        pygame.display.set_icon(icon)

        # Mapas
        self.tmx_maps = {
            0: load_pygame(join('..', 'data', 'levels', '0.tmx')),
            1: load_pygame(join('..', 'data', 'levels', '1.tmx')),
            2: load_pygame(join('..', 'data', 'levels', '2.tmx')),
            3: load_pygame(join('..', 'data', 'levels', '3.tmx')),
            4: load_pygame(join('..', 'data', 'levels', '4.tmx')),
            5: load_pygame(join('..', 'data', 'levels', '5.tmx')),
            6: load_pygame(join('..', 'data', 'levels', '6.tmx')),
            7: load_pygame(join('..', 'data', 'levels', '7.tmx')),
            8: load_pygame(join('..', 'data', 'levels', '8.tmx')),
            9: load_pygame(join('..', 'data', 'levels', '9.tmx')),
        }

        self.level_frames = {
            # Adição dos sprites animados
            'saw': import_folder('..', 'graphics', 'enemies', 'saw', 'animation'),
            'floor_spike': import_sub_folders('..', 'graphics','enemies', 'floor_spikes'),
            'chest': import_folder('..', 'graphics', 'level', 'chest'),
            'player': import_sub_folders('..', 'graphics', 'player'),
            'saw_chain': import_image('..',  'graphics', 'enemies', 'saw', 'saw_chain'),
            'helicopter': import_folder('..', 'graphics', 'level', 'helicopter'),
            'spike': import_image('..',  'graphics', 'enemies', 'spike_ball', 'Spiked Ball'),
            'spike_chain': import_image('..',  'graphics', 'enemies', 'spike_ball', 'spiked_chain'),
            'runner': import_folder('..', 'graphics', 'enemies', 'runner', 'run'),
            'gulka': import_sub_folders('..', 'graphics', 'enemies', 'gulka'),
            'fool_eater': import_sub_folders('..', 'graphics', 'enemies', 'fool_eater'),
            'breakable_wall': import_image('..',  'graphics', 'enemies', 'breakable_wall', 'wall'),
            'slime': import_sub_folders('..', 'graphics', 'enemies', 'slime'),
            'butterfly': import_folder('..', 'graphics', 'enemies', 'butterfly'),
            'lace': import_sub_folders('..', 'graphics', 'enemies', 'lace'),
            'fly': import_sub_folders('..', 'graphics', 'enemies', 'fly'),
            'ranged_fly': import_sub_folders('..', 'graphics', 'enemies', 'ranged_fly'),
            'pearl': import_image('..',  'graphics', 'enemies', 'bullets', 'pearl'),
            'items': import_sub_folders('..', 'graphics', 'items'),
            'kurisu': import_image('..',  'graphics', 'icon', 'chibi'),
            'particle': import_folder('..', 'graphics', 'effects', 'particle'),
            'water_top': import_folder('..', 'graphics', 'level', 'water', 'top'),
            'water_body': import_image('..', 'graphics', 'level', 'water', 'body'),
            'player_neutral_attack': import_sub_folders('..', 'graphics', 'player', 'attack_animation'),
            'player_throw_attack': import_image('..', 'graphics', 'player', 'throw_attack', '0'),
            'player_spin_attack': import_folder('..', 'graphics', 'player', 'spin_attack'),
            'player_parry_attack': import_folder('..', 'graphics', 'player', 'parry_attack_animation'),
            'bench': import_image('..',  'graphics', 'level', 'bench', 'bench'),
            'weapons': import_sub_folders('..', 'graphics', 'ui', 'weapons'),
            'door': import_folder('..', 'graphics', 'objects', 'door'),
        }
        self.font = pygame.font.Font(join('..', 'graphics', 'ui', 'SuperPixel.ttf'), 40)

        self.ui_frames = {
            'heart': import_folder('..', 'graphics', 'ui', 'heart'), 
            'heartless': import_image('..', 'graphics', 'ui', 'heartless', '0'), 
            'coin':import_image('..', 'graphics', 'ui', 'coin'),
            'ui_bar': import_folder('..', 'graphics', 'ui', 'bar'), 
            'string_bar': import_folder('..', 'graphics', 'ui', 'string'), 
            'weapons': import_sub_folders('..', 'graphics', 'ui', 'weapons'), 
        }

        self.audio_files = {
            'geo': pygame.mixer.Sound(join('..', 'audio', 'geo_collect.wav')),
            'neutral_attack': pygame.mixer.Sound(join('..', 'audio', 'hornet_sword.wav')),
            'jump': pygame.mixer.Sound(join('..', 'audio', 'hornet_jump.wav')), 
            'damage': pygame.mixer.Sound(join('..', 'audio', 'hero_damage.wav')),
            'pearl': pygame.mixer.Sound(join('..', 'audio', 'pearl.wav')),
            'wall_jump': pygame.mixer.Sound(join('..', 'audio', 'hero_mantis_claw.wav')),
            'dash': pygame.mixer.Sound(join('..', 'audio', 'hero_dash.wav')),
            'throw': pygame.mixer.Sound(join('..', 'audio', 'hornet_needle_thow.wav')),
            'catch': pygame.mixer.Sound(join('..', 'audio', 'hornet_needle_catch.wav')),
            'focus_heal': pygame.mixer.Sound(join('..', 'audio', 'focus_health_heal.wav')),
            'focus_charge': pygame.mixer.Sound(join('..', 'audio', 'focus_health_charging.wav')),
            'bench_rest': pygame.mixer.Sound(join('..', 'audio', 'bench_rest.wav')),
            'parry_prepare': pygame.mixer.Sound(join('..', 'audio', 'hornet_parry_prepare.wav')),
            'parry': pygame.mixer.Sound(join('..', 'audio', 'hornet_parry.wav')),
            'enemy_damage': pygame.mixer.Sound(join('..', 'audio', 'enemy_damage.wav')),
            'switch_weapons': pygame.mixer.Sound(join('..', 'audio', 'switch_weapons.wav')),
            'door_open': pygame.mixer.Sound(join('..', 'audio', 'door_open.wav')),
            'door_close': pygame.mixer.Sound(join('..', 'audio', 'door_close.wav')),
            'special_item_loop': pygame.mixer.Sound(join('..', 'audio', 'special_item_loop.wav')),
            'special_item_pickup': pygame.mixer.Sound(join('..', 'audio', 'special_item_pickup.wav')),
            'chest_open': pygame.mixer.Sound(join('..', 'audio', 'chest_open.wav')),
            'breakable_wall_hit': pygame.mixer.Sound(join('..', 'audio', 'breakable_wall_hit.wav')),
            'ui_button': pygame.mixer.Sound(join('..', 'audio', 'ui_button_confirm.ogg')),
            'main_ost': pygame.mixer.Sound(join('..', 'audio', 'main_ost.ogg')),
            'lace_ost': pygame.mixer.Sound(join('..', 'audio', 'lace_ost.ogg')),
            'ending_ost': pygame.mixer.Sound(join('..', 'audio', 'ending_ost.ogg')),
        }
        self.audio_files['ending_ost'].set_volume(0.5)
        self.audio_files['main_ost'].set_volume(0.6)

    def init_joysticks(self):
        joystick_count = pygame.joystick.get_count()

        if joystick_count > 0:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                self.joysticks.append(joystick)

            # Identificar tipo de controle
            if self.joysticks[0].get_name().lower().find("xbox") != -1:
                self.controller_type = 'Xbox 360'
            elif self.joysticks[0].get_name().lower().find("ps4") != -1:
                self.controller_type = 'PS4'
            else:
                self.controller_type = 'Unknown'

    def switch_screen(self, target, player_spawn, last_bench):
        if target >= len(self.tmx_maps):
            target = 0
        self.last_bench = last_bench
        self.current_stage = Level(self.tmx_maps[target], self.level_frames, self.audio_files, self.data, self.switch_screen, target, player_spawn, self.last_bench)
        self.current_stage.timers['loading_time'].activate()

    def show_fps(self):
        if self.should_show_fps:
            fps = self.clock.get_fps()
            font = pygame.font.SysFont(None, 24)
            fps_text = font.render(f"FPS: {int(fps)}", True, pygame.Color('white'))
            self.display_surface.blit(fps_text, (10, 10))

    def detect_pause_button(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
        elif event.type == pygame.JOYBUTTONDOWN: 
            for joystick in self.joysticks:
                if self.controller_type == 'Xbox 360':
                    if joystick.get_button(7):
                        return True
                elif self.controller_type == 'PS4':
                    if joystick.get_button(9):
                        return True
        return False
    
    def set_slow_motion(self, factor):
        # Ativa o slow motion com o fator especificado (1.0 = normal, <1 = lento)
        if factor < 1.0:  # Slow motion
            self.slow_motion_active = True
            self.slow_motion_factor = factor
        else:  # Voltar ao normal
            self.slow_motion_active = False
            self.slow_motion_factor = 1.0

    def handle_music(self, next_music=None, volume=-1):
        if self.actual_bg_music != next_music and next_music != None:
            # Pausar a música atual, se estiver tocando
            if self.music_channel.get_busy():
                self.music_channel.pause()
                self.music_channel.fadeout(500)  # Fade out da música atual

            # Atualizar a música atual
            self.actual_bg_music = next_music
            bg_music = self.audio_files[f'{next_music}_ost']
            self.music_channel.play(bg_music, loops=-1)
        if volume != -1:
            self.music_channel.set_volume(volume)
        
    def final_screen(self, dt):
        if not self.final_screen_ended:
            self.final_animation_timer.update()
            lace = self.current_stage.lace
            player = self.current_stage.player
            if lace.on_final_animation:
                if self.current_stage.collision_sprites:
                    level = self.current_stage
                    collision_sprites = self.current_stage.collision_sprites.sprites() + self.current_stage.semi_collision_sprites.sprites()
                    for sprite in collision_sprites:
                        sprite.kill()
                    # Free level
                    level.player.throw_attacking = False
                    level.during_throw_attack = False
                    level.during_spin_attack = False
                    if level.player_neutral_attack_sprite != None:
                        level.player_neutral_attack_sprite.kill()
                    if level.player_throw_attack_sprite != None:
                        level.player_throw_attack_sprite.kill()
                    if level.player_throw_attack_sprite != None:
                        level.player_throw_attack_sprite.kill()
                    for sprite in level.weapon_sprites:
                        sprite.free()
                    # Free Player
                    player.on_final_animation = True
                    player.spin_attacking = False
                    player.using_weapon = False
                    player.direction.x = 0
                    player.direction.y = 0
                    player.dash_progress = player.dash_distance
                    # Free lace
                    lace.can_move = False
                    lace.direction.x = 0
                    lace.direction.y = 0
                    lace.state = 'dash'
                    self.final_animation_timer.activate()

                    # Player surf
                    white_mask = pygame.mask.from_surface(player.image)
                    white_surf = white_mask.to_surface()
                    white_surf.set_colorkey('black')
                    player.image = white_surf

                    # Lace surf
                    white_mask = pygame.mask.from_surface(lace.image)
                    white_surf = white_mask.to_surface()
                    white_surf.set_colorkey('black')
                    lace.image = white_surf
                    
                    # Efeitos
                    level.fade_alpha = 0
                    level.fade_out = True
                    self.set_slow_motion(0.1)

            if not self.final_animation_timer.active and lace.on_final_animation:
                self.set_slow_motion(1)
                self.state = 'final_screen'
                self.final_screen_ended = True

            if player.hitbox_rect.x > lace.hitbox_rect.x and lace.on_final_animation:
                player.hitbox_rect.x += 50 * dt
                lace.hitbox_rect.x -= 50 * dt
            elif lace.on_final_animation:
                player.hitbox_rect.x -= 50 * dt
                lace.hitbox_rect.x += 50 * dt

    def run(self):
        while True:
            delta_time = self.clock.tick() / 1000 * self.slow_motion_factor # Delta time para normalizar o fps, o fps não é travado
            # Verificação dos eventos do jogo
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:  # Verifica se uma tecla foi pressionada
                    if event.key == pygame.K_F3:  # Verifica se a tecla é F3
                        self.should_show_fps = not self.should_show_fps  # Alterna o estado de exibição de FPS
                if self.detect_pause_button(event) and not self.state == 'final_screen':
                    self.state = 'menu'
                    self.menu.fade_alpha = 255

            # Menu
            if self.state == 'menu':
                self.handle_music(volume=0.5)
                next_state = self.menu.display_menu()
                if next_state == 'play':
                    self.handle_music(volume=1)
                    self.state = 'game'
                    self.current_stage.timers['loading_time'].activate()

            # Game
            elif self.state == 'game':
                if not hasattr(self.current_stage, 'lace'):
                    self.handle_music('main')
                self.current_stage.run(delta_time) # Atualização dos sprites do jogo a partir do arquivo "Level"
    
                if not self.current_stage.timers['loading_time'].active and not self.final_animation_timer.active:
                    self.ui.update(delta_time) # HUD do jogo
                if self.should_show_fps:
                    self.show_fps()
                pygame.display.update() # Atualização da tela

            # Final Screen
            if hasattr(self.current_stage, 'lace'):
                lace = self.current_stage.lace
                if lace.state != 'idle' and not lace.on_final_animation:
                    self.handle_music('lace')
                elif lace.on_final_animation:
                    self.handle_music('ending')
                self.final_screen(delta_time)
                if self.state == 'final_screen':
                    next_state = self.final_screen_menu.display_menu()

if __name__ == '__main__': # Verifica se o script está sendo executado diretamente (exemplo: python main.py)
    # Inicialização do jogo
    game = Game()
    game.run()