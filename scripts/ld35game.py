#!/usr/bin/env python
import ld35

if __name__ == "__main__":
    game = ld35.game.Game(ld35.resources.get('examples/examplemap.tmx'))
    game.run()
