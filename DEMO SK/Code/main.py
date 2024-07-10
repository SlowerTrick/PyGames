from settings import *
from level import Level
from pytmx.util_pygame import load_pygame
from os.path import join

class Game:
    def __init__(self):
        pygame.init() # Inicialização do pygame
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE) # Tela
        pygame.display.set_caption('DEMO SilkSong') # Nome do jogo
        icon = pygame.image.load('../Assets/Hornet/chibi.jpg') # Icone do jogo
        pygame.display.set_icon(icon)
        self.clock = pygame.time.Clock() # FPS

        # Carregamento dos mapas do jogo
        self.tmx_maps = {0: load_pygame(join('..', 'data', 'levels', 'omni.tmx'))}
        self.current_stage = Level(self.tmx_maps[0])

    def run(self):
        while True:
            delta_time = self.clock.tick() / 1000 # Delta time para normalizar o fps, o fps não é travado

            # Verificação dos eventos do jogo
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            self.current_stage.run(delta_time) # Atualização dos sprites do jogo a partir do arquivo "Level"
            pygame.display.update() # Atualização da tel

if __name__ == '__main__': # Verifica se o script está sendo executado diretamente (exemplo: python main.py)
    # Inicialização do jogo
    game = Game()
    game.run()