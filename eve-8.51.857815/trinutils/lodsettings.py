#Embedded file name: trinutils\lodsettings.py
"""Module to force-apply LoD view thresholds to trinity settings,
forcing a LoD change for the entire scene.

Use `View(<HIGH|MEDIUM|LOW|DEFAULT>)` to view the appropriate LoD version.

The constants are duples where item 0 is the low detail threshold
and item 1 is the medium detail threshold.

`DEFAULT` is given the medium/low detail thresholds when this module
is first imported, so if modifications have been made to the settings
before import, DEFAULT will just revert it to those settings.

Unfortunately, since lod choice is set by size on screen,
this code is basically untestable.
"""
import sys
import trinity
KEY_LOWDETAIL = 'eveSpaceSceneLowDetailThreshold'
KEY_MEDDETAIL = 'eveSpaceSceneMediumDetailThreshold'
HIGH = (0, 0)
MEDIUM = (0, sys.maxint)
LOW = (sys.maxint, sys.maxint)
_settings = trinity.settings
DEFAULT = (_settings.GetValue(KEY_LOWDETAIL), _settings.GetValue(KEY_MEDDETAIL))

def View(threshold):
    """Sets the current trinity eveSpaceScene settings so the indicated
    LoD is always visible (valid values are the consts on this module)."""
    _settings.SetValue(KEY_LOWDETAIL, threshold[0])
    _settings.SetValue(KEY_MEDDETAIL, threshold[1])
