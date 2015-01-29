#Embedded file name: trinutils\searchpath.py
import contextlib
import blue

@contextlib.contextmanager
def change_search_path_ctx(value, key = 'res'):
    """Context manager for temporarily changing a search path."""

    def get_search_path():
        return blue.paths.GetSearchPath(key)

    def set_search_path(value_):
        blue.paths.SetSearchPath(key, unicode(value_))

    orig = get_search_path()
    set_search_path(value)
    try:
        yield
    finally:
        if orig is not None:
            set_search_path(orig)
