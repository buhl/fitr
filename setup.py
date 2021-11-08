# -*- coding: utf-8 -*-
from os.path import dirname, join
from contextlib import contextmanager

from setuptools import setup, find_packages



@contextmanager
def read(filepath, *args, default=None):
    file = join(dirname(__file__), filepath)
    try:
        yield open(file, *args).read()
    except (FileNotFoundError, IOError) as exc:
        if default is not None:
            yield default
        else:
            raise exc


pkginfo = __import__("src.fitr.__pkginfo__", {}, {}, ["__pkginfo__"])

setup_dict = {
    "name": pkginfo.name.lower(),
    "version": ".".join(map(str, pkginfo.version)),
    "description": pkginfo.__doc__,
    'package_dir': {'': 'src'},
    'packages': find_packages('./src'),
    'entry_points': {
        'console_scripts': [
            'FitR =  fitr.cli:run',
            'LFitR =  fitr.lazy:run',
        ],
    },
}

if hasattr(pkginfo, "licens"):
    setup_dict["licens"] = pkginfo.licens

with read("requirements.txt", "r", default="") as content:
    if content:
        setup_dict["install_requires"] = [r.strip() for r in content.split("\n") if r.strip()]

with read("README", "r", default="") as content:
    if content:
        setup_dict["long_description"] = content


if __name__ == '__main__':
    setup(**setup_dict)

