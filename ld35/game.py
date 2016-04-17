import pygame
from pygame import Rect

from pytmx.util_pygame import load_pygame
import pyscroll
from pyscroll import PyscrollGroup

import resources
import gameobjects

import logging
logger = logging.getLogger()


class Game:
    def __init__(self, filename):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 1280, 720

        self.filename = filename

        self.camera = Rect(0, 0, self.width, self.height)

        self._clock = pygame.time.Clock()
        self.fps = 60

        self.updateables = []
        self.drawables = []

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

        self.teleport_group = pygame.sprite.Group()

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = list()
        destinations = {}  # destinations by destination ID
        waiting_teleports = {}  # lists of teleports by destination ID
        self.all_teleports = []
        self.all_rising_platforms = []

        # Find known object types and attach behavior
        for o in tmx_data.objects:
            if hasattr(gameobjects, o.type):
                klass = getattr(gameobjects, o.type)
                if hasattr(klass, 'from_tmx'):
                    game_object = klass.from_tmx(o)
                    self.group.add(game_object)

                    if o.name == 'Player':
                        self.player = game_object

                    if o.type == 'Teleport':
                        if game_object.destination_id is not None:
                            # hook it up if we can
                            game_object.destination = destinations.get(game_object.destination_id, None)
                            logger.debug('Adding teleport {0} with destination: {1}/{2}'.format(game_object.id,
                                                                                                game_object.destination_id,
                                                                                                game_object.destination))

                            # store it for later if not
                            teleports = waiting_teleports.get(game_object.destination_id, [])
                            teleports.append(game_object)
                            waiting_teleports[game_object.destination_id] = teleports

                            self.all_teleports.append(game_object)

            elif o.type == 'Wall':
                self.walls.append(pygame.Rect(
                    o.x, o.y,
                    o.width, o.height))
            elif o.type == 'TeleportDestination':
                # save teleport destinations for Teleports read later
                dest = Rect(o.x, o.y, o.width, o.height)
                destinations[o.id] = dest

                # Complete any teleports waiting for this destination
                if o.id in waiting_teleports:
                    for t in waiting_teleports[o.id]:
                        t.destination = dest
                        logger.debug('Completing teleport {0} with destination: {1}/{2}'.format(t.id, o.id, dest))
            elif o.type == 'RisingPlatform':
                self.all_rising_platforms.append(
                    Rect(
                        o.x,
                        o.y,
                        o.width,
                        o.height
                    )
                )
            else:
                logger.error('Unrecognized object type: {0}'.format(o.type))

        # for t in self.all_teleports:
        #    self.teleport_group.add(t)

        self.group.center(self.player.rect.center)

        self.camera_shakes = 0
        self.camera_shake_dist = 0

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_collide()
            self.on_draw()
        self.on_cleanup()

    def add_game_object(self, game_object):
        if hasattr(game_object, 'update'):
            self.updateables.append(game_object)

        if hasattr(game_object, 'draw'):
            self.drawables.append(game_object)

    def play_music(self, filename):
        # Ideally we want to load new music when going into a new map.
        # Note: pygame's fadeout is blocking so will have to do setvolume over many updates then load the new clip
        self._musicfile = filename
        pygame.mixer.music.load(resources.get(self._musicfile))
        pygame.mixer.music.play(-1)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._running = False
            if event.key == pygame.K_SPACE:
                self.camera_shake()

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
        # Can use a new group to hold all player sprites if needed
        # for sprite in self.group.sprites():
        collision_list = self.player.feet.collidelistall(self.walls)
        if len(collision_list) > 0:
            wall_list = [self.walls[i] for i in collision_list]
            self.player.move_back(d_t, wall_list)

        # Camera shake
        if self.camera_shakes > 0:
            self.camera_shake_dist = -self.camera_shake_dist
            self.camera_shakes -= 1
        elif self.camera_shakes == 0 and self.camera_shake_dist != 0:
            self.camera_shake_dist = 0

    def on_collide(self):
        for sprite in self.group.sprites():
            # collider = pygame.sprite.spritecollideany(sprite, self.teleport_group)
            teleport_rects = [x.rect for x in self.all_teleports]
            teleport_collision_list = sprite.rect.collidelistall(teleport_rects)
            if len(teleport_collision_list) > 0:
                collider = self.all_teleports[teleport_collision_list[0]]  # Just get the first index
                collider.on_collision(sprite)
            rising_platform_rects = [x.rect for x in self.all_rising_platforms]
            rising_platform_collision_list = sprite.rect.collidelistall(rising_platform_rects)
            if len(rising_platform_collision_list) > 0:
                collider = self.all_rising_platforms[rising_platform_collision_list[0]]
                collider.on_collision(sprite)

    def on_draw(self):
        # self._display_surf.fill((0, 0, 0))

        camera_smooth_factor = 10
        c_pos = self.group.view.center
        c_tgt = self.player.rect.center
        distance_x = c_pos[0] + (c_tgt[0] - c_pos[0]) / camera_smooth_factor
        distance_y = c_pos[1] + (c_tgt[1] - c_pos[1]) / camera_smooth_factor

        self.group.center((distance_x + self.camera_shake_dist, distance_y))

        self.group.draw(self._display_surf)

        for drawable in self.drawables:
            drawable.draw(self._display_surf, self.camera)

        pygame.display.flip()

    def on_cleanup(self):
        pygame.quit()

    def camera_shake(self, shakes=32, dist=4):
        self.camera_shakes = shakes
        self.camera_shake_dist = dist


if __name__ == "__main__":
    game = Game(resources.get('examples/examplemap.tmx'))
