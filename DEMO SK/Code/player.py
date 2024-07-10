from settings import *
from timecount import Timer

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups, collision_sprites):
        super().__init__(groups)
        self.image = pygame.Surface((56, 56)) #48 e 56 era antes, pygame.Surface é usado para criar uma imagem
        self.image.fill('blue')

        # Retângulos
        self.rect = self.image.get_frect(topleft = pos)
        self.old_rect = self.rect.copy()

        # Movimento
        self.direction = vector()
        self.speed = 200
        self.gravity = 1300
        self.jump = False
        self.jump_height = 700

        # Colisão
        self.collision_sprites = collision_sprites
        self.on_surface = {'floor': False, 'left_wall': False, 'right_wall': False}
        self.platform = None

        # Temporizador
        self.timers = {
            'wall_jump': Timer(400),
            'wall_slide_block': Timer(250)
        }

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
            if keys[pygame.K_LEFT]: 
                input_vector.x -= 1
            # Mantém a distancia do vetor e mantém o seu tamanho uniforme
            self.direction.x = input_vector.normalize().x if input_vector else 0
        
        if keys[pygame.K_SPACE]:
            self.jump = True

    def move(self, delta_time):
        # Horizontal
        self.rect.x += self.direction.x * self.speed * delta_time # delta_time por conta do fps
        self.collision('horizontal')

        # Vertical

        # Gravidade na parede
        if not self.on_surface['floor'] and any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active:
            self.direction.y = 0
            self.rect.y += self.gravity / 10 * delta_time

        else:
            # Gravidade normal
            self.direction.y += self.gravity / 2 * delta_time # Medida para normalizar a velocidade (fps)
            self.rect.y += self.direction.y * delta_time
            self.direction.y += self.gravity / 2 * delta_time 

        # Pulo
        if self.jump:
            # Pulo normal
            if self.on_surface['floor']:
                self.direction.y = -self.jump_height
                self.timers['wall_slide_block'].activate()              
                self.rect.bottom -= 1 # Evitar bugs com a plataforma vertical, funciona sem isso se necessário
            # Pulo na parede
            elif any((self.on_surface['left_wall'], self.on_surface['right_wall'])) and not self.timers['wall_slide_block'].active:
                self.direction.y = -self.jump_height
                self.direction.x = 1 if self.on_surface['left_wall'] else -1
                self.timers['wall_jump'].activate()
            self.jump = False

        self.collision('vertical')

    def platform_move(self, delta_time):
        if self.platform:
            self.rect.topleft += self.platform.direction * self.platform.speed * delta_time

    def check_contact(self):
        floor_rect = pygame.Rect(self.rect.bottomleft,(self.rect.width,2))
        right_rect = pygame.Rect(self.rect.topright + vector(0, self.rect.height / 4),(2,self.rect.height / 2))
        left_rect = pygame.Rect(self.rect.topleft + vector(-2, self.rect.height / 4),(2,self.rect.height / 2))

        collide_rects = [sprite.rect for sprite in self.collision_sprites]

        # collisions
        self.on_surface['floor'] = True if floor_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['right_wall'] = True if right_rect.collidelist(collide_rects) >= 0 else False
        self.on_surface['left_wall']  = True if left_rect.collidelist(collide_rects) >= 0 else False

        self.platform = None
        for sprite in [sprite for sprite in self.collision_sprites.sprites() if hasattr(sprite, 'moving')]:
            if sprite.rect.colliderect(floor_rect):
                self.platform = sprite
    
    def collision(self, axis):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.rect):
                if axis == 'horizontal':
                    # Colisão à esquerda
                    if self.rect.left <= sprite.rect.right and self.old_rect.left >= sprite.old_rect.right:
                        self.rect.left = sprite.rect.right
                    
                    # Colisão à direita
                    if self.rect.right >= sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left

                if axis == 'vertical':
                    # Colisão com o chão
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top
                    
                    # Colisão com o teto
                    if self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                        if hasattr(sprite, 'moving'):
                            self.rect.top += 6

                    self.direction.y = 0

    def update_timers(self):
        # Atualiza todos os temporizadores estabelicidos
        for timer in self.timers.values():
            timer.update()

    def update(self, delta_time):
        self.old_rect = self.rect.copy()
        self.update_timers()
        self.input()
        self.move(delta_time)
        self.platform_move(delta_time)
        self.check_contact()