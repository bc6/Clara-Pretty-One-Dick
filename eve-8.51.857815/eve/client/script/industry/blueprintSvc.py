#Embedded file name: eve/client/script/industry\blueprintSvc.py
import blue
import util
import const
import service
import telemetry
import industry
from eve.common.script.util import industryCommon
import eve.client.script.industry.mixins

class BlueprintService(service.Service):
    """
    Responsible for loading and caching blueprint data on the client, merging static data
    available in FSD and per instance data based on inventory items.
    """
    __guid__ = 'svc.blueprintSvc'
    __servicename__ = 'Blueprint'
    __displayname__ = 'Blueprint Service'
    __notifyevents__ = ['OnBlueprintsUpdated', 'OnSessionChanged', 'OnIndustryJob']

    def Run(self, *args, **kwargs):
        service.Service.Run(self, *args, **kwargs)
        self.blueprintManager = sm.RemoteSvc('blueprintManager')

    def OnBlueprintsUpdated(self, ownerID):
        """
        Callback from the blueprint storage whenever static blueprint data is updated.
        """
        objectCaching = sm.GetService('objectCaching')
        keys = [ key for key in objectCaching.cachedMethodCalls if key[:3] == ('blueprintManager', 'GetBlueprintDataByOwner', ownerID) ]
        objectCaching.InvalidateCachedObjects(keys)
        sm.ScatterEvent('OnBlueprintReload', ownerID)

    def OnIndustryJob(self, jobID, ownerID, blueprintID, installerID, status, successfulRuns):
        """
        Listens to industry job changes so we can update the cached data for this blueprint.
        We modify the data inline so we don't need to reload the entire resource.
        """
        objectCaching = sm.GetService('objectCaching')
        keys = [ key for key in objectCaching.cachedMethodCalls if key[:3] == ('blueprintManager', 'GetBlueprintDataByOwner', ownerID) ]
        for key in keys:
            blueprints, facilities = objectCaching.cachedMethodCalls[key]['lret']
            for blueprint in blueprints:
                if blueprint.itemID == blueprintID:
                    if status < industry.STATUS_COMPLETED:
                        blueprint.jobID = jobID
                    else:
                        blueprint.jobID = None

    def OnSessionChanged(self, isRemote, session, change):
        """
        Listens to session changes and invalidate the blueprint cache if corp permissions change.
        """
        if 'corprole' in change:
            self.OnBlueprintsUpdated(session.corpid)

    @telemetry.ZONE_METHOD
    def GetBlueprintType(self, blueprintTypeID, isCopy = False):
        """
        Returns an immutable blueprint object based on a typeID. The returned object can be made
        mutable by calling its copy() method. A KeyError will be thrown if we cannot find the type.
        """
        try:
            ret = cfg.blueprints[blueprintTypeID]
            if isCopy or cfg.invtypes.Get(blueprintTypeID).categoryID == const.categoryAncientRelic:
                ret = ret.copy()
                ret.original = False
            return ret
        except KeyError:
            raise UserError('IndustryBlueprintNotFound')

    def GetBlueprintTypeCopy(self, typeID, original = True, runsRemaining = None, materialEfficiency = None, timeEfficiency = None):
        """
        Returns a mutable blueprint object based on a typeID
        """
        bpData = self.GetBlueprintType(typeID).copy()
        bpData.original = original and cfg.invtypes.Get(typeID).categoryID != const.categoryAncientRelic
        if runsRemaining is not None:
            bpData.runsRemaining = runsRemaining
        if materialEfficiency is not None:
            bpData.materialEfficiency = materialEfficiency
        if timeEfficiency is not None:
            bpData.timeEfficiency = timeEfficiency
        return bpData

    @telemetry.ZONE_METHOD
    def GetBlueprintItem(self, blueprintID):
        """
        Returns a mutable blueprint object from an itemID, including up to date ME / PE data.
        Throws a UserError if we are unable to find the requested blueprint.
        """
        return industryCommon.BlueprintInstance(self.blueprintManager.GetBlueprintData(blueprintID))

    def GetBlueprint(self, blueprintID, blueprintTypeID, isCopy = False):
        """
        Shorthand method for fetching a blueprint by itemID or typeID, depending on which is valid.
        """
        try:
            return self.GetBlueprintItem(blueprintID)
        except UserError:
            return self.GetBlueprintType(blueprintTypeID, isCopy=isCopy)

    def GetBlueprintByProduct(self, productTypeID):
        """
        Returns a static blueprint object used to build the specific product, if one exists.
        """
        try:
            return cfg.blueprints.index('productTypeID', productTypeID)
        except KeyError:
            return None

    @telemetry.ZONE_METHOD
    def GetOwnerBlueprints(self, ownerID, facilityID = None):
        """
        Returns a list of all blueprints for a given ownerID.
        """
        blueprints = []
        locations = set()
        rows, facilities = self.blueprintManager.GetBlueprintDataByOwner(ownerID, facilityID)
        for data in rows:
            try:
                blueprint = industryCommon.BlueprintInstance(data)
                blueprints.append(blueprint)
                locations.add(blueprint.locationID)
                locations.add(blueprint.facilityID)
                blue.pyos.BeNice()
            except KeyError:
                self.LogError('Unable to load blueprint instance: ', data)

        cfg.evelocations.Prime(locations)
        facilitySvc = sm.GetService('facilitySvc')
        for blueprint in blueprints:
            try:
                blueprint.facility = facilitySvc.GetFacility(blueprint.facilityID)
                blue.pyos.BeNice()
            except KeyError:
                pass

        return (blueprints, facilities)

    def GetCharacterBlueprints(self, facilityID = None):
        """
        Fetches the our personal blueprints.
        """
        return self.GetOwnerBlueprints(session.charid, facilityID)

    def GetCorporationBlueprints(self, facilityID = None):
        """
        Fetches the our corporations blueprints.
        """
        return self.GetOwnerBlueprints(session.corpid, facilityID)

    def CanSeeCorpBlueprints(self):
        """
         Can the current player view corporation blueprints
         NOTE: Players also need take access to individual divisions
        """
        if util.IsNPC(session.corpid):
            return False
        return session.corprole & (const.corpRoleCanRentResearchSlot | const.corpRoleFactoryManager | const.corpRoleCanRentFactorySlot) > 0
