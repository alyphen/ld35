import pygame
from pygame.locals import *

from pytmx import *
from pytmx.util_pygame import load_pygame
import pyscroll
from pyscroll import PyscrollGroup


from tilemap import Tilemap
import gameobjects
from gameobjects import Player


class Game:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1280, 720

        self.filename = 'examples/examplemap.tmx'

        self.camera = pygame.Rect(0, 0, self.width, self.height)

        self._clock = pygame.time.Clock()
        self.fps = 60

        self.updateables = []
        self.drawables = []

    def add_game_object(self, game_object):
        if hasattr(game_object, 'update'):
            self.updateables.append(game_object)

        if hasattr(game_object, 'draw'):
            self.drawables.append(game_object)

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True

        tmx_data = load_pygame(self.filename)
        map_data = pyscroll.data.TiledMapData(tmx_data)
        self.map_layer = pyscroll.BufferedRenderer(map_data, self._display_surf.get_size())
        self.map_layer.zoom = 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        # Find known object types and attach behavior
        for o in tmx_data.objects:
            if hasattr(gameobjects, o.type):
                klass = getattr(gameobjects, o.type)
                if hasattr(klass, 'from_tmx'):
                    game_object = klass.from_tmx(o)
                    self.group.add(game_object)

                    if o.name == 'Player':
                        self.player = game_object

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

        self.group.update(d_t)

    def on_draw(self):
        #self._display_surf.fill((0, 0, 0))
        self.group.center(self.player.rect.center)
        self.group.draw(self._display_surf)


        #for drawable in self.drawables:
        #    drawable.draw(self._display_surf, self.camera)

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
