import pygame

class Player(pygame.sprite.Sprite):
    @classmethod
    def from_tmx(self, tmx_object):
        player = Player((tmx_object.x, tmx_object.y))
        #player.image = tmx_object.image
        player.id = tmx_object.id

        return player
    def __init__(self, position, speed=200):
        super(Player, self).__init__()
        self.image = pygame.image.load("examples/placeholder_player.png")

        self.rect = self.image.get_rect()
        self.feet = pygame.Rect(0, 0, self.rect.width * .5, 12)

        self.k_left = 0
        self.k_right = 0
        self.k_up = 0
        self.k_down = 0

        self.speed = speed
        self.position = position
        self._old_position = self.position

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
        self._old_position = self.position

        d_t /= 1000.0
        x, y = self.position

        d_x = d_t * (self.k_left + self.k_right)
        d_y = d_t * (self.k_up + self.k_down)
        self.d_pos = (d_x, d_y)

        x += d_x
        y += d_y

        self.position = (x, y)
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom

    # This is used to move back from walls
    # Should really be more generic collision response
    def move_back(self, d_t, walls):
        #self.position = self._old_position

        for wall in walls:
            # find region
            overlap = self.rect.clip(wall)

            # compensate for collidepoint not detecting edges
            overlap.height += 1
            overlap.width += 1

            x, y = self.position

            if overlap.collidepoint(self.feet.midtop):
                y -= overlap.height
                y = self._old_position[1]
            elif overlap.collidepoint(self.feet.midleft):
                x += overlap.width
                x = self._old_position[0]
            elif overlap.collidepoint(self.feet.midbottom):
                y += overlap.height
                y = self._old_position[1]
            elif overlap.collidepoint(self.feet.midright):
                x -= overlap.width
                x = self._old_position[0]

            self.position = (x, y)

        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom

