from settings import *
from level import Level
from pytmx.util_pygame import load_pygame
from os.path import join
from support import *
from data import Data
from ui import UI
from menu import Menu

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
        self.menu = Menu(self.display_surface, self.font)
        self.state = "game"

        # Level
        self.start_stage = 0 # 8 para lace
        self.player_spawn = 'left'
        self.current_stage = Level(self.tmx_maps[self.start_stage], self.level_frames, self.audio_files, self.data, self.switch_screen, self.start_stage, self.player_spawn)
        self.current_stage.timers['loading_time'].activate()
        self.bg_music.play(-1)

        # Inicializando os joysticks
        self.joysticks = []
        self.controller_type = None  # Será 'Xbox 360' ou 'PS4' ou 'None'

        # Detectando os joysticks conectados
        self.init_joysticks()

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
            10: load_pygame(join('..', 'data', 'levels', '10.tmx')),
        }

        self.level_frames = {
            # Adição dos sprites animados
            'flag': import_folder('..', 'graphics', 'level', 'flag'),
            'saw': import_folder('..', 'graphics', 'enemies', 'saw', 'animation'),
            'floor_spike': import_sub_folders('..', 'graphics','enemies', 'floor_spikes'),
            'chest': import_folder('..', 'graphics', 'level', 'chest'),
            'window': import_folder('..', 'graphics','level', 'window'),
            'big_chain': import_folder('..', 'graphics','level', 'big_chains'),
            'small_chain': import_folder('..', 'graphics','level', 'small_chains'),
            'candle_light': import_folder('..', 'graphics','level', 'candle light'),
            'player': import_sub_folders('..', 'graphics', 'player'),
            'saw_chain': import_image('..',  'graphics', 'enemies', 'saw', 'saw_chain'),
            'helicopter': import_folder('..', 'graphics', 'level', 'helicopter'),
            'spike': import_image('..',  'graphics', 'enemies', 'spike_ball', 'Spiked Ball'),
            'spike_chain': import_image('..',  'graphics', 'enemies', 'spike_ball', 'spiked_chain'),
            'runner': import_folder('..', 'graphics', 'enemies', 'runner', 'run'),
            'shell': import_sub_folders('..', 'graphics', 'enemies', 'shell'),
            'breakable_wall': import_image('..',  'graphics', 'enemies', 'breakable_wall', 'wall'),
            'slime': import_sub_folders('..', 'graphics', 'enemies', 'slime'),
            'butterfly': import_folder('..', 'graphics', 'enemies', 'butterfly'),
            'lace': import_sub_folders('..', 'graphics', 'enemies', 'lace'),
            'fly': import_sub_folders('..', 'graphics', 'enemies', 'fly'),
            'pearl': import_image('..',  'graphics', 'enemies', 'bullets', 'pearl'),
            'items': import_sub_folders('..', 'graphics', 'items'),
            'kurisu': import_image('..',  'graphics', 'icon', 'chibi'),
            'particle': import_folder('..', 'graphics', 'effects', 'particle'),
            'water_top': import_folder('..', 'graphics', 'level', 'water', 'top'),
            'water_body': import_image('..', 'graphics', 'level', 'water', 'body'),
            'bg_tiles': import_folder_dict('..', 'graphics', 'level', 'bg', 'tiles'),
            'cloud_small': import_folder('..', 'graphics','level', 'clouds', 'small'),
            'cloud_large': import_image('..', 'graphics','level', 'clouds', 'large_cloud'),
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
        }
        self.bg_music = pygame.mixer.Sound(join('..', 'audio', 'noragami.mp3'))
        self.bg_music.set_volume(0.5)

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

    def switch_screen(self, target, player_spawn):
        print(len(self.tmx_maps))
        if target >= len(self.tmx_maps):
            target = 0
        self.current_stage = Level(self.tmx_maps[target], self.level_frames, self.audio_files, self.data, self.switch_screen, target, player_spawn)
        self.current_stage.timers['loading_time'].activate()

    def show_fps(self):
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

    def run(self):
        while True:
            delta_time = self.clock.tick() / 1000 # Delta time para normalizar o fps, o fps não é travado
            # Verificação dos eventos do jogo
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.detect_pause_button(event):
                        self.state = 'menu'

            # Menu
            if self.state == 'menu':
                next_state = self.menu.display_menu()
                if next_state == 'play':
                    self.state = 'game'
                    self.current_stage.timers['loading_time'].activate()
            # Jogo
            elif self.state == 'game':
                self.current_stage.run(delta_time) # Atualização dos sprites do jogo a partir do arquivo "Level"
    
                if not self.current_stage.timers['loading_time'].active:
                    self.ui.update(delta_time) # HUD do jogo
                self.show_fps()
                pygame.display.update() # Atualização da tela

if __name__ == '__main__': # Verifica se o script está sendo executado diretamente (exemplo: python main.py)
    # Inicialização do jogo
    game = Game()
    game.run()