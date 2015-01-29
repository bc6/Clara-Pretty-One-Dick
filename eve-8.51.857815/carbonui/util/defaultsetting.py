#Embedded file name: carbonui/util\defaultsetting.py
"""

    Author:     Fridrik Haraldsson
    Created:    September 2008
    Project:    Core


    Description:

    This file holds default setting values for the uicore. Similar file should be
    done in the gameroot to assing default settings for the game. This is done to prevent 
    different defaultvalues in various classes where the setting is being used.

    If you think the setting you are working with doesn't require registered 
    default value then do;

    myval = settings.sectionName.groupName.Get(settingKey, myDefaultValue)

    (c) CCP 2008

"""
from itertoolsext import Bundle

class SafeBundle(Bundle):

    def __getattr__(self, item):
        try:
            return Bundle.__getattr__(self, item)
        except (KeyError, AttributeError):
            return None


user = SafeBundle(ui=SafeBundle(language=0))
user.__name__ = 'user'
public = SafeBundle(device=SafeBundle(ditherbackbuffer=1))
public.__name__ = 'public'
char = SafeBundle()
char.__name__ = 'char'
exports = {'defaultsetting.user': user,
 'defaultsetting.public': public,
 'defaultsetting.char': char}
