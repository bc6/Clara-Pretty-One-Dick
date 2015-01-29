#Embedded file name: eve/common/script/util\leftToRightHanded.py
"""
Contains functions for converting positions and rotations from left and right handed
"""

def ConvertSpherical(latitude, longitude):
    return (latitude, -longitude)


exports = {'lh2rhUtil.ConvertSpherical': ConvertSpherical}
