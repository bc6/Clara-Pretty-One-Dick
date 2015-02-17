#Embedded file name: eve/common/script/net\eveMachoNetVersion.py
"""
Separating the machoVersion from the rest due to its frequent updates (moved from machoNet.py)
"""
machoVersion = 407
version = machoVersion
exports = {'macho.version': machoVersion}
