#Embedded file name: eve/client/script/util\bubble.py
"""
Utility functions related to Michelle's ballpark. 

They are here so we don't bloat the interface of michelle.Park with stuff that
can be defined in terms of the existing interface.
"""

def SlimItemFromCharID(charID):
    """
    Used to find a ship by pilot charID in bubble.
    """
    bp = sm.GetService('michelle').GetBallpark()
    if bp:
        for item in bp.slimItems.values():
            if item.charID == charID:
                return item


def InBubble(itemID):
    bp = sm.GetService('michelle').GetBallpark()
    if bp:
        return itemID in bp.balls
    else:
        return False


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('util', globals())
