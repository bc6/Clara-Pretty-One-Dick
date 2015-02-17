#Embedded file name: eve/client/script/dogma\clientDogmaIM.py
import service
import dogmax
import util
import uthread

class ClientDogmaInstanceManager(service.Service):
    __guid__ = 'svc.clientDogmaIM'
    __startupdependencies__ = ['clientEffectCompiler', 'invCache', 'godma']
    __notifyevents__ = ['OnSessionChanged', 'ProcessSessionChange', 'DoPrepareShiplessCharacterMove']

    def Run(self, *args):
        service.Service.Run(self, *args)
        self.dogmaLocation = None
        self.nextKey = 0
        self.shipIDBeingActivated = None

    def GetDogmaLocation(self, *args):
        """
            We currently just have one dogmaLocation which is the one where you handle
            the ship you are in. In the future I hope to have more dogmaLocations, at
            least one to handle virtual ships you are not in.
        """
        uthread.Lock('GetDogmaLocation')
        try:
            if self.dogmaLocation is None:
                self.dogmaLocation = dogmax.DogmaLocation(self)
                self.LogInfo('Created client dogmaLocation', id(self.dogmaLocation))
        finally:
            uthread.UnLock('GetDogmaLocation')

        return self.dogmaLocation

    def GodmaItemChanged(self, item, change):
        if item.itemID == session.charid:
            return
        if self.dogmaLocation is not None:
            shipID = self.dogmaLocation.shipID
            if item.locationID in (shipID, session.charid):
                self.dogmaLocation.OnItemChange(item, change)
            elif change.get(const.ixLocationID, None) in (shipID, session.charid):
                self.dogmaLocation.OnItemChange(item, change)
            elif item.itemID == shipID and session.stationid2 is not None:
                if item.locationID != session.stationid or item.flagID != const.flagHangar:
                    if util.IsWorldSpace(item.locationID) or util.IsSolarSystem(item.locationID):
                        self.LogInfo('ActiveShip moved as we are undocking. Ignoring')
                    elif util.IsStation(item.locationID) and item.flagID == const.flagHangar and item.ownerID == session.charid:
                        self.LogInfo("Active ship moved stations but is still in it's hangar", item, change, session.stationid)
                    else:
                        sm.GetService('station').TryLeaveShip(item)
                        self.dogmaLocation.UnboardShip(session.charid)
                        self.LogError('Our active ship got moved', item, change)

    def ProcessSessionChange(self, isRemote, session, change):
        if self.dogmaLocation is None:
            return
        if 'stationid2' in change or 'solarsystemid' in change:
            self.dogmaLocation.UpdateRemoteDogmaLocation()

    def OnSessionChanged(self, isRemote, session, change):
        if 'stationid2' in change:
            self.FinalizeShiplessCharacterMove()

    def GetCapacityForItem(self, itemID, attributeID):
        if self.dogmaLocation is None:
            return
        if not self.dogmaLocation.IsItemLoaded(itemID):
            return
        return self.dogmaLocation.GetAttributeValue(itemID, attributeID)

    def DoPrepareShiplessCharacterMove(self, shipID):
        """
            Called during a session change to a station to ensure that 
            the character starts his station experience in some space craft
            See FinalizeShiplessCharacterMove
        """
        if shipID is not None:
            self.LogInfo('DoPrepareShiplessCharacterMove::Preparing shipID', shipID, 'for boarding')
            self.shipIDBeingActivated = shipID

    def FinalizeShiplessCharacterMove(self):
        """
            Moves the character into his new ship once a session change has been completed.
        """
        if self.shipIDBeingActivated is not None:
            self.LogInfo('FinalizeShiplessCharacterMove::Moving character to shipID ', self.shipIDBeingActivated, ' after session change.')
            self.GetDogmaLocation().MakeShipActive(self.shipIDBeingActivated)
            self.shipIDBeingActivated = None
