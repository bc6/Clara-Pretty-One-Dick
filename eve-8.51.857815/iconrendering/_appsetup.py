#Embedded file name: iconrendering\_appsetup.py
"""Import this in your test packages to append packages to the sys path."""
import os
import sys
import site
pkgspath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
site.addsitedir(pkgspath)
rootpath = os.path.abspath(os.path.join(pkgspath, '..'))
if rootpath not in sys.path:
    sys.path.append(rootpath)
import binbootstrapper
binbootstrapper.update_binaries(__file__, *binbootstrapper.DLLS_GRAPHICS)
import trinity
from binbootstrapper.trinityapp import create_windowless_device

def CreateTrinityApp():
    create_windowless_device()
    trinity.device.animationTimeScale = 0.0
