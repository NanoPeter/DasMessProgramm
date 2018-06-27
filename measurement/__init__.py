from .measurement import REGISTRY

from importlib import import_module
import os

directory = __file__[:-len('__init__.py')]

paths = [x for x in os.listdir(directory) if x.endswith('py') and x != '__init__.py' and x != 'measurement.py']

for path in paths:
    print('importing measurement.{}'.format(path[:-3]))
    import_module('measurement.{}'.format(path[:-3]))