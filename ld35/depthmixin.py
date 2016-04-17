from pyscroll import PyscrollGroup

class DepthMixin(object):
    '''A mixin for pygame.sprite.Group objects that sorts sprites during update according to z.'''
    def __init__(self, *args, **kwargs):
        super(DepthMixin, self).__init__(*args, **kwargs)

    def update(self, *args, **kwargs):
        def combine_z(s):
            return s.rect.center[1] | getattr(s, 'z', 0) << 8

        self._spritelist.sort(lambda l, r: combine_z(l) - combine_z(r))
        super(DepthMixin, self).update(*args, **kwargs)

class DepthOrderedScrollGroup(DepthMixin, PyscrollGroup):
    pass
