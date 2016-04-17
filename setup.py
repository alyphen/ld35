import os
from setuptools import setup

setup(
    name = "ld35",
    version = "0.0.1.dev0",
    url = "https://github.com/seventhroot/ld35",
    author = 'Seventh Root',
    description = 'The Seventh Root entry for Ludum Dare 35',
    long_description_markdown_filename='README.md',
    packages = ['ld35'],
    package_data = {'ld35': [
        'assets/*.ogg',
        'assets/*.wav',
        'assets/*.png',
        'assets/*.tmx',
        'examples/*.png',
        'examples/*.tmx',
    ]},
    setup_requires=['setuptools-markdown'],
    install_requires = [
        'pygame==1.9.1',
        'Pyganim==0.9.2',
        'pyscroll==2.16.6',
        'PyTMX==3.20.14',
        'six==1.10.0',
    ],
    scripts = ['scripts/ld35game.py'],

    # this is to compensate for pytmx.
    # better solution may be to give it a suitable resource loader
    zip_safe = False,
)
