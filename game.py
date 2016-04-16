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
    def __init__(self, filename):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1280, 720

        self.filename = filename

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

    def play_music(self, filename):
        # Ideally we want to load new music when going into a new map.
        # Note: pygame's fadeout is blocking so will have to do setvolume over many updates then load the new clip
        self._musicfile = filename
        pygame.mixer.music.load(self._musicfile)
        pygame.mixer.music.play(-1)

    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self._running = True

        # Load map data
        tmx_data = load_pygame(self.filename)

        pygame.mixer.init()
        musicfile = tmx_data.properties.get('music')
        if musicfile:
            self.play_music(musicfile)

        map_data = pyscroll.data.TiledMapData(tmx_data)
        self.map_layer = pyscroll.BufferedRenderer(map_data, self._display_surf.get_size())
        self.map_layer.zoom = 4
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)
        # really the group can be added as a gameobject


        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = list()

        # Find known object types and attach behavior
        for o in tmx_data.objects:
            if hasattr(gameobjects, o.type):
                klass = getattr(gameobjects, o.type)
                if hasattr(klass, 'from_tmx'):
                    game_object = klass.from_tmx(o)
                    self.group.add(game_object)

                    if o.name == 'Player':
                        self.player = game_object
            elif o.type == 'Wall':
                self.walls.append(pygame.Rect(
                    o.x, o.y,
                    o.width, o.height))
            else:
                print('Unrecognized object type: {0}'.format(o.type))

        self.group.center(self.player.rect.center)

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
            updateable.update(d_t)

        self.camera.center = self.player.position

        self.group.update(d_t)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        for sprite in self.group.sprites():
            collision_list = sprite.feet.collidelistall(self.walls)
            if len(collision_list) > 0:
                wall_list = [self.walls[i] for i in collision_list]
                sprite.move_back(d_t, wall_list)

    def on_draw(self):
        #self._display_surf.fill((0, 0, 0))

        camera_smooth_factor = 10
        c_pos = self.group.view.center
        c_tgt = self.player.rect.center
        distance_x = c_pos[0] + (c_tgt[0] - c_pos[0]) / camera_smooth_factor
        distance_y = c_pos[1] + (c_tgt[1] - c_pos[1]) / camera_smooth_factor

        self.group.center((distance_x, distance_y))

        self.group.draw(self._display_surf)

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
    game = Game('examples/examplemap.tmx')
    game.on_execute()
