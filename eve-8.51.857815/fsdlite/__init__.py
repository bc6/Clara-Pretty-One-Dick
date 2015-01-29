#Embedded file name: fsdlite\__init__.py
"""
    Authors:   Cameron Royal
    Created:   April 2014
    Project:   EVE

    The fsdlite package is a standalone serialization library designed to work
    with the EVE staticdata YAML format for files. It reads in the raw data and
    serializes it into a sqlite database for memory efficient access. It also
    helps with constructing python objects from the data and automatic indexing.
"""
try:
    from _fsdlite import dump, load, encode, decode, strip
except:
    from .encoder import dump, load, encode, decode, strip

from .util import repr, Immutable, WeakMethod, extend_class, Extendable
from .monitor import start_file_monitor, stop_file_monitor
from .indexer import index
from .cache import Cache
from .signal import Signal
from .storage import Storage, WeakStorage
