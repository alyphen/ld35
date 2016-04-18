import pygame
import pyganim

import resources

import logging

logger = logging.getLogger()


def floor_for_z(z):
    return int(z / 32)

def z_for_floor(floor):
    return floor * 32

class TriggerMixin(object):
    def __init__(self, *args, **kwargs):
        super(TriggerMixin, self).__init__(*args, **kwargs)

        self.collisions_last_frame = set()
        self.active_collisions = set()

    def update(self, *args, **kwargs):
        super(TriggerMixin, self).update(*args, **kwargs)

        # find collisions not in last frame and do on_exit
        exiting = self.active_collisions - self.collisions_last_frame
        for c in exiting:
            if hasattr(self, 'on_exit'):
                self.on_exit(c)
            self.active_collisions.remove(c)

        # reset detection for this frame
        self.collisions_last_frame.clear()

    def on_collision(self, other):
        if other is self:
            return

        track = True
        # find new collisions and do on_enter
        # if on_enter returns False then do not track the other
        if hasattr(self, 'on_enter') and other not in self.active_collisions:
            track = self.on_enter(other)

        if track is None:
            track = True

        # track this collision for on_enter/on_exit
        if track:
            self.collisions_last_frame.add(other)
            self.active_collisions.add(other)


class Teleport(TriggerMixin, pygame.sprite.Sprite):
    @classmethod
    def from_tmx(cls, tmx_object):
        r = pygame.Rect(
            tmx_object.x,
            tmx_object.y,
            tmx_object.width,
            tmx_object.height
        )
        teleport = Teleport(r)
        teleport.id = tmx_object.id
        teleport.destination_id = int(tmx_object.properties.get('destination'))
        return teleport

    def __init__(self, rect):
        super(Teleport, self).__init__()
        self.rect = rect
        self.image = pygame.image.load("examples/placeholder_player.png")
        # self.rect = self.image.get_rect()
        # self.rect.center = self.position

        self.destination = None

    def on_enter(self, other):
        if hasattr(other, 'teleport_to'):
            # send player to the destination
            other.teleport_to(self.destination)


class Player(pygame.sprite.Sprite):
    # how many layers are displayed per floor?
    layers_per_floor = 3
    # out of the x layers per floor, which one does this go on?
    layer_floor_offset = 2

    _z = 0

    @classmethod
    def from_tmx(self, tmx_object):
        player = Player((tmx_object.x, tmx_object.y))
        # player.image = tmx_object.image
        player.id = tmx_object.id

        return player

    @property
    def z(self):
        return self._z

    @z.setter
    def z(self, value):
        floor = self.floor

        self._z = value

        if floor != self.floor:
            self.on_floor_change()

    @property
    def floor(self):
        return int(self.z / 32)

    @floor.setter
    def floor(self, value):
        # this resets z to be on the floor.
        # perhaps it should instead map z into the floor
        # e.g. if z = 36 (on floor 1) map it to z = 4 (on floor 0)
        self.z = value * 32

    @property
    def layer(self):
        '''Returns layer number assuming there are 2 layers per floor.'''
        return self.floor * self.layers_per_floor + self.layer_floor_offset

    @layer.setter
    def layer(self, value):
        self.floor = int((value - self.layer_floor_offset) / self.layers_per_floor)

    @property
    def hitbox(self):
        r = self.rect
        return r.inflate(-r.width / 2, -r.height / 2)

    def on_floor_change(self):
        for listener in self._floor_listeners:
            listener(self)

    def __init__(self, position, movestep=16, speed=200):
        super(Player, self).__init__()
        # self.image = pygame.image.load("examples/placeholder_player.png")

        self._floor_listeners = set()

        self.layer = 1
        self._z = 0

        self.build_animations()
        self.update_animation()

        self.feet = pygame.Rect(0, 0, self.rect.width * 1.0, 10)

        self.reset_inputs()

        self.movestep = movestep
        self.speed = speed
        self.destination = self.position = position
        self._old_position = self.position

        self.velocity = (0, 0)

        self._snd_step_concrete = pygame.mixer.Sound(resources.get("assets/step_concrete.wav"))
        self._snd_step_grass = pygame.mixer.Sound(resources.get("assets/step_grass.wav"))
        self._snd_step_water = pygame.mixer.Sound(resources.get("assets/step_water.wav"))

    def add_floor_listener(self, listener):
        '''Adds a callable to be called when this object's floor changes.'''
        self._floor_listeners.add(listener)

    def remove_floor_listener(self, listener):
        '''Removes the given floor listener.'''
        self._floor_listeners.remove(listener)

    def build_animations(self):
        images = pyganim.getImagesFromSpriteSheet(
            resources.get('examples/placeholder_player_ani.png'),
            rows=4, cols=3, rects=[])

        self.animations = {
            'idle_up': [(images[0], 100)],
            'idle_down': [(images[3], 100)],
            'idle_left': [(images[6], 100)],
            'idle_right': [(images[9], 100)],

            'walk_up': zip([images[x] for x in [1, 0, 2, 0]], [200] * 4),
            'walk_down': zip([images[x] for x in [4, 3, 5, 3]], [200] * 4),
            'walk_left': zip([images[x] for x in [7, 6, 8, 6]], [200] * 4),
            'walk_right': zip([images[x] for x in [10, 9, 11, 9]], [200] * 4),
        }

        self.idle_transitions = {
            'walk_up': 'idle_up',
            'walk_down': 'idle_down',
            'walk_left': 'idle_left',
            'walk_right': 'idle_right',
        }

        for k, v in self.animations.items():
            self.animations[k] = pyganim.PygAnimation(list(v))

        self.animate('idle_up')

    def animate(self, name):
        if name == 'idle':
            name = self.idle_transitions.get(self.active_anim, 'idle_down')
            logger.debug('transition from {0} to {1}'.format(self.active_anim, name))

        self.animations[name].play()
        self.active_anim = name

    def update_animation(self):
        self.image = self.animations[self.active_anim].getCurrentFrame()
        self.rect = self.image.get_rect()

    def reset_inputs(self):
        self.k_left = 0
        self.k_right = 0
        self.k_up = 0
        self.k_down = 0

    @property
    def has_input(self):
        return sum((self.k_left, self.k_right, self.k_up, self.k_down)) != 0

    def on_event(self, event):
        down = event.type == pygame.KEYDOWN
        if not hasattr(event, 'key'):
            return

        if event.key == pygame.K_LEFT:
            self.k_left = down * -1
        if event.key == pygame.K_RIGHT:
            self.k_right = down * 1
        if event.key == pygame.K_UP:
            self.k_up = down * -1
        if event.key == pygame.K_DOWN:
            self.k_down = down * 1

    def update(self, d_t):
        self._old_position = self.position

        d_t /= 1000.0
        x, y = self.position

        if self.velocity == (0, 0):
            d_x = (self.k_left + self.k_right)

            # only find d_y if there is no horizontal movement
            d_y = 0
            if d_x == 0:
                d_y = (self.k_up + self.k_down)
            self.velocity = (d_x, d_y)

            d = self.rect.x + d_x * self.movestep, self.rect.y + d_y * self.movestep
            # round/quantize destination to movestep
            l = lambda x: ((x + 8) / self.movestep) * self.movestep
            self.destination = (l(d[0]), l(d[1]))

            if d_x < 0:
                self.animate('walk_left')
            elif d_x > 0:
                self.animate('walk_right')
            elif d_y < 0:
                self.animate('walk_up')
            elif d_y > 0:
                self.animate('walk_down')
                # No else: 'idle' because it would reset every idle frame

        distance_x = abs(self.destination[0] - self.position[0])
        distance_y = abs(self.destination[1] - self.position[1])

        # print('distance: {0}, {1}, position: {2}, destination: {3}'
        # .format(distance_x, distance_y, self.position, self.destination))

        d_x = self.velocity[0] * min(d_t * self.speed, distance_x)
        d_y = self.velocity[1] * min(d_t * self.speed, distance_y)

        if d_x != 0 or d_y != 0:
            if not pygame.mixer.get_busy():
                self._snd_step_grass.play()

        # print('d_x: {0},    d_y: {1}'.format(d_x, d_y))

        x += d_x
        y += d_y
        self.position = (int(x), int(y))

        if self.position == self.destination and self.velocity != (0, 0):
            self.velocity = (0, 0)
            if not self.has_input:
                self.animate('idle')

        self.update_animation()

        # keep our feet on the ground
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom

    # This is used to move back from walls
    # Should really be more generic collision response
    def move_back(self, walls):
        # self.position = self._old_position

        for wall in walls:
            # find region
            overlap = self.rect.clip(wall)

            # compensate for collidepoint not detecting edges
            overlap.height += 1
            overlap.width += 1

            x, y = self.position

            if overlap.collidepoint(self.rect.midtop):
                y -= overlap.height
                y = self._old_position[1]
                self.reset_inputs()
            elif overlap.collidepoint(self.rect.midleft):
                x += overlap.width
                x = self._old_position[0]
                self.reset_inputs()
            elif overlap.collidepoint(self.rect.midbottom):
                y += overlap.height
                y = self._old_position[1]
                self.reset_inputs()
            elif overlap.collidepoint(self.rect.midright):
                x -= overlap.width
                x = self._old_position[0]
                self.reset_inputs()

            self.position = (int(x), int(y))
            self.destination = self.position

        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom

    def teleport_to(self, destination):
        # move us to the new spot
        self.rect.clamp_ip(destination)
        self.position = self.rect.topleft

        # and reset input
        self.reset_inputs()


class RisingPlatform(TriggerMixin, pygame.sprite.Sprite):
    @classmethod
    def from_tmx(cls, tmx_object):
        platform = RisingPlatform((tmx_object.x, tmx_object.y), int(tmx_object.floor))
        platform.id = tmx_object.id
        return platform

    def __init__(self, position, floor=0):
        super(RisingPlatform, self).__init__()
        self.position = position
        self.floor = floor
        self.height = floor * 32
        self.rect = pygame.Rect((position[0] - 8, position[1] - 8), (32, 32))
        self.rect = pygame.Rect((position[0], position[1]), (32, 32))
        self.image = pygame.image.load(resources.get("examples/platformgrass.png"))
        self.image_offset = (-8, -8)

    @property
    def rising(self):
        return self.height < self.floor * 32

    @property
    def falling(self):
        return self.height > self.floor * 32

    @property
    def stopped(self):
        return not (self.rising or self.falling)

    def update(self, d_t):
        super(RisingPlatform, self).update(d_t)

        if self.falling:
            self.height -= 1
        elif self.rising:
            self.height += 1

        self.z = self.height

        # anything touching (contained? half contained?) the platform should be moved as well
        for game_object in self.active_collisions:
            game_object.z = self.z


    def on_enter(self, other):
        if not isinstance(other, Player):
            return
        logger.info('{other} entered {self}'.format(other=other, self=self))
        logger.info('\t\t{0}, {1} =?= {2}'.format(self.stopped, self.floor, other.floor))
        if not self.stopped or self.floor != other.floor:
            logger.info('\t\tmove_back()!  removing from active collisions')
            other.move_back([self.rect])
            return False # Explicitly do not track this object.  (Prevents on_trigger)

        if hasattr(self, 'target') and hasattr(self.target, 'on_trigger'):
            self.target.on_trigger(self)

        return True

    def on_exit(self, other):
        logger.info('{other} exited {self}'.format(other=other, self=self))
        if not self.stopped:
            # Prevent the player from leaving the platform until the movement is done
            pass

    def on_trigger(self, other):
        if self.stopped:
            if self.floor == 0:
                self.floor = 1
            else:
                self.floor = 0


class FallingPlatform(RisingPlatform):
    @classmethod
    def from_tmx(cls, tmx_object):
        platform = FallingPlatform((tmx_object.x, tmx_object.y), int(tmx_object.floor))
        platform.id = tmx_object.id
        return platform

    def __init__(self, *args, **kwargs):
        floor = kwargs.pop('floor', 1)
        kwargs['floor'] = floor

        super(FallingPlatform, self).__init__(self, *args, **kwargs)

    def on_enter(self, other):
        if not self.stopped or self.floor != other.floor:
            other.move_back([self.rect])

        if isinstance(other, Player):
            if self.stopped and self.floor == 1:
                self.floor = 0


class RisingFallingPlatform(RisingPlatform):
    @classmethod
    def from_tmx(cls, tmx_object):
        platform = RisingFallingPlatform((tmx_object.x, tmx_object.y), int(tmx_object.floor))
        platform.id = tmx_object.id
        return platform

    def __init__(self, *args, **kwargs):
        super(RisingFallingPlatform, self).__init__(*args, **kwargs)

    def on_enter(self, other):
        if not self.stopped or self.floor != other.floor:
            other.move_back([self.rect])

        if isinstance(other, Player):
            if self.stopped:
                if self.floor == 1:
                    self.floor = 0
                elif self.floor == 0:
                    self.floor = 1


class Switch(TriggerMixin, pygame.sprite.Sprite):
    @classmethod
    def from_tmx(cls, tmx_object):
        rect = pygame.Rect(
            tmx_object.x,
            tmx_object.y,
            tmx_object.width,
            tmx_object.height
        )
        switch = Switch(rect)
        switch.id = tmx_object.id
        return switch

    def __init__(self, rect):
        super(Switch, self).__init__()
        self.rect = rect
        images = pyganim.getImagesFromSpriteSheet(
            resources.get("assets/stonepad.png"),
            rows=1, cols=2, rects=[])
        self._sound = pygame.mixer.Sound("assets/step_concrete.wav")

        self.image = images[0]
        self.released_image = images[0]
        self.pressed_image = images[1]
        self.active = False

    def on_enter(self, other):
        if isinstance(other, Player) and getattr(self, 'floor', 0) == other.floor:
            if not self.active:
                self._sound.play()
            self.active = True
            self.image = self.pressed_image

            if hasattr(self, 'target') and hasattr(self.target, 'on_trigger'):
                self.target.on_trigger(self)

    def on_exit(self, other):
        if self.active:
            self.active = False
            self.image = self.released_image


class Keystone(TriggerMixin, pygame.sprite.Sprite):
    @classmethod
    def from_tmx(cls, tmx_object):
        rect = pygame.Rect(
            tmx_object.x,
            tmx_object.y,
            tmx_object.width,
            tmx_object.height
        )
        keystone = Keystone(rect)
        keystone.id = tmx_object.id
        return keystone

    def __init__(self, rect):
        super(Keystone, self).__init__()
        self.rect = rect
        self.images = pyganim.getImagesFromSpriteSheet(resources.get('examples/keystone.png'),
            rows=1, cols=5, rects=[])
        self.animation = pyganim.PygAnimation(zip([self.images[x] for x in [0, 1, 2, 3, 4, 3, 2, 1]], [200] * 8))
        self.animate()
        self.image = self.images[0]

    def animate(self):
        self.animation.play()

    def on_enter(self, other):
        if isinstance(other, Player):
            # Win
            print("Win")

    def update(self, dt):
        self.image = self.animation.getCurrentFrame()
