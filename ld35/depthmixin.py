from pyscroll import PyscrollGroup

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

        for spr in self.sprites():
            new_rect = spr.rect.move(ox, oy - getattr(spr, 'z', 0))
            try:
                new_surfaces_append((spr.image, new_rect, gl(spr), spr.blendmode))
            except AttributeError:  # generally should only fail when no blendmode available
                new_surfaces_append((spr.image, new_rect, gl(spr)))
            spritedict[spr] = new_rect

        return self._map_layer.draw(surface, surface.get_rect(), new_surfaces)
