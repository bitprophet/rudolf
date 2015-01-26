#!/usr/bin/env python

from setuptools import setup

setup(
    name="rudolf",
    version="0.3",
    download_url = "http://pypi.python.org/pypi/rudolf/",

    description = "Colour output plugin for the nose testing framework",
    author = "John J. Lee",
    author_email = "jjl@pobox.com",
    license = "ZPL 2.1",
    platforms = ["POSIX"],

    install_requires = ["nose>=0.1.0"],

    url = "http://pypi.python.org/pypi/rudolf/",

    long_description = """Colour output plugin for the nose testing framework.

Only works on Unix-like systems (uses ANSI colour codes).

Use ``nosetests --with-color`` (no "u"!) to turn it on.

http://en.wikipedia.org/wiki/Rudolph_the_Red-Nosed_Reindeer

"Rudolph the Red-Nosed Reindeer" is a popular Christmas story about Santa
Claus' ninth and lead reindeer who possesses an unusually red colored nose that
gives off its own light that is powerful enough to illuminate the team's path
through inclement weather.
""",

    py_modules = ["rudolf"],
    entry_points = {
        "nose.plugins.0.10": ["color = rudolf:ColorOutputPlugin"]
        },
    zip_safe = True,
)
