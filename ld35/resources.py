from pkg_resources import resource_filename
import sys, os

def get(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
        return os.path.join(datadir, *(filename.split('/')))
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)

        return resource_filename('ld35', filename)

