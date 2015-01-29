#Embedded file name: watchdog/utils\unicode_paths.py
import sys
from watchdog.utils import platform
try:
    str_cls = unicode
    bytes_cls = str
except NameError:
    str_cls = str
    bytes_cls = bytes

fs_encoding = sys.getfilesystemencoding()
fs_fallback_encoding = 'utf-8'

def encode(path):
    if isinstance(path, str_cls):
        try:
            path = path.encode(fs_encoding, 'strict')
        except UnicodeEncodeError:
            if not platform.is_linux():
                raise
            path = path.encode(fs_fallback_encoding, 'strict')

    return path


def decode(path):
    if isinstance(path, bytes_cls):
        try:
            path = path.decode(fs_encoding, 'strict')
        except UnicodeDecodeError:
            if not platform.is_linux():
                raise
            path = path.decode(fs_fallback_encoding, 'strict')

    return path
