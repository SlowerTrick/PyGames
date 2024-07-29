from settings import *
from os.path import join

class Button:
    def __init__(self, image, pos, text_input, font, base_color, hovering_color):
        self.image = image
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.font = font
        self.base_color, self.hovering_color = base_color, hovering_color
        self.text_input = text_input
        self.text = self.font.render(self.text_input, True, self.base_color)
        if self.image is None:
            self.image = self.text
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))
        self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos))

    def update(self, screen):
        if self.image is not None:
            screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def checkForInput(self, position):
        if self.rect.collidepoint(position):
            return True
        return False

    def changeColor(self, position):
        if self.rect.collidepoint(position):
            self.text = self.font.render(self.text_input, True, self.hovering_color)
        else:
            self.text = self.font.render(self.text_input, True, self.base_color)

class Menu:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.play_button = Button(None, (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), "PLAY", self.get_font(45), "White", "Red")
        self.quit_button = Button(None, (WINDOW_WIDTH / 2, WINDOW_HEIGHT / 1.5), "QUIT", self.get_font(45), "White", "Red")
        self.background_image = pygame.image.load(join('..', 'graphics', 'ui', 'Background.png'))
        self.background_image = pygame.transform.scale(self.background_image, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
    def get_font(self, size):
        return pygame.font.Font(join('..', 'graphics', 'ui', 'SuperPixel.ttf'), 40)

    def display_menu(self):
        while True:
            self.screen.fill("black")
            self.screen.blit(self.background_image, (-1, 0))

            mouse_pos = pygame.mouse.get_pos()

            menu_text = self.get_font(75).render("SILKSONG DEMAKE", True, "White")
            menu_rect = menu_text.get_rect(center=(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 3))
            self.screen.blit(menu_text, menu_rect)

            self.play_button.changeColor(mouse_pos)
            self.play_button.update(self.screen)

            self.quit_button.changeColor(mouse_pos)
            self.quit_button.update(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.play_button.checkForInput(mouse_pos):
                        return "play"
                    if self.quit_button.checkForInput(mouse_pos):
                        pygame.quit()
                        sys.exit()
            pygame.display.update()