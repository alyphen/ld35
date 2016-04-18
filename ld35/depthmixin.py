from pyscroll import PyscrollGroup
import pygame

class DepthMixin(object):
    '''A mixin for pygame.sprite.Group objects that sorts sprites during update
    according to z.'''
    def __init__(self, *args, **kwargs):
        super(DepthMixin, self).__init__(*args, **kwargs)

    def update(self, *args, **kwargs):
        super(DepthMixin, self).update(*args, **kwargs)

        def spr_idx(s):
            idx = getattr(s, 'index', lambda s: s.rect.center[1] + (getattr(s, 'h', 0) +
                                                                    getattr(s, 'z', 0) << 8))
            return idx(s)

        self._spritelist.sort(lambda l, r: spr_idx(l) - spr_idx(r))

class DepthOrderedScrollGroup(DepthMixin, PyscrollGroup):
    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        super(DepthOrderedScrollGroup, self).__init__(*args, **kwargs)

    # note: copied from pyscroll and modified for z drawing
    def draw(self, surface):
        """ Draw all sprites and map onto the surface

        :param surface: pygame surface to draw to
        """
        ox, oy = self._map_layer.get_center_offset()

        new_surfaces = list()
        spritedict = self.spritedict
        gl = self.get_layer_of_sprite
        new_surfaces_append = new_surfaces.append

        debug_rects = []

        for spr in self.sprites():
            new_rect = spr.rect.move(ox, oy - getattr(spr, 'z', 0))
            if self.debug:
                debug_rects.append(new_rect)
                if hasattr(spr, 'hitbox'):
                    debug_rects.append(spr.hitbox.move(ox, oy - getattr(spr, 'z', 0)))

            if hasattr(spr, 'image_offset'):
                # not move_ip because we need debug_rect to remain un-moved
                new_rect = new_rect.move(spr.image_offset)

            try:
                new_surfaces_append((spr.image, new_rect, gl(spr), spr.blendmode))
            except AttributeError:  # generally should only fail when no blendmode available
                new_surfaces_append((spr.image, new_rect, gl(spr)))
            spritedict[spr] = new_rect

        ret = self._map_layer.draw(surface, surface.get_rect(), new_surfaces)

        # debug
        if self.debug:
            zoom = self._map_layer._zoom_level
            for r in debug_rects:
                r.x *= zoom
                r.y *= zoom
                r.width *= zoom
                r.height *= zoom
                pygame.draw.rect(surface, (200, 100, 100), r, 1)

        return ret
