import pygame

class CameraGroup(pygame.sprite.Group):
    def __init__(self, *args, **kwargs):
        super(CameraGroup, self).__init__(*args, **kwargs)

    def draw(self, surface, camera):
        for sprite in self.sprites():
            draw_rect = sprite.rect

            if camera.colliderect(draw_rect):
                draw_rect.x -= camera.x
                draw_rect.y -= camera.y

                surface.blit(sprite.image, draw_rect)
