#Embedded file name: yamlext\fsd.py
import fsdCommon.fsdYamlExtensions as fsdYamlExtensions
from . import PyIO
__all__ = ['dumps',
 'dumpfile',
 'dump',
 'loads',
 'loadfile',
 'load']

class _fsdIO(PyIO):

    def __init__(self):
        PyIO.__init__(self)
        self._loader = fsdYamlExtensions.FsdYamlLoader
        self._dumper = fsdYamlExtensions.FsdYamlDumper


def dumps(obj, **kwargs):
    return _fsdIO().dumps(obj, **kwargs)


def dumpfile(obj, path, **kwargs):
    return _fsdIO().dumpfile(obj, path, **kwargs)


def dump(obj, stream, **kwargs):
    return _fsdIO().dump(obj, stream, **kwargs)


def loads(s):
    return _fsdIO().loads(s)


def loadfile(path):
    return _fsdIO().loadfile(path)


def load(stream):
    return _fsdIO().load(stream)
