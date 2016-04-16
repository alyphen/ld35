import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, position):
        super(Player, self).__init__()
        self.image = pygame.image.load("images/player.png")

        self.rect = self.image.get_rect()

        self.k_left = 0
        self.k_right = 0
        self.k_up = 0
        self.k_down = 0

        self.speed = 100
        self.position = position

    def on_event(self, event):
        down = event.type == pygame.KEYDOWN
        if not hasattr(event, 'key'): return

        if event.key == pygame.K_LEFT:
            self.k_left = down * -self.speed
        if event.key == pygame.K_RIGHT:
            self.k_right = down * self.speed
        if event.key == pygame.K_UP:
            self.k_up = down * -self.speed
        if event.key == pygame.K_DOWN:
            self.k_down = down * self.speed


    def update(self, d_t):
        d_t /= 1000.0
        x, y = self.position

        x += d_t * (self.k_left + self.k_right)
        y += d_t * (self.k_up + self.k_down)

        self.position = (x, y)
        self.rect.center = self.position

    def draw(self, surface):
        surface.blit(self.image, self.rect)
