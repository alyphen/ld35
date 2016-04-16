import pygame
from pygame.locals import *

from tilemap import Tilemap
from player import Player
from camera_group import CameraGroup


class Game:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1280, 720

        self.camera = pygame.Rect(0, 0, self.width, self.height)

        self._clock = pygame.time.Clock()
        self.fps = 60

        self.updateables = []
        self.drawables = []

        self.players_group = CameraGroup()

    def add_game_object(self, game_object):
        if hasattr(game_object, 'update'):
            self.updateables.append(game_object)

        if hasattr(game_object, 'draw'):
            self.drawables.append(game_object)

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True

        tile_sprite = pygame.image.load('images/basetile.png')
        self.tilemap = Tilemap(tile_sprite, 5000, 1000)
        self.add_game_object(self.tilemap)

        self.player = Player((500, 500))
        self.players_group.add(self.player)
        self.add_game_object(self.players_group)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._running = False

        self.player.on_event(event)

    def on_loop(self):
        d_t = self._clock.tick(self.fps)
        for updateable in self.updateables:
            # camera is given here to ensure Sprite Groups can pass it on to Sprites
            updateable.update(d_t)
        self.camera.center = self.player.position

    def on_draw(self):
        self._display_surf.fill((0, 0, 0))

        for drawable in self.drawables:
            drawable.draw(self._display_surf, self.camera)

        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def on_execute(self):
        self.on_init()
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_draw()
        self.on_cleanup()

if __name__ == "__main__":
    game = Game()
    game.on_execute()
