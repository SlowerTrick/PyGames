from typing import Any
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.image = pygame.Surface((56, 56)) #48 e 56 era antes
        self.image.fill('blue')
        self.rect = self.image.get_frect(topleft = pos)

        # movement
        self.direction = vector()
        self.speed = 200

    def input(self):
        keys = pygame.key.get_pressed()
        input_vector = vector(0,0)
        if keys[pygame.K_RIGHT]:
            input_vector.x += 1
        if keys[pygame.K_LEFT]: 
            input_vector.x -= 1

        # mantém a distancia do vetor mas mantém o seu tamnaho igual
        self.direction = input_vector.normalize() if input_vector else input_vector

    def move(self, dt):
        self.rect.topleft += self.direction * self.speed * dt

    def update(self, dt):
        self.input()
        self.move(dt)