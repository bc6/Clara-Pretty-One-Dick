#Embedded file name: whitelistpickle\__init__.py
"""
Code to make `cPickle`'s `load` and `loads`
functions work with a whitelist.
We do this by overriding the cPickle.Unpickler method.

Some notes:

- The original, unmolested unpickler is available on `cPickleUnpickler`.
- The default whitelist is `blue.marshal.globalsWhitelist`.
- Call `patch_cPickle` to patch the actual `cPickle` module.
- Only old-style classes can be unpickled because `copy_reg._reconstructor`
  is not part of the whitelist.
"""
import cPickle
import cStringIO
try:
    import blue
except ImportError:
    blue = None

cPickleUnpickler = cPickle.Unpickler

def get_whitelist():
    return blue.marshal.globalsWhitelist


def find_global(moduleName, className, getwhitelist = None):
    fromlist = []
    if '.' in moduleName:
        fromlist.append(moduleName[moduleName.index('.'):])
    mod = __import__(moduleName, globals(), locals(), fromlist)
    obj = getattr(mod, className)
    if obj in (getwhitelist or get_whitelist)():
        return obj
    raise cPickle.UnpicklingError('%s.%s not in whitelist' % (moduleName, className))


def Unpickler(file):
    u = cPickleUnpickler(file)
    u.find_global = find_global
    return u


def load(fileObj):
    return cPickle.Unpickler(fileObj).load()


def loads(blob):
    return load(cStringIO.StringIO(blob))


def patch_cPickle():
    cPickle.Unpickler = Unpickler
    cPickle.load = load
    cPickle.loads = loads
