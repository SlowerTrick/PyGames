from settings import *
from os.path import join
from timecount import Timer
import pygame
import sys

class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image or font.render(text_input, True, base_color)
        self.pos = pos
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.text_input = text_input
        self.text = font.render(text_input, True, base_color)
        self.rect = self.image.get_rect(center=pos)
        self.text_rect = self.text.get_rect(center=pos)

    def update(self, screen):
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def check_for_input(self, position):
        return self.rect.collidepoint(position)

    def change_color(self, selected):
        color = self.hovering_color if selected else self.base_color
        self.text = self.font.render(self.text_input, True, color)

class Menu:
    def __init__(self, screen, font, button_sound):
        self.screen = screen
        self.font = font
        self.button_sound = button_sound
        self.buttons = [
            Button(None, (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), "PLAY", self.get_font(45), "White", "Gray"),
            Button(None, (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.5), "QUIT", self.get_font(45), "White", "Gray"),
        ]
        self.background_image = pygame.transform.scale(
            pygame.image.load(join('..', 'graphics', 'ui', 'Background.png')), 
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        self.selected_button = 0

        # Temporizador
        self.button_cooldown = Timer(250)

        # Inicializando os joysticks
        self.joysticks = []
        self.controller_type = None  # Será 'Xbox' ou 'PS4' ou 'None'

        # Detectando os joysticks conectados
        self.init_joysticks()

        # Efeitos da tela
        self.fade_alpha = 255  # Nível de opacidade inicial (0-255)
        self.fade_speed = 5   # Velocidade do fade 

    def init_joysticks(self):
        joystick_count = pygame.joystick.get_count()

        if joystick_count > 0:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                self.joysticks.append(joystick)

            joystick_name = self.joysticks[0].get_name().lower()
            
            xbox_keywords = ['xbox', '360', 'one', 'series']
            ps_keywords = ['ps', 'play', 'ps4', 'ds', 'dualshock', 'wireless', 'controller']

            # Verifica se qualquer palavra-chave está no nome do joystick
            if any(keyword in joystick_name for keyword in xbox_keywords):
                self.controller_type = 'Xbox'
            elif any(keyword in joystick_name for keyword in ps_keywords):
                self.controller_type = 'PS4'
            else:
                self.controller_type = 'Unknown'
        
    def get_font(self, size):
        return pygame.font.Font(join('..', 'graphics', 'ui', 'SuperPixel.ttf'), size)

    def handle_events(self, mouse_pos):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in {pygame.K_w, pygame.K_UP}:
                    self.change_selection(-1)
                if event.key in {pygame.K_s, pygame.K_DOWN}:
                    self.change_selection(1)
                if event.key == pygame.K_RETURN:
                    return self.activate_button()

            if self.detect_pause_button(event): 
                return 'play'

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(self.buttons):
                    if button.check_for_input(mouse_pos):
                        self.selected_button = i
                        return self.activate_button()

        # Suporte ao controle
        return self.handle_joystick_input()

    def handle_joystick_input(self):
        # Atualiza o cooldown
        self.button_cooldown.update()
        
        if not self.button_cooldown.active:
            # Eixos analógicos
            vertical_axis = sum(joystick.get_axis(1) for joystick in self.joysticks)
            if vertical_axis < -0.5:  # Para cima
                self.change_selection(-1)
                self.button_cooldown.activate()
            elif vertical_axis > 0.5:  # Para baixo
                self.change_selection(1)
                self.button_cooldown.activate()

            # Botão de seleção (exemplo: botão "A" no controle Xbox)
            if any(joystick.get_button(0) for joystick in self.joysticks):
                return self.activate_button()

    def detect_pause_button(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
        elif event.type == pygame.JOYBUTTONDOWN: 
            for joystick in self.joysticks:
                if self.controller_type == 'Xbox':
                    if joystick.get_button(7):
                        return True
                elif self.controller_type == 'PS4':
                    if joystick.get_button(6):
                        return True
        return False

    def change_selection(self, direction):
        if not self.button_cooldown.active:
            self.selected_button = (self.selected_button + direction) % len(self.buttons)

    def activate_button(self):
        if self.selected_button == 0:  # PLAY
            self.button_sound.play()
            return "play"
        if self.selected_button == 1:  # QUIT
            self.button_sound.play()
            pygame.quit()
            sys.exit()

    def screen_effects(self):
        # Fade in
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen.get_size())
            fade_surface.fill((0, 0, 0))  # Preencher com preto
            fade_surface.set_alpha(self.fade_alpha)  # Definir opacidade
            self.screen.blit(fade_surface, (0, 0))  # Aplicar o fade na tela
            self.fade_alpha -= self.fade_speed # Reduzir opacidade gradualmente
            if self.fade_alpha < 0:
                self.fade_alpha = 0  # Garantir que a opacidade não fique negativa

    def display_menu(self):
        menu_state = None  # Variável para armazenar o estado do menu
        while True:
            self.screen.blit(self.background_image, (0, 0))

            # Renderiza texto principal
            menu_text = self.get_font(55).render("SILKSONG DEMAKE", True, "White")
            menu_rect = menu_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 3))
            self.screen.blit(menu_text, menu_rect)

            # Efeitos
            self.screen_effects()

            # Atualiza os botões
            for i, button in enumerate(self.buttons):
                button.change_color(i == self.selected_button)
                button.update(self.screen)
                if i == self.selected_button:
                    pygame.draw.rect(self.screen, "White", button.rect.inflate(10, 10), 3)

            mouse_pos = pygame.mouse.get_pos()
            menu_state = self.handle_events(mouse_pos)
            
            if menu_state:  # Sai do menu se o estado mudar
                return menu_state
            
            pygame.display.update()

class Final_screen:
    def __init__(self, screen, font, button_sound):
        self.screen = screen
        self.font = font
        self.button_sound = button_sound
        self.buttons = [
            Button(None, (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.2), "QUIT", self.get_font(25), "White", "Gray"),
        ]
        self.background_image = pygame.transform.scale(
            pygame.image.load(join('..', 'graphics', 'ui', 'Background.png')), 
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        self.selected_button = 0

        # Temporizador
        self.button_cooldown = Timer(250)

        # Inicializando os joysticks
        self.joysticks = []
        self.controller_type = None  # Será 'Xbox' ou 'PS4' ou 'None'

        # Detectando os joysticks conectados
        self.init_joysticks()

        # Efeitos da tela
        self.fade_alpha = 255  # Nível de opacidade inicial (0-255)
        self.fade_speed = 5   # Velocidade do fade 

    def init_joysticks(self):
        joystick_count = pygame.joystick.get_count()

        if joystick_count > 0:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                self.joysticks.append(joystick)

            joystick_name = self.joysticks[0].get_name().lower()
            
            xbox_keywords = ['xbox', '360', 'one', 'series']
            ps_keywords = ['ps', 'play', 'ps4', 'ds', 'dualshock', 'wireless', 'controller']

            # Verifica se qualquer palavra-chave está no nome do joystick
            if any(keyword in joystick_name for keyword in xbox_keywords):
                self.controller_type = 'Xbox'
            elif any(keyword in joystick_name for keyword in ps_keywords):
                self.controller_type = 'PS4'
            else:
                self.controller_type = 'Unknown'
        
    def get_font(self, size):
        return pygame.font.Font(join('..', 'graphics', 'ui', 'SuperPixel.ttf'), size)

    def handle_events(self, mouse_pos):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key in {pygame.K_w, pygame.K_UP}:
                    self.change_selection(-1)
                if event.key in {pygame.K_s, pygame.K_DOWN}:
                    self.change_selection(1)
                if event.key == pygame.K_RETURN:
                    return self.activate_button()

            if self.detect_pause_button(event): 
                return 'play'

            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, button in enumerate(self.buttons):
                    if button.check_for_input(mouse_pos):
                        self.selected_button = i
                        return self.activate_button()

        # Suporte ao controle
        return self.handle_joystick_input()

    def handle_joystick_input(self):
        # Atualiza o cooldown
        self.button_cooldown.update()
        
        if not self.button_cooldown.active:
            # Eixos analógicos
            vertical_axis = sum(joystick.get_axis(1) for joystick in self.joysticks)
            if vertical_axis < -0.5:  # Para cima
                self.change_selection(-1)
                self.button_cooldown.activate()
            elif vertical_axis > 0.5:  # Para baixo
                self.change_selection(1)
                self.button_cooldown.activate()

            # Botão de seleção
            if any(joystick.get_button(0) for joystick in self.joysticks):
                return self.activate_button()

    def detect_pause_button(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return True
        elif event.type == pygame.JOYBUTTONDOWN: 
            for joystick in self.joysticks:
                if self.controller_type == 'Xbox':
                    if joystick.get_button(7):
                        return True
                elif self.controller_type == 'PS4':
                    if joystick.get_button(6):
                        return True
        return False

    def change_selection(self, direction):
        if not self.button_cooldown.active:
            self.selected_button = (self.selected_button + direction) % len(self.buttons)

    def activate_button(self):
        if self.selected_button == 0:  # QUIT
            self.button_sound.play()
            pygame.quit()
            sys.exit()

    def screen_effects(self):
        # Fade in
        if self.fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen.get_size())
            fade_surface.fill((0, 0, 0))  # Preencher com preto
            fade_surface.set_alpha(self.fade_alpha)  # Definir opacidade
            self.screen.blit(fade_surface, (0, 0))  # Aplicar o fade na tela
            self.fade_alpha -= self.fade_speed / 5  # Reduzir opacidade gradualmente
            if self.fade_alpha < 0:
                self.fade_alpha = 0  # Garantir que a opacidade não fique negativa

    def display_menu(self):
        menu_state = None  # Variável para armazenar o estado do menu
        while True:
            self.screen.blit(self.background_image, (0, 0))

            # Renderiza texto principal
            menu_text = self.get_font(55).render("SILKSONG DEMAKE", True, "White")
            menu_rect = menu_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 6))
            self.screen.blit(menu_text, menu_rect)

            # Renderiza o "The End"
            the_end_text = self.get_font(85).render("The End", True, "#800020")
            the_end_rect = the_end_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2))
            self.screen.blit(the_end_text, the_end_rect)

            # Efeitos
            self.screen_effects()

            # Atualiza os botões
            for i, button in enumerate(self.buttons):
                button.change_color(i == self.selected_button)
                button.update(self.screen)
                if i == self.selected_button:
                    pygame.draw.rect(self.screen, "White", button.rect.inflate(10, 10), 3)

            mouse_pos = pygame.mouse.get_pos()
            menu_state = self.handle_events(mouse_pos)
            
            if menu_state:  # Sai do menu se o estado mudar
                return menu_state
            
            pygame.display.update()