from settings import *
from sprites import Sprite, MovingSprite
from player import Player

class Level:
    def __init__(self, tmx_map):
        self.display_surface = pygame.display.get_surface() # Inicializa a partir da tela em main

        # Inicialização do grupo de sprites
        self.all_sprites = pygame.sprite.Group() # Criação do grupo de sprites
        self.collision_sprites = pygame.sprite.Group()
        self.setup(tmx_map) # 

    def setup(self, tmx_map):
        # Tiles
        for x, y, surface in tmx_map.get_layer_by_name('Terrain').tiles():
            Sprite((x * TILE_SIZE, y * TILE_SIZE), surface, (self.all_sprites, self.collision_sprites))
        
        # Objetos
        for obj in tmx_map.get_layer_by_name('Objects'):
            if obj.name == 'player':
                Player((obj.x, obj.y), self.all_sprites, self.collision_sprites)
        
        # Objetos moveis
        for obj in tmx_map.get_layer_by_name('Moving Objects'):
            if obj.name == 'helicopter':
                if obj.width > obj.height: # Horizontal
                    move_dir = 'x'
                    start_pos = (obj.x, obj.y + obj.height / 2)
                    end_pos = (obj.x + obj.width, obj.y + obj.height / 2)
                else: # Vertical
                    move_dir = 'y'
                    start_pos = (obj.x + obj.width / 2, obj.y)
                    end_pos = (obj.x + obj.width / 2, obj.y + obj.height)
                speed = obj.properties['speed']
                MovingSprite((self.all_sprites, self.collision_sprites), start_pos, end_pos, move_dir, speed)

    def run(self, delta_time):
        self.display_surface.fill('black') # Preenche a tela com a cor preta
        self.all_sprites.update(delta_time) # Atualiza os sprites da tela
        self.all_sprites.draw(self.display_surface) # Coloca todos os sprite na tela