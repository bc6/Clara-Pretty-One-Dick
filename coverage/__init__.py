#Embedded file name: coverage\__init__.py
"""Code coverage measurement for Python.

Ned Batchelder
http://nedbatchelder.com/code/coverage

"""
from coverage.version import __version__, __url__
from coverage.control import coverage, process_startup
from coverage.data import CoverageData
from coverage.cmdline import main, CoverageScript
from coverage.misc import CoverageException
_the_coverage = None

def _singleton_method(name):
    """Return a function to the `name` method on a singleton `coverage` object.
    
    The singleton object is created the first time one of these functions is
    called.
    
    """

    def wrapper(*args, **kwargs):
        """Singleton wrapper around a coverage method."""
        global _the_coverage
        if not _the_coverage:
            _the_coverage = coverage(auto_data=True)
        return getattr(_the_coverage, name)(*args, **kwargs)

    import inspect
    meth = getattr(coverage, name)
    args, varargs, kw, defaults = inspect.getargspec(meth)
    argspec = inspect.formatargspec(args[1:], varargs, kw, defaults)
    docstring = meth.__doc__
    wrapper.__doc__ = '        A first-use-singleton wrapper around coverage.%(name)s.\n\n        This wrapper is provided for backward compatibility with legacy code.\n        New code should use coverage.%(name)s directly.\n\n        %(name)s%(argspec)s:\n\n        %(docstring)s\n        ' % locals()
    return wrapper


use_cache = _singleton_method('use_cache')
start = _singleton_method('start')
stop = _singleton_method('stop')
erase = _singleton_method('erase')
exclude = _singleton_method('exclude')
analysis = _singleton_method('analysis')
analysis2 = _singleton_method('analysis2')
report = _singleton_method('report')
annotate = _singleton_method('annotate')
import encodings.utf_8
import sys
try:
    del sys.modules['coverage.coverage']
except KeyError:
    pass
