#Embedded file name: eve/client/script/parklife\spewContainerManager.py
"""
This module contains the implementation of the spew container manager.
"""

class SpewContainerManager(object):
    """
    This used to be the take manager for mini containers but they have been removed.
    
    This management of animation state for spew containers is all that remains.
    """
    __guid__ = 'spewContainerManager.SpewContainerManager'
    __notifyevents__ = ['OnSlimItemChange']

    def __init__(self, park):
        self.ballpark = park
        sm.RegisterNotify(self)

    def OnSlimItemChange(self, oldSlim, newSlim):
        slimItem = newSlim
        itemID = newSlim.itemID
        if slimItem.groupID in (const.groupSpewContainer, const.groupSpawnContainer) and slimItem.hackingSecurityState is not None:
            sm.GetService('invCache').InvalidateLocationCache(itemID)
            self.OnSpewSecurityStateChange(itemID, slimItem.hackingSecurityState)

    def GetSpewContainer(self, spewContainerID):
        """
        Returns a SpewContainer ball or None if we don't have a ballpark or a ball
        for the SpewContainer.
        """
        spewContainer = None
        if self.ballpark:
            spewContainer = self.ballpark.GetBall(spewContainerID)
        return spewContainer

    def OnSpewSecurityStateChange(self, spewContainerID, securityState):
        spewContainer = self.GetSpewContainer(spewContainerID)
        if spewContainer:
            try:
                spewContainer.SetSecurityState(securityState)
            except AttributeError:
                pass
