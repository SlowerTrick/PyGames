from settings import *
from level import Level
from pytmx.util_pygame import load_pygame
from os.path import join
from support import *
from data import Data
from ui import UI

class Game:
    def __init__(self):
        pygame.init() # Inicialização do pygame
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.FULLSCREEN) # Tela
        pygame.display.set_caption('DEMO SilkSong') # Nome do jogo
        icon = pygame.image.load('../Assets/Hornet/chibi.jpg') # Icone do jogo
        pygame.display.set_icon(icon)

        self.clock = pygame.time.Clock() # FPS
        self.import_assets()

        # Carregamento das informações do jogo
        self.ui = UI(self.font, self.ui_frames)
        self.data = Data(self.ui)

        # Carregamento dos mapas do jogo
        self.tmx_maps = {0: load_pygame(join('..', 'data', 'levels', 'omni.tmx'))}
        self.current_stage = Level(self.tmx_maps[0], self.level_frames, self.data)

    def import_assets(self):
        self.level_frames = {
            # Adição dos sprites animados
            'flag': import_folder('..', 'graphics', 'level', 'flag'),
            'saw': import_folder('..', 'graphics', 'enemies', 'saw', 'animation'),
            'floor_spike': import_folder('..', 'graphics','enemies', 'floor_spikes'),
            'palms': import_sub_folders('..', 'graphics', 'level', 'palms'),
            'candle': import_folder('..', 'graphics','level', 'candle'),
            'window': import_folder('..', 'graphics','level', 'window'),
            'big_chain': import_folder('..', 'graphics','level', 'big_chains'),
            'small_chain': import_folder('..', 'graphics','level', 'small_chains'),
            'candle_light': import_folder('..', 'graphics','level', 'candle light'),
            'player': import_sub_folders('..', 'graphics', 'player'),
            'saw_chain': import_image('..',  'graphics', 'enemies', 'saw', 'saw_chain'),
            'helicopter': import_folder('..', 'graphics', 'level', 'helicopter'),
            'boat': import_folder('..',  'graphics', 'objects', 'boat'),
            'spike': import_image('..',  'graphics', 'enemies', 'spike_ball', 'Spiked Ball'),
            'spike_chain': import_image('..',  'graphics', 'enemies', 'spike_ball', 'spiked_chain'),
            'tooth': import_folder('..', 'graphics','enemies', 'tooth', 'run'),
            'shell': import_sub_folders('..', 'graphics','enemies', 'shell'),
            'pearl': import_image('..',  'graphics', 'enemies', 'bullets', 'pearl'),
            'items': import_sub_folders('..', 'graphics', 'items'),
            'particle': import_folder('..', 'graphics', 'effects', 'particle'),
            'water_top': import_folder('..', 'graphics', 'level', 'water', 'top'),
            'water_body': import_image('..', 'graphics', 'level', 'water', 'body'),
            'bg_tiles': import_folder_dict('..', 'graphics', 'level', 'bg', 'tiles'),
            'cloud_small': import_folder('..', 'graphics','level', 'clouds', 'small'),
            'cloud_large': import_image('..', 'graphics','level', 'clouds', 'large_cloud'),
        }

        self.font = pygame.font.Font(join('..', 'graphics', 'ui', 'runescape_uf.ttf'), 40)
        self.ui_frames = {
            'heart': import_folder('..', 'graphics', 'ui', 'heart'), 
            'coin':import_image('..', 'graphics', 'ui', 'coin')
        }

    def run(self):
        while True:
            delta_time = self.clock.tick() / 1000 # Delta time para normalizar o fps, o fps não é travado
            
            # Verificação dos eventos do jogo
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.current_stage.run(delta_time) # Atualização dos sprites do jogo a partir do arquivo "Level"
            self.ui.update(delta_time) # HUD do jogo
            pygame.display.update() # Atualização da tela

if __name__ == '__main__': # Verifica se o script está sendo executado diretamente (exemplo: python main.py)
    # Inicialização do jogo
    game = Game()
    game.run()