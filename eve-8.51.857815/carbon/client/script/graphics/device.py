#Embedded file name: carbon/client/script/graphics\device.py
"""
Provide functions to deal with texture quality settings for characters and environments
"""
import trinity

def SetEnvMipLevelSkipCount():
    trinity.device.mipLevelSkipCount = 0


def SetCharMipLevelSkipCount():
    trinity.device.mipLevelSkipCount = 0


exports = {'device.SetEnvMipLevelSkipCount': SetEnvMipLevelSkipCount,
 'device.SetCharMipLevelSkipCount': SetCharMipLevelSkipCount}
