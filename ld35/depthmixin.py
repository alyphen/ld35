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
    pass
