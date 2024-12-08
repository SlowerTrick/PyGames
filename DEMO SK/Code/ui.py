from settings import * 
from sprites import AnimatedSprite, Sprite
from random import randint
from timecount import Timer

class UI:
    def __init__(self, font, frames):
        self.display_surface = pygame.display.get_surface()
        self.sprites = pygame.sprite.Group()
        self.font = font

        # Vida do jogador
        self.heart_frames = frames['heart']
        self.heartless_frames = frames['heartless']
        self.ui_bar_frames = frames['ui_bar']
        self.string_bar_frames = frames['string_bar']
        self.weapons_frames = frames['weapons']
        self.heart_surface_width = self.heart_frames[0].get_width()
        self.heart_padding = 6

        # Moedas do jogador
        self.coin_amount = 0
        self.coin_timer = Timer(1000)
        self.coin_surface = frames['coin']

    def create_hearts(self, amount, max):
        for sprite in self.sprites:
            if hasattr(sprite, 'is_heart'):
                sprite.kill()

        for heart in range(max):
            x = 80 + heart * (self.heart_surface_width + self.heart_padding)
            y = 30
            if heart < amount:
                Heart((x,y), self.heart_frames, self.sprites)
            else:
                HeartLess((x,y), self.heartless_frames, self.sprites)

    def create_ui_bar(self, health_regen):
        UIBar((10,10), self.ui_bar_frames, self.sprites, health_regen)
    
    def create_string_bar(self, amount):
        for sprite in self.sprites:
            if hasattr(sprite, 'is_StringBar'):
                sprite.kill()
        StringBar((25, 90), self.string_bar_frames, self.sprites, amount)
    
    def create_weapons_frame(self, weapon):
        for sprite in self.sprites:
            if hasattr(sprite, 'is_WeaponFrame') or hasattr(sprite, 'is_WeaponFrameChild'):
                sprite.kill()
        WeaponFrame((120, 90), self.weapons_frames['weapons'][weapon], self.sprites)

    def display_text(self):
        if self.coin_timer.active:
            text_surface = self.font.render(str(self.coin_amount), False, '#33323d')
            text_rect = text_surface.get_frect(topleft = (16,34))
            self.display_surface.blit(text_surface, text_rect)

            coin_rect = self.coin_surface.get_frect(center = text_rect.bottomleft).move(0,-2)
            self.display_surface.blit(self.coin_surface, coin_rect)

    def show_coins(self, amount):
        self.coin_amount = amount
        self.coin_timer.activate()

    def update(self, dt):
        if randint(0,1000) == 1:
            for animate in self.sprites:
                animate.active = True

        self.coin_timer.update()
        self.sprites.update(dt)
        self.sprites.draw(self.display_surface)
        self.display_text()

class Heart(AnimatedSprite):
    def __init__(self, pos, frames, groups):
        super().__init__(pos, frames, groups)
        self.active = False
        self.is_heart = True

    def animate(self, dt):
        self.frame_index += ANIMATION_SPEED * dt
        if self.frame_index < len(self.frames):
            self.image = self.frames[int(self.frame_index)]
        else:
            self.active = False
            self.frame_index = 0 

    def update(self, dt):
        if self.active:
            self.animate(dt)

class HeartLess(Sprite):
    def __init__(self, pos, frames, groups):
        self.is_heart = True
        super().__init__(pos, frames, groups)

class UIBar(Sprite):
    def __init__(self, pos, frames, groups, health_regen):
        self.is_UIBar = True
        if health_regen:
            self.image = frames[1]
        else:
            self.image = frames[0]

        super().__init__(pos, self.image, groups)

class StringBar(Sprite):
    def __init__(self, pos, frames, groups, string_count):
        self.is_StringBar = True
        self.image = self.frames = frames[string_count]
        super().__init__(pos, self.image, groups)

class WeaponFrame(Sprite):
    def __init__(self, pos, frames, groups):
        self.is_WeaponFrame = True
        self.image = self.frames = frames
        super().__init__(pos, frames, groups)

class WeaponFrameChild(Sprite):
    def __init__(self, pos, frames, groups, weapon):
        self.is_WeaponFrameChild = True
        self.image = self.frames = frames
        super().__init__(pos, frames, groups)
    