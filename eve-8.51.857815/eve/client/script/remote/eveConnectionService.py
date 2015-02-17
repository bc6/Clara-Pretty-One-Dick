#Embedded file name: eve/client/script/remote\eveConnectionService.py
"""
Handles connection to the server and login along synchronizing the clock.

Also does application specific stuff related to the connection process. 
The logic of some of these is debatable though :|
"""
import svc

class EveConnectionService(svc.connection):
    """
        This service helps with the plights on network connections
    """
    __guid__ = 'svc.eveConnection'
    __replaceservice__ = 'connection'
    __notifyevents__ = svc.connection.__notifyevents__ + ['OnStationOwnerChanged', 'ProcessSessionChange', 'OnStationInformationUpdated']

    def __init__(self):
        svc.connection.__init__(self)

    def ProcessSessionChange(self, isRemote, session, change):
        """
            If connection service is responsible for passing on station owner changes, 
            it can be responsible for clearing it as well when we leave stations.
        """
        if 'stationid' in change and not session.stationid:
            eve.ClearStationItem()

    def OnStationOwnerChanged(self, ownerID):
        """
            Connection service is responsible for passing on station owner changes
        """
        eve.SetStationItemBits((eve.stationItem.hangarGraphicID,
         ownerID,
         eve.stationItem.itemID,
         eve.stationItem.serviceMask,
         eve.stationItem.stationTypeID))

    def OnStationInformationUpdated(self, stationID):
        """
            As stated above, connection service is responsible for dealing with
            station information changes.
            
            This method is called when a station owner changes information that would invalidate
            the cached station object from GetStation. It does not affect the StationItemBits.
        """
        sm.GetService('objectCaching').InvalidateCachedMethodCall('stationSvc', 'GetStation', stationID)
