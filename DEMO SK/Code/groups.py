from settings import *
from sprites import Sprite, Cloud
from random import choice, randint
from timecount import Timer

class AllSprites(pygame.sprite.Group):
    def __init__(self, width, height, clouds, horizon_line, bg_tile = None, top_limit = 0):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = vector()
        self.width, self.height = width * TILE_SIZE, height * TILE_SIZE
        self.borders = {
            'left': 0,
            'right': -self.width + WINDOW_WIDTH,
            'bottom': -self.height + WINDOW_HEIGHT,
            'top': top_limit,
        }
        self.sky = not bg_tile # Bool para verificar a necessidade do céu, a partir da não existencia de um tile
        self.horizon_line = horizon_line

        if bg_tile:
            for col in range(width):
                for row in range(-int(top_limit / TILE_SIZE) - 1, height):
                    x, y = col * TILE_SIZE, row * TILE_SIZE
                    Sprite((x, y), bg_tile, self, -1)
        else:
            # Céu
            self.large_cloud = clouds['large']
            self.small_clouds = clouds['small']
            self.cloud_direction = -1

            # Nuvem grande
            self.large_cloud_speed = 50
            self.large_cloud_x = 0
            self.large_cloud_tiles = int(self.width / self.large_cloud.get_width()) + 2
            self.large_cloud_width, self.large_cloud_height = self.large_cloud.get_size()

            # Nuvem pequena
            self.cloud_timer = Timer(2500, self.create_cloud, True) # Cria a nuvem repete a cada 2.5 segundos
            self.cloud_timer.activate()
            for cloud in range(5):
                pos = (randint(0, self.width), randint(self.borders['top'], self.horizon_line))
                surface = choice(self.small_clouds)
                Cloud(pos, surface, self)
        
    def draw_large_cloud(self, delta_time):
        self.large_cloud_x += self.cloud_direction * self.large_cloud_speed * delta_time 
        if self.large_cloud_x <= -self.large_cloud_width:
            self.large_cloud_x = 0

        for cloud in range(self.large_cloud_tiles):
            left = self.large_cloud_x + self.large_cloud_width * cloud + self.offset.x
            top = self.horizon_line - self.large_cloud_height + self.offset.y
            self.display_surface.blit(self.large_cloud, (left, top))
    
    def camera_constraint(self):
        # Limitação da camera do jogador
        self.offset.x = self.offset.x if self.offset.x < self.borders['left'] else self.borders['left']
        self.offset.x = self.offset.x if self.offset.x > self.borders['right'] else self.borders['right']
        self.offset.y = self.offset.y if self.offset.y > self.borders['bottom'] else self.borders['bottom']
        self.offset.y = self.offset.y if self.offset.y < self.borders['top'] else self.borders['top']
    
    def draw_sky(self):
        self.display_surface.fill('#181818')
        horizon_pos = self.horizon_line + self.offset.y

        sea_rect = pygame.FRect(0,horizon_pos, WINDOW_WIDTH, WINDOW_HEIGHT - horizon_pos)
        pygame.draw.rect(self.display_surface, '#181818', sea_rect)

        # Linha do horizonte
        pygame.draw.line(self.display_surface, '#181818', (0, horizon_pos), (WINDOW_WIDTH, horizon_pos), 4)

    def create_cloud(self):
        pos = (randint(self.width + 500, self.width + 600), randint(self.borders['top'], self.horizon_line))
        surface = choice(self.small_clouds)
        Cloud(pos, surface, self)

    def draw(self, target_pos, delta_time):
        # Movimentação da camera do jogador
        self.offset.x = -(target_pos[0] - WINDOW_WIDTH / 2) # "-" pois o movimento é oposto ao crescimento da tela
        self.offset.y = -(target_pos[1] - WINDOW_HEIGHT / 2) # "-" pois o movimento é oposto ao crescimento da tela
        self.camera_constraint()

        # Desenho do céu
        if self.sky:
            self.cloud_timer.update()
            self.draw_sky()
            self.draw_large_cloud(delta_time)

        for sprite in sorted(self, key = lambda sprite: sprite.z):
            # Desenha os elementos com base na ordem em Z_LAYER
            offset_pos = sprite.rect.topleft + self.offset
            self.display_surface.blit(sprite.image, offset_pos)