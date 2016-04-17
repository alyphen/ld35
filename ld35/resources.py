from pkg_resources import resource_filename

def get(filename):
    return resource_filename('ld35', filename)
