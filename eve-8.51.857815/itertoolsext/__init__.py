#Embedded file name: itertoolsext\__init__.py
from brennivin.itertoolsext import *

def get_column(columnid, *rows):
    """Given multiple ``rows``, return the values from ``columnid``."""
    if not rows:
        return
    column_elements = zip(*rows)[columnid]
    return iter(column_elements)
