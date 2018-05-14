from .measurement import REGISTRY

from importlib import import_module
import os
paths = [x for x in os.listdir('./meas') if x.endswith('py') and x != '__init__.py' and x != 'measurement.py']

for path in paths:
    print('importing meas.{}'.format(path[:-3]))
    import_module('meas.{}'.format(path[:-3]))