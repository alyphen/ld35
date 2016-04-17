import pygame
import pyganim

import resources

import logging

logger = logging.getLogger()


class Teleport(pygame.sprite.Sprite):
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

    def on_collision(self, other):
        if hasattr(other, 'teleport_to'):
            # send player to the destination
            other.teleport_to(self.destination)


class Player(pygame.sprite.Sprite):
    @classmethod
    def from_tmx(self, tmx_object):
        player = Player((tmx_object.x, tmx_object.y))
        # player.image = tmx_object.image
        player.id = tmx_object.id

        return player

    def __init__(self, position, movestep=32, speed=200):
        super(Player, self).__init__()
        # self.image = pygame.image.load("examples/placeholder_player.png")

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

            self.destination = self.rect.x + d_x * self.movestep, self.rect.y + d_y * self.movestep

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
            self.animate('idle')

        self.update_animation()

        # keep our feet on the ground
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom

    # This is used to move back from walls
    # Should really be more generic collision response
    def move_back(self, d_t, walls):
        # self.position = self._old_position

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
                self.reset_inputs()
            elif overlap.collidepoint(self.feet.midleft):
                x += overlap.width
                x = self._old_position[0]
                self.reset_inputs()
            elif overlap.collidepoint(self.feet.midbottom):
                y += overlap.height
                y = self._old_position[1]
                self.reset_inputs()
            elif overlap.collidepoint(self.feet.midright):
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


class RisingPlatform(pygame.sprite.Sprite):
    @classmethod
    def from_tmx(cls, tmx_object):
        rising_platform = RisingPlatform((tmx_object.x, tmx_object.y), tmx_object.floor)
        rising_platform.id = tmx_object.id
        return rising_platform

    def __init__(self, position, floor=0):
        super(RisingPlatform, self).__init__()
        self.position = position
        self.floor = floor
        self.height = floor * 32
        self.rect = pygame.Rect(position, (32, 32))
        self.image = pygame.image.load(resources.get("assets/rising_platform.png"))

    def update(self, d_t):
        if self.height > self.floor * 32:
            self.height -= 1
        elif self.height < self.floor * 32:
            self.height += 1

    def on_collision(self, other):
        pass


class Switch(pygame.sprite.Sprite):
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

        self.image = images[0]
        self.pressed_image = images[1]
        self.active = False

    def on_collision(self, other):
        if isinstance(other, Player):
            self.active = True
            self.image = self.pressed_image
