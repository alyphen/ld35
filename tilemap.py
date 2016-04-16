import pygame


class Tileset(object):
    """Maintains images to be indexed and drawn by a tilemap."""
    pass


class Tilemap(object):
    def __init__(self, image, width, height):
        self._sprite = pygame.sprite.Sprite()
        self._sprite.image = image
        self._sprite.rect = image.get_rect()

        self.width = width
        self.height = height
        self.tiles = [[0 for x in range(width)] for y in range(height)]

    def draw(self, surface, camera):
        columns = self.width / self._sprite.rect.width
        rows = self.height / self._sprite.rect.height

        for c in range(columns):
            for r in range(rows):
                self._sprite.rect.x = c * self._sprite.rect.w
                self._sprite.rect.y = r * self._sprite.rect.h

                if camera.colliderect(self._sprite.rect):
                    draw_rect = self._sprite.rect
                    draw_rect.x -= camera.x
                    draw_rect.y -= camera.y
                    surface.blit(self._sprite.image, self._sprite.rect)
