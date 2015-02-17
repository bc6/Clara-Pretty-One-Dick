#Embedded file name: eve/common/script/sys\eveCfg.py
"""
Data and Configuration Service
Utility classes for EVE client and server

Installs itself as 'cfg' in the builtin namespace and 'const'
for constants.

Caching of static server data
Wrapping of DB data including Inventory types and groups.

Note! If any method (like sysCfg.Recordset.Get) has to fetch data from
the server the call must be made on a uthread.
"""
import math
import sys
import types
import random
import copy
import re
import sqlite3
import collections
import blue
import bluepy
from crimewatch.util import GetKillReportHashValue
import eve.common.script.util.utillib_bootstrap as utillib
import carbon.common.script.util.format as formatUtil
import eve.common.script.util.eveFormat as evefmtutil
from carbon.common.script.sys.crowset import CRowset
import carbon.common.script.sys.service as service
import carbon.common.script.net.machobase as machobase
import localization
import re
import sqlite3
import fsdlite
import remotefilecache
import uthread
import carbon.common.script.sys.cfg as sysCfg
from inventorycommon.util import IsNPC
import pytelemetry.zoning as telemetry
import collections
globals().update(service.consts)
import const
import standingUtil
import fsdSchemas.binaryLoader as fsdBinaryLoader
import spacecomponents.common.factory
from spacecomponents.common.helper import HasCargoBayComponent
import evewar.util
from eve.common.script.sys.idCheckers import IsCelestial, IsConstellation, IsRegion, IsSolarSystem, IsStation
OWNER_AURA_IDENTIFIER = -1
OWNER_SYSTEM_IDENTIFIER = -2

class Standings():
    __guid__ = 'eveCfg.Standings'
    __passbyvalue__ = 1

    def __init__(self, fromID, fromFactionID, fromCorpID, fromCharID, toID, toFactionID, toCorpID, toCharID):
        self.fromID, self.fromFactionID, self.fromCorpID, self.fromCharID, self.toID, self.toFactionID, self.toCorpID, self.toCharID = (fromID,
         fromFactionID,
         fromCorpID,
         fromCharID,
         toID,
         toFactionID,
         toCorpID,
         toCharID)
        self.faction = utillib.KeyVal(faction=0.0, corp=0.0, char=0.0)
        self.corp = utillib.KeyVal(faction=0.0, corp=0.0, char=0.0)
        self.char = utillib.KeyVal(faction=0.0, corp=0.0, char=0.0)

    def __str__(self):
        return 'Standing from %s toward %s: faction:(%s,%s,%s), corp:(%s,%s,%s), char:(%s,%s,%s)' % (self.fromID,
         self.toID,
         self.faction.faction,
         self.faction.corp,
         self.faction.char,
         self.corp.faction,
         self.corp.corp,
         self.corp.char,
         self.char.faction,
         self.char.corp,
         self.char.char)

    def __repr__(self):
        return self.__str__()

    def CanUseAgent(self, level, agentTypeID = None, noL1Check = 1):
        return CanUseAgent(level, agentTypeID, self.faction.char, self.corp.char, self.char.char, self.fromCorpID, self.fromFactionID, {}, noL1Check)

    def __getattr__(self, theKey):
        if theKey == 'minimum':
            m = None
            for each in (self.faction, self.corp, self.char):
                for other in (each.faction, each.corp, each.char):
                    if other != 0.0 and (m is None or other < m):
                        m = other

            if m is None:
                return 0.0
            return m
        if theKey == 'maximum':
            m = None
            for each in (self.faction, self.corp, self.char):
                for other in (each.faction, each.corp, each.char):
                    if other != 0.0 and (m is None or other > m):
                        m = other

            if m is None:
                return 0.0
            return m
        if theKey == 'direct':
            if self.fromID == self.fromFactionID:
                tmp = self.faction
            elif self.fromID == self.fromCorpID:
                tmp = self.corp
            elif self.fromID == self.fromCharID:
                tmp = self.char
            if self.toID == self.toFactionID:
                return tmp.faction
            elif self.toID == self.toCorpID:
                return tmp.corp
            elif self.toID == self.toCharID:
                return tmp.char
            else:
                return 0.0
        else:
            if theKey == 'all':
                return [(self.fromFactionID, self.toFactionID, self.faction.faction),
                 (self.fromFactionID, self.toCorpID, self.faction.corp),
                 (self.fromFactionID, self.toCharID, self.faction.char),
                 (self.fromCorpID, self.toFactionID, self.corp.faction),
                 (self.fromCorpID, self.toCorpID, self.corp.corp),
                 (self.fromCorpID, self.toCharID, self.corp.char),
                 (self.fromCharID, self.toFactionID, self.char.faction),
                 (self.fromCharID, self.toCorpID, self.char.corp),
                 (self.fromCharID, self.toCharID, self.char.char)]
            raise AttributeError(theKey)


def CanUseAgent(level, agentTypeID, fac, coc, cac, fromCorpID, fromFactionID, skills, noL1Check = 1):
    if agentTypeID == const.agentTypeAura:
        return True
    elif level == 1 and agentTypeID != const.agentTypeResearchAgent and noL1Check:
        return 1
    m = (level - 1) * 2.0 - 1.0
    if boot.role == 'client':
        bonus = 0.0
        if not skills:
            char = sm.GetService('godma').GetItem(eve.session.charid)
            for skill in char.skills.itervalues():
                if skill.typeID in (const.typeConnections, const.typeDiplomacy, const.typeCriminalConnections):
                    skills[skill.typeID] = skill.skillLevel

            skills[0] = 0
        unused, facBonus = standingUtil.GetStandingBonus(fac, fromFactionID, skills)
        unused, cocBonus = standingUtil.GetStandingBonus(coc, fromFactionID, skills)
        unused, cacBonus = standingUtil.GetStandingBonus(cac, fromFactionID, skills)
        if facBonus > 0.0:
            fac = (1.0 - (1.0 - fac / 10.0) * (1.0 - facBonus / 10.0)) * 10.0
        if cocBonus > 0.0:
            coc = (1.0 - (1.0 - coc / 10.0) * (1.0 - cocBonus / 10.0)) * 10.0
        if cacBonus > 0.0:
            cac = (1.0 - (1.0 - cac / 10.0) * (1.0 - cacBonus / 10.0)) * 10.0
    if max(fac, coc, cac) >= m and min(fac, coc, cac) > -2.0:
        if agentTypeID == const.agentTypeResearchAgent and coc < m - 2.0:
            return 0
        return 1
    else:
        return 0


class EveDataConfig(sysCfg.DataConfig):
    __guid__ = 'svc.eveDataconfig'
    __replaceservice__ = 'dataconfig'

    def __init__(self):
        sysCfg.DataConfig.__init__(self)

    def _CreateConfig(self):
        return EveConfig()


class EveConfig(sysCfg.Config):
    __guid__ = 'util.EveConfig'

    def __init__(self):
        sysCfg.Config.__init__(self)
        self.fmtMapping[const.UE_OWNERID] = lambda value, value2: cfg.eveowners.Get(value).ownerName
        self.fmtMapping[const.UE_OWNERIDNICK] = lambda value, value2: cfg.eveowners.Get(value).ownerName.split(' ')[0]
        self.fmtMapping[const.UE_LOCID] = lambda value, value2: cfg.evelocations.Get(value).locationName
        self.fmtMapping[const.UE_TYPEID] = lambda value, value2: cfg.invtypes.Get(value).typeName
        self.fmtMapping[const.UE_TYPEID2] = lambda value, value2: cfg.invtypes.Get(value).description
        self.fmtMapping[const.UE_TYPEIDL] = lambda value, value2: cfg.FormatConvert(const.UE_LIST, [ (const.UE_TYPEID, x) for x in value ], value2)
        self.fmtMapping[const.UE_BPTYPEID] = lambda value, value2: cfg.invtypes.Get(cfg.blueprints.Get(value).blueprintTypeID).typeName
        self.fmtMapping[const.UE_GROUPID] = lambda value, value2: cfg.invgroups.Get(value).groupName
        self.fmtMapping[const.UE_GROUPID2] = lambda value, value2: cfg.invgroups.Get(value).description
        self.fmtMapping[const.UE_CATID] = lambda value, value2: cfg.invcategories.Get(value).categoryName
        self.fmtMapping[const.UE_CATID2] = lambda value, value2: cfg.invcategories.Get(value).description
        self.fmtMapping[const.UE_AMT] = lambda value, value2: formatUtil.FmtAmt(value)
        self.fmtMapping[const.UE_AMT2] = lambda value, value2: evefmtutil.FmtISK(value)
        self.fmtMapping[const.UE_AMT3] = lambda value, value2: evefmtutil.FmtISK(value)
        self.fmtMapping[const.UE_ISK] = lambda value, value2: evefmtutil.FmtISK(value)
        self.fmtMapping[const.UE_AUR] = lambda value, value2: evefmtutil.FmtAUR(value)
        self.fmtMapping[const.UE_DIST] = lambda value, value2: formatUtil.FmtDist(value)
        self.fmtMapping[const.UE_TYPEIDANDQUANTITY] = self.__FormatTypeIDAndQuantity
        self.crystalgroups = []
        self.rawCelestialCache = {}
        self.localdb = None
        self.mapObjectsDb = None

    def Release(self):
        sysCfg.Config.Release(self)
        self.graphics = None
        self.icons = None
        self.sounds = None
        self.groupGraphics = None
        self.invgroups = None
        self.invtypes = None
        self.invmetagroups = None
        self.invmetatypes = None
        self.ramaltypes = None
        self.ramaltypesdetailpercategory = None
        self.ramaltypesdetailpergroup = None
        self.ramactivities = None
        self.ramtyperequirements = None
        self.invtypematerials = None
        self.ramcompletedstatuses = None
        self.staoperationtypes = None
        self.mapcelestialdescriptions = None
        self.dgmattribs = None
        self.dgmeffects = None
        self.dgmtypeattribs = None
        self.dgmtypeeffects = None
        self.dgmunits = None
        self.eveowners = None
        self.evelocations = None
        self.rawCelestialCache = None
        self.corptickernames = None
        self.allianceshortnames = None
        self.factions = None
        self.npccorporations = None
        self.crystalgroups = None
        self.locationwormholeclasses = None
        self.nebulas = None
        self.schematics = None
        self.schematicstypemap = None
        self.schematicspinmap = None
        self.schematicsByPin = None
        self.schematicsByType = None
        self.billtypes = None
        self.bloodlineNames = None
        self.overviewDefaults = None
        self.overviewDefaultGroups = None
        self.positions = None
        self.messages = None
        self.localdb = None
        self.mapObjectsDb = None

    def GetStartupData(self):
        """
        Overrides the default behaviour in order to load messages from bulk AFTER we have
        acquired logchannels, but before we login.
        """
        sysCfg.Config.GetStartupData(self)
        if boot.role == 'client':
            self.messages = _LoadMessagesFromFSD()

    def IsLocalIdentity(self, theID):
        if theID >= const.minPlayerOwner or theID > const.maxNPCStation and theID <= const.maxStation:
            return False
        return True

    @telemetry.ZONE_METHOD
    def GetMessage(self, key, dict = None, onNotFound = 'return', onDictMissing = 'error', languageID = None):
        """
        Tries to display a pre-formatted message 
        """
        try:
            msg = self.messages[key]
        except KeyError:
            return self._GetContentForMissingMessage(key, dict, languageID=languageID)

        bodyID, titleID = msg.bodyID, msg.titleID
        title, text = self._GetTitleAndTextForMessage(dict, titleID, bodyID, languageID=languageID)
        return utillib.KeyVal(text=text, title=title, type=msg.dialogType, audio=msg.urlAudio, icon=msg.urlIcon, suppress=msg.suppressable)

    @telemetry.ZONE_METHOD
    def GetMessageTypeAndText(self, key, paramDict, onNotFound = 'return', onDictMissing = 'error', languageID = None):
        """
        Tries to display a pre-formatted message. This is a variant of GetMessage that only
        returns text and type, and does a less expensive expansion of paramDict for owner and such.
        """
        try:
            msg = self.messages[key]
        except KeyError:
            return self._GetContentForMissingMessage(key, paramDict, languageID=languageID)

        for k, v in paramDict.iteritems():
            if type(v) != types.TupleType:
                continue
            value2 = None
            if len(v) >= 3:
                value2 = v[2]
            paramDict[k] = self.FormatConvert(v[0], v[1], value2)

        text = localization.GetByMessageID(msg.bodyID, languageID=languageID, **paramDict)
        return utillib.KeyVal(text=text, type=msg.dialogType)

    def _GetContentForMissingMessage(self, key, paramDict, languageID):
        if key != 'ErrMessageNotFound':
            return self.GetMessage('ErrMessageNotFound', {'msgid': key,
             'args': repr(paramDict)}, languageID=languageID)
        else:
            return utillib.KeyVal(text='Could not find message with key ' + key + '. This is most likely due to a missing or outdated 10000001.cache2 bulkdata file, or the message is missing.', title='Message not found', type='fatal', audio='', icon='', suppress=False)

    def _GetTitleAndTextForMessage(self, paramDict, titleID, bodyID, languageID):
        if paramDict is not None and paramDict != -1:
            paramDict = self.__prepdict(paramDict)
            title = localization.GetByMessageID(titleID, languageID=languageID, **paramDict) if titleID is not None else None
            text = localization.GetByMessageID(bodyID, languageID=languageID, **paramDict) if bodyID is not None else None
        else:
            title = localization.GetByMessageID(titleID, languageID=languageID) if titleID is not None else None
            text = localization.GetByMessageID(bodyID, languageID=languageID) if bodyID is not None else None
        return (title, text)

    def GetRawMessageTitle(self, key):
        """
            Used to display the name of a message in the system menu. No error when the message is not found.
        """
        msg = self.messages.get(key, None)
        if msg:
            if msg.titleID is not None:
                return localization._GetRawByMessageID(msg.titleID)

    def IsChargeCompatible(self, item):
        if not item[const.ixSingleton]:
            return 0
        else:
            return item[const.ixGroupID] in self.__chargecompatiblegroups__

    def IsFittableCategory(self, categoryID):
        return categoryID in (const.categoryModule, const.categorySubSystem, const.categoryStructureUpgrade)

    def IsSubSystemVisible(self, flag):
        return flag >= const.flagSubSystemSlot0 and flag < const.flagSubSystemSlot0 + const.visibleSubSystems

    def IsContainer(self, item, doSpaceComponentCheck = True):
        """
        Utility function which takes an 'item' struct as returned from the inventory
        system and checks wether it's a container or not
        """
        if not item.singleton:
            return False
        elif item.categoryID in self.__containercategories__ or item.groupID in self.__containergroups__:
            return True
        elif doSpaceComponentCheck:
            return IsSolarSystem(item.locationID) and HasCargoBayComponent(item.typeID)
        else:
            return False

    def IsCargoContainer(self, item):
        return item.singleton and item.groupID in self.__containergroups__

    def AppGetStartupData(self):
        """Reads in all constants and messages from the database and calls LoadStaticData()"""
        configSvc = sm.GetService('config')
        initdata = configSvc.GetInitVals()
        self.GotInitData(initdata)
        configSvc.RegisterTablesForUpdates()

    def ReportLoginProgress(self, section, stepNum, totalSteps = None):
        """Report login progress but only if we are in client mode"""
        if totalSteps is not None:
            self.totalLogonSteps = totalSteps
        if machobase.mode == 'client':
            sm.ScatterEvent('OnProcessLoginProgress', 'loginprogress::gettingbulkdata', section, stepNum, self.totalLogonSteps)
        else:
            cfg.LogInfo(section, stepNum)

    def LoadMapObjectsDB(self):
        res = blue.ResFile()
        if blue.pyos.packaged:
            mapObjectsResPath = blue.paths.ResolvePath('bin:/staticdata/mapObjects.db')
        else:
            mapObjectsResPath = blue.paths.ResolvePath('resbin:/staticdata/mapObjects.db')
        if not res.Open(mapObjectsResPath):
            cfg.LogError('Could not find file %s.' % mapObjectsResPath)
        else:
            self.mapObjectsDb = sqlite3.connect(mapObjectsResPath)
            self.mapObjectsDb.row_factory = sqlite3.Row
        res.Close()

    @telemetry.ZONE_METHOD
    def LoadBlueprints(self):
        import industry
        if blue.pyos.packaged:
            if boot.role == 'client':
                cache = blue.paths.ResolvePath(u'bin:/staticdata/blueprints.db')
            else:
                cache = blue.paths.ResolvePath(u'res:/staticdata/blueprints.db')
            self.blueprints = fsdlite.Storage(None, cache, mapping=industry.MAPPING, indexes=industry.INDEXES, monitor=False)
        else:
            static = blue.paths.ResolvePath(u'root:/staticData/blueprints/*.staticdata')
            cache = blue.paths.ResolvePath(u'root:/autobuild/staticData/server/blueprints.db')
            self.blueprints = fsdlite.Storage(static, cache, mapping=industry.MAPPING, indexes=industry.INDEXES, monitor=True)

    def GotInitData(self, initdata):
        """
        Reads in all constants and messages from the database and calls LoadStaticData().
        Called both from GetStartupData and from the various bulk data update notifications.
        """
        cfg.LogInfo('App GotInitData')
        remotefilecache.prefetch_folder('res:/staticdata')
        sysCfg.Config.GotInitData(self, initdata)
        self.dgmunits = self.LoadBulkIndex('dgmunits', const.cacheDogmaUnits, 'unitID', DgmUnit)
        self.invcategories = self.LoadBulkIndex('invcategories', const.cacheInvCategories, 'categoryID', InvCategory)
        self.invmetagroups = self.LoadBulkIndex('invmetagroups', const.cacheInvMetaGroups, 'metaGroupID', InvMetaGroup)
        self.invgroups = self.LoadBulkIndex('invgroups', const.cacheInvGroups, 'groupID', InvGroup)
        self.invtypes = self.LoadBulkIndex('invtypes', const.cacheInvTypes, 'typeID', InvType)
        self.fsdTypeOverrides = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/typeIDs.static', 'res:/staticdata/typeIDs.schema', optimize=False)
        self.fsdTestTypeOverrides = None
        self.fsdDustIcons = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/dustIcons.static')
        if not blue.pyos.packaged:
            self.fsdTestTypeOverrides = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/testTypeIDs.static', 'res:/staticdata/typeIDs.schema', optimize=False)
        self.mapRegionCache = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/regions.static', 'res:/staticdata/regions.schema', optimize=False)
        self.mapConstellationCache = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/constellations.static', 'res:/staticdata/constellations.schema', optimize=False)
        self.mapSystemCache = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/systems.static', 'res:/staticdata/systems.schema', optimize=False)
        self.mapJumpCache = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/jumps.static', 'res:/staticdata/jumps.schema', optimize=False)
        self.mapSolarSystemContentCache = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/solarSystemContent.static')
        self.invtypereactions = self.LoadBulkFilter('invtypereactions', const.cacheInvTypeReactions, 'reactionTypeID')
        self.invmetatypes = self.LoadBulkIndex('invmetatypes', const.cacheInvMetaTypes, 'typeID')
        self.invmetatypesByParent = self.LoadBulkFilter('invmetatypesByParent', const.cacheInvMetaTypes, 'parentTypeID')
        invcontrabandtypes = self.LoadBulk(None, const.cacheInvContrabandTypes)
        self.invcontrabandTypesByFaction = {}
        self.invcontrabandFactionsByType = {}
        self.bulkIDsToCfgNames[const.cacheInvContrabandTypes] = ['invcontrabandTypesByFaction', 'invcontrabandFactionsByType']
        for each in invcontrabandtypes:
            if each.factionID not in self.invcontrabandTypesByFaction:
                self.invcontrabandTypesByFaction[each.factionID] = {}
            self.invcontrabandTypesByFaction[each.factionID][each.typeID] = each
            if each.typeID not in self.invcontrabandFactionsByType:
                self.invcontrabandFactionsByType[each.typeID] = {}
            self.invcontrabandFactionsByType[each.typeID][each.factionID] = each

        self.dgmattribs = self.LoadBulkIndex('dgmattribs', const.cacheDogmaAttributes, 'attributeID', DgmAttribute)
        self.dgmeffects = self.LoadBulkIndex('dgmeffects', const.cacheDogmaEffects, 'effectID', DgmEffect)
        self.dgmtypeattribs = self.LoadBulkFilter('dgmtypeattribs', const.cacheDogmaTypeAttributes, 'typeID')
        self.dgmtypeeffects = self.LoadBulkFilter('dgmtypeeffects', const.cacheDogmaTypeEffects, 'typeID')
        self.dgmexpressions = self.LoadBulkIndex('dgmexpressions', const.cacheDogmaExpressions, 'expressionID')
        self.shiptypes = self.LoadBulkIndex('shiptypes', const.cacheShipTypes, 'shipTypeID')
        self.ramaltypes = self.LoadBulkIndex('ramaltypes', const.cacheRamAssemblyLineTypes, 'assemblyLineTypeID')
        self.ramaltypesdetailpercategory = self.LoadBulkFilter('ramaltypesdetailpercategory', const.cacheRamAssemblyLineTypesCategory, 'assemblyLineTypeID', virtualColumns=[('activityID', RamActivityVirtualColumn)])
        self.ramaltypesdetailpergroup = self.LoadBulkFilter('ramaltypesdetailpergroup', const.cacheRamAssemblyLineTypesGroup, 'assemblyLineTypeID', virtualColumns=[('activityID', RamActivityVirtualColumn)])
        self.ramactivities = self.LoadBulkIndex('ramactivities', const.cacheRamActivities, 'activityID', RamActivity)
        self.ramcompletedstatuses = self.LoadBulkIndex('ramcompletedstatuses', const.cacheRamCompletedStatuses, 'completedStatus', RamCompletedStatus)
        self.invtypematerials = self.LoadBulkFilter('invtypematerials', const.cacheInvTypeMaterials, 'typeID')
        self.staoperationtypes = self.LoadBulkIndex('staoperationtypes', const.cacheStaOperations, 'operationID')
        ramtyperequirements = self.LoadBulk('ramtyperequirements', const.cacheRamTypeRequirements)
        d = {}
        for row in ramtyperequirements:
            key = (row.typeID, row.activityID)
            if key in d:
                d[key].append(row)
            else:
                d[key] = [row]

        self.ramtyperequirements = d
        self.mapcelestialdescriptions = self.LoadBulkIndex('mapcelestialdescriptions', const.cacheMapCelestialDescriptions, 'itemID', MapCelestialDescription)
        self.locationwormholeclasses = self.LoadBulkIndex('locationwormholeclasses', const.cacheMapLocationWormholeClasses, 'locationID')
        self.nebulas = self.LoadBulkIndex('nebulas', const.cacheMapNebulas, 'locationID')
        self.battlefields = self.LoadBulkIndex('battlefields', const.cacheMapBattlefields, 'battlefieldID')
        self.districts = self.LoadBulkIndex('districts', const.cacheMapDistricts, 'districtID')
        self.levels = self.LoadBulkIndex('levels', const.cacheMapLevels, 'levelID')
        self.schematics = self.LoadBulkIndex('schematics', const.cachePlanetSchematics, 'schematicID', Schematic)
        self.schematicstypemap = self.LoadBulkFilter('schematicstypemap', const.cachePlanetSchematicsTypeMap, 'schematicID')
        self.schematicspinmap = self.LoadBulkFilter('schematicspinmap', const.cachePlanetSchematicsPinMap, 'schematicID')
        self.schematicsByPin = self.LoadBulkFilter('schematicsByPin', const.cachePlanetSchematicsPinMap, 'pinTypeID')
        self.schematicsByType = self.LoadBulkFilter('schematicsByType', const.cachePlanetSchematicsTypeMap, 'typeID')
        self.groupsByCategories = self.LoadBulkFilter('groupsByCategories', const.cacheInvGroups, 'categoryID')
        self.typesByGroups = self.LoadBulkFilter('typesByGroups', const.cacheInvTypes, 'groupID')
        self.typesByMarketGroups = self.LoadBulkFilter('typesByMarketGroups', const.cacheInvTypes, 'marketGroupID')
        self.billtypes = self.LoadBulkIndex('billtypes', const.cacheActBillTypes, 'billTypeID', Billtype)
        self.overviewDefaults = self.LoadBulkIndex('overviewDefaults', const.cacheChrDefaultOverviews, 'overviewID', OverviewDefault)
        self.overviewDefaultGroups = self.LoadBulkFilter('overviewDefaultGroups', const.cacheChrDefaultOverviewGroups, 'overviewID')
        self.bloodlineNames = self.LoadBulkFilter('bloodlineNames', const.cacheChrBloodlineNames, 'bloodlineID')
        self.bloodlines = self.LoadBulkIndex('bloodlines', const.cacheChrBloodlines, 'bloodlineID')
        self.factions = self.LoadBulkIndex('factions', const.cacheChrFactions, 'factionID', Faction)
        self.races = self.LoadBulkIndex('races', const.cacheChrRaces, 'raceID', Race)
        self.npccorporations = self.LoadBulkIndex('npccorporations', const.cacheCrpNpcCorporations, 'corporationID')
        self.corptickernames = self.LoadBulk('corptickernames', const.cacheCrpTickerNamesStatic, sysCfg.Recordset(CrpTickerNames, 'corporationID', 'GetCorpTickerNamesEx', 'GetMultiCorpTickerNamesEx'), tableID=const.cacheCrpNpcCorporations)
        self.messages = _LoadMessagesFromFSD()
        if boot.role == 'client':
            self.localdb = sqlite3.connect(blue.paths.ResolvePathForWriting(u'app:/bulkdata/mapbulk.db'))
            self.localdb.row_factory = sqlite3.Row
            self.CheckLocalDBVersion()
            self.LoadMapObjectsDB()
            self.mapCelestialLocationCache = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/locationCache.static')
            self.mapFactionsOwningSolarSystems = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/factionsOwningSolarSystems.static', 'res:/staticdata/factionsOwningSolarSystems.schema', optimize=False)
            self.fsdInfoBubbleElements = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/infoBubbleElements.static', 'res:/staticdata/infoBubbleElements.schema', optimize=False)
            self.fsdInfoBubbleFactions = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/infoBubbleFactions.static', 'res:/staticdata/infoBubbleFactions.schema', optimize=False)
            self.fsdInfoBubbleGroups = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/infoBubbleGroups.static', 'res:/staticdata/infoBubbleGroups.schema', optimize=False)
            self.groupGraphics = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/groupGraphics.static')
        else:
            self.localdb = None
            self.securityForSystemsWithPlanetsInLocation = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/securityForSystemsWithPlanetsInLocation.static')
        self.LoadEveOwners()
        self.LoadEveLocations()
        self.LoadBlueprints()
        allianceshortnameRowHeader = blue.DBRowDescriptor((('allianceID', const.DBTYPE_I4), ('shortName', const.DBTYPE_WSTR)))
        self.allianceshortnameRowset = CRowset(allianceshortnameRowHeader, [])
        self.allianceshortnames = sysCfg.Recordset(AllShortNames, 'allianceID', 'GetAllianceShortNamesEx', 'GetMultiAllianceShortNamesEx')
        self.ConvertData(self.allianceshortnameRowset, self.allianceshortnames)
        positionRowHeader = blue.DBRowDescriptor((('itemID', const.DBTYPE_I8),
         ('x', const.DBTYPE_R5),
         ('y', const.DBTYPE_R5),
         ('z', const.DBTYPE_R5),
         ('yaw', const.DBTYPE_R4),
         ('pitch', const.DBTYPE_R4),
         ('roll', const.DBTYPE_R4)))
        positionRowset = CRowset(positionRowHeader, [])
        self.positions = sysCfg.Recordset(Position, 'itemID', 'GetPositionEx', 'GetPositionsEx')
        self.ConvertData(positionRowset, self.positions)
        if boot.role == 'client':
            self._averageMarketPrice = {}
            uthread.new(self.GetAveragePricesThread)
        else:
            self._averageMarketPrice = self.GetConfigSvc().GetAverageMarketPrices()
        self.__containercategories__ = (const.categoryStation,
         const.categoryShip,
         const.categoryTrading,
         const.categoryStructure)
        self.__containergroups__ = (const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer,
         const.groupConstellation,
         const.groupRegion,
         const.groupSolarSystem,
         const.groupMissionContainer,
         const.groupSpewContainer)
        self.__chargecompatiblegroups__ = (const.groupFrequencyMiningLaser,
         const.groupEnergyWeapon,
         const.groupProjectileWeapon,
         const.groupMissileLauncher,
         const.groupCapacitorBooster,
         const.groupHybridWeapon,
         const.groupScanProbeLauncher,
         const.groupComputerInterfaceNode,
         const.groupMissileLauncherBomb,
         const.groupMissileLauncherCruise,
         const.groupMissileLauncherDefender,
         const.groupMissileLauncherAssault,
         const.groupMissileLauncherSiege,
         const.groupMissileLauncherHeavy,
         const.groupMissileLauncherHeavyAssault,
         const.groupMissileLauncherRocket,
         const.groupMissileLauncherStandard,
         const.groupMissileLauncherCitadel,
         const.groupMissileLauncherFestival,
         const.groupBubbleProbeLauncher,
         const.groupSensorBooster,
         const.groupRemoteSensorBooster,
         const.groupRemoteSensorDamper,
         const.groupTrackingComputer,
         const.groupTrackingDisruptor,
         const.groupTrackingLink,
         const.groupWarpDisruptFieldGenerator,
         const.groupFueledShieldBooster,
         const.groupFueledArmorRepairer,
         const.groupSurveyProbeLauncher,
         const.groupMissileLauncherRapidHeavy,
         const.groupDroneTrackingModules)
        self.spaceComponentStaticData = spacecomponents.common.factory.CreateComponentStaticData('res:/staticdata/spacecomponents.static')
        if boot.role == 'server':
            if prefs.GetValue('enableTrueMoonMinerals', False):
                self._moonMinerals = fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/moonMinerals.static', 'res:/staticdata/moonMinerals.schema', optimize=False)
            else:
                testMoonMineralDistribution = {const.typeAtmosphericGases: 1,
                 const.typeEvaporiteDeposits: 1,
                 const.typeSilicates: 1,
                 const.typeHydrocarbons: 1}
                self._moonMinerals = collections.defaultdict(lambda : testMoonMineralDistribution)

    @telemetry.ZONE_METHOD
    def __prepdict(self, dict):
        dict = copy.deepcopy(dict)
        if charsession:
            for k, v in {'session.char': (const.UE_OWNERID, charsession.charid),
             'session.nick': (const.UE_OWNERIDNICK, charsession.charid),
             'session.corp': (const.UE_OWNERID, charsession.corpid),
             'session.station': (const.UE_LOCID, charsession.stationid),
             'session.solarsystem': (const.UE_LOCID, charsession.solarsystemid2),
             'session.constellation': (const.UE_LOCID, charsession.constellationid),
             'session.region': (const.UE_LOCID, charsession.regionid),
             'session.location': (const.UE_LOCID, charsession.locationid)}.iteritems():
                if v[1] is not None:
                    dict[k] = v

        for k, v in dict.iteritems():
            if type(v) != types.TupleType:
                continue
            value2 = None
            if len(v) >= 3:
                value2 = v[2]
            dict[k] = self.FormatConvert(v[0], v[1], value2)

        return dict

    def __FormatTypeIDAndQuantity(self, typeID, quantity):
        return localization.GetByLabel('UI/Common/QuantityAndItem', quantity=quantity, item=typeID)

    def GetAveragePricesThread(self):
        """
        This is being threaded in the client since the data can be big and we don't wan't the client to halt because of this.
        """
        blue.pyos.synchro.SleepWallclock(2000)
        self._averageMarketPrice = self.GetConfigSvc().GetAverageMarketPrices()

    def GetCrystalGroups(self):
        """
        handy to know if it's a single ammo charge to load or if it can handle more
        """
        if not self.crystalgroups:
            crystalGroupIDs = [ x.groupID for x in cfg.groupsByCategories.get(const.categoryCharge, []) if x.groupName.endswith('Crystal') ]
            self.crystalgroups.extend(crystalGroupIDs)
            scriptGroupIDs = [ x.groupID for x in cfg.groupsByCategories.get(const.categoryCharge, []) if x.groupName.endswith('Script') ]
            self.crystalgroups.extend(scriptGroupIDs)
        return self.crystalgroups

    def GetLocationWormholeClass(self, solarSystemID):
        system = self.mapSystemCache[solarSystemID]
        return getattr(system, 'wormholeClassID', const.INVALID_WORMHOLE_CLASS_ID)

    def GetNebula(self, solarSystemID, constellationID, regionID, returnPath = True):
        """
            Returns either the graphicID or the graphicPath for a given location in the world.
        """
        if returnPath:
            return self.mapRegionCache.Get(regionID).nebulaPath
        else:
            return self.mapRegionCache.Get(regionID).nebulaID

    @telemetry.ZONE_METHOD
    def LoadEveOwners(self):
        npccharacters = self.LoadBulkIndex(None, const.cacheChrNpcCharacters, 'characterID')
        rowDescriptor = self.GetOwnersRowDescriptor()
        self.eveowners = sysCfg.Recordset(EveOwners, 'ownerID', 'GetOwnersEx', 'GetMultiOwnersEx')
        self.eveowners.header = ['ownerID',
         'ownerName',
         'typeID',
         'gender',
         'ownerNameID']
        bloodlinesToTypes = {const.bloodlineDeteis: const.typeCharacterDeteis,
         const.bloodlineCivire: const.typeCharacterCivire,
         const.bloodlineSebiestor: const.typeCharacterSebiestor,
         const.bloodlineBrutor: const.typeCharacterBrutor,
         const.bloodlineAmarr: const.typeCharacterAmarr,
         const.bloodlineNiKunni: const.typeCharacterNiKunni,
         const.bloodlineGallente: const.typeCharacterGallente,
         const.bloodlineIntaki: const.typeCharacterIntaki,
         const.bloodlineStatic: const.typeCharacterStatic,
         const.bloodlineModifier: const.typeCharacterModifier,
         const.bloodlineAchura: const.typeCharacterAchura,
         const.bloodlineJinMei: const.typeCharacterJinMei,
         const.bloodlineKhanid: const.typeCharacterKhanid,
         const.bloodlineVherokior: const.typeCharacterVherokior}
        for row in self.factions:
            if boot.role == 'client':
                factionName = localization.GetImportantByMessageID(row.factionNameID) or row.factionName
            else:
                factionName = row.factionName
            self.factions.data[row.factionID].factionName = factionName
            if row.descriptionID:
                self.factions.data[row.factionID].description = localization.GetByMessageID(row.descriptionID)
            self.eveowners.data[row.factionID] = blue.DBRow(rowDescriptor, [row.factionID,
             factionName,
             const.typeFaction,
             None,
             row.factionNameID])

        for row in self.npccorporations:
            if boot.role == 'client':
                corporationName = localization.GetImportantByMessageID(row.corporationNameID) or row.corporationName
            else:
                corporationName = row.corporationName
            self.npccorporations.data[row.corporationID].corporationName = corporationName
            if row.descriptionID:
                self.npccorporations.data[row.corporationID].description = localization.GetByMessageID(row.descriptionID)
            self.eveowners.data[row.corporationID] = blue.DBRow(rowDescriptor, [row.corporationID,
             corporationName,
             const.typeCorporation,
             None,
             row.corporationNameID])

        for row in npccharacters:
            if boot.role == 'client':
                npcName = localization.GetImportantByMessageID(row.characterNameID) or row.characterName
            else:
                npcName = row.characterName
            try:
                self.eveowners.data[row.characterID] = blue.DBRow(rowDescriptor, [row.characterID,
                 npcName,
                 bloodlinesToTypes[row.bloodlineID],
                 row.gender,
                 row.characterNameID])
            except KeyError:
                self.LogError('ERROR: NPC missing from eveowner table - PLEASE FIX THIS!', row.characterID, npcName)

        auraName = localization.GetImportantByLabel(OWNER_NAME_OVERRIDES[OWNER_AURA_IDENTIFIER])
        for i in const.auraAgentIDs:
            self.eveowners.data[i].ownerName = auraName

        self.eveowners.data[1] = blue.DBRow(rowDescriptor, [1,
         localization.GetByLabel(OWNER_NAME_OVERRIDES[OWNER_SYSTEM_IDENTIFIER]),
         0,
         None,
         None])

    def UpdateEveOwnerName(self, ownerID, ownerName):
        owner = self.eveowners.Get(ownerID)
        self.eveowners.data[ownerID] = blue.DBRow(self.GetOwnersRowDescriptor(), [ownerID,
         ownerName,
         owner.typeID,
         owner.gender,
         owner.ownerNameID])

    def GetOwnersRowDescriptor(self):
        return blue.DBRowDescriptor((('ownerID', const.DBTYPE_I4),
         ('ownerName', const.DBTYPE_WSTR),
         ('typeID', const.DBTYPE_I2),
         ('gender', const.DBTYPE_I2),
         ('ownerNameID', const.DBTYPE_I4)))

    def GetLocationRowDescriptor(self):
        return blue.DBRowDescriptor((('locationID', const.DBTYPE_I8),
         ('locationName', const.DBTYPE_WSTR),
         ('x', const.DBTYPE_R5),
         ('y', const.DBTYPE_R5),
         ('z', const.DBTYPE_R5),
         ('locationNameID', const.DBTYPE_I4)))

    @telemetry.ZONE_METHOD
    def LoadEveLocations(self):
        """
            Constructs cfg.evelocations from bulk data files and the sqlite bulkdata db.
            It is imperative that these things are primed on startup or the resolution of translated names
            will become recursive and that causes deadlocks in the Prime method.
        """
        self.stations = self.LoadBulk('stations', const.cacheStaStationsStatic, sysCfg.Recordset(sysCfg.Row, 'stationID', 'GetStationEx', 'GetMultiStationEx'))
        rowDescriptor = self.GetLocationRowDescriptor()
        self.evelocations = sysCfg.Recordset(EveLocations, 'locationID', 'GetLocationsEx', 'GetMultiLocationsEx', 'GetLocationsLocal')
        self.evelocations.header = ['locationID',
         'locationName',
         'x',
         'y',
         'z',
         'locationNameID']
        for regionID, region in self.mapRegionCache.iteritems():
            regionName = localization.GetImportantByMessageID(region.nameID)
            self.evelocations.data[regionID] = blue.DBRow(rowDescriptor, [regionID,
             regionName,
             region.center[0],
             region.center[1],
             region.center[2],
             region.nameID])

        for constellationID, constellation in self.mapConstellationCache.iteritems():
            constellationName = localization.GetImportantByMessageID(constellation.nameID)
            self.evelocations.data[constellationID] = blue.DBRow(rowDescriptor, [constellationID,
             constellationName,
             constellation.center.x,
             constellation.center.y,
             constellation.center.z,
             constellation.nameID])

        for solarSystemID, solarSystem in self.mapSystemCache.iteritems():
            solarSystemName = localization.GetImportantByMessageID(solarSystem.nameID)
            self.evelocations.data[solarSystemID] = blue.DBRow(rowDescriptor, [solarSystemID,
             solarSystemName,
             solarSystem.center.x,
             solarSystem.center.y,
             solarSystem.center.z,
             solarSystem.nameID])

        localStations = {}
        if boot.role == 'client':
            localStations = self.PrimeStationCelestials()
        for row in self.stations:
            if boot.role == 'client' and row.stationID in localStations and localStations[row.stationID]['isConquerable'] != 1:
                stationName = self.GetNPCStationNameFromLocalRow(localStations[row.stationID])
            else:
                stationName = row.stationName
            self.evelocations.data[row.stationID] = blue.DBRow(rowDescriptor, [row.stationID,
             stationName,
             row.x,
             row.y,
             row.z,
             None])

    @telemetry.ZONE_METHOD
    def PrimeStationCelestials(self):
        if boot.role != 'client':
            raise RuntimeError('PrimeStationCelestials::Non-client based call to PrimeStationCelestials!')
        sql = 'SELECT *\n                   FROM npcStations\n              '
        stations = self.mapObjectsDb.execute(sql)
        localStations = {}
        primeList = []
        for station in stations:
            if station['orbitID'] is not None:
                primeList.append(station['orbitID'])
            localStations[station['stationID']] = station

        cfg.evelocations.Prime(primeList)
        return localStations

    @telemetry.ZONE_METHOD
    def GetMarketGroup(self, marketGroupID):
        if boot.role != 'client':
            raise RuntimeError('GetMarketGroup::Non-clientbased call made!!')
        marketGroup = utillib.KeyVal()
        sql = '\n                SELECT *\n                  FROM marketGroups\n                 WHERE marketGroupID = %d\n              ' % marketGroupID
        row = self.localdb.execute(sql).fetchone()
        marketGroup.marketGroupID = row['marketGroupID']
        marketGroup.parentGroupID = row['parentGroupID']
        marketGroup.description = localization.GetByMessageID(row['descriptionID'])
        marketGroup.marketGroupName = localization.GetByMessageID(row['marketGroupNameID'])
        marketGroup.iconID = row['iconID']
        return marketGroup

    @telemetry.ZONE_METHOD
    def GetTypesRequiredBySkill(self, skillTypeID):
        if boot.role != 'client':
            raise RuntimeError('GetTypesRequiredBySkill::Non-clientbased call made!!')
        sql = '\n                SELECT *\n                  FROM typeSkillReqs\n                 WHERE skillTypeID = %d\n              ' % skillTypeID
        skillReqs = {}
        rs = self.localdb.execute(sql)
        for row in rs:
            skillLevel = row['skillLevel']
            marketGroupID = row['marketGroupID']
            metaLevel = row['metaLevel']
            typeID = row['typeID']
            if metaLevel not in const.metaGroupsUsed:
                metaLevel = const.metaGroupUnused
            if skillLevel not in skillReqs:
                skillReqs[skillLevel] = {}
            if marketGroupID not in skillReqs[skillLevel]:
                skillReqs[skillLevel][marketGroupID] = {}
            if metaLevel not in skillReqs[skillLevel][marketGroupID]:
                skillReqs[skillLevel][marketGroupID][metaLevel] = []
            skillReqs[skillLevel][marketGroupID][metaLevel].append(row['typeID'])

        return skillReqs

    @telemetry.ZONE_METHOD
    def GetLocationsLocalBySystem(self, solarSystemID, requireLocalizedTexts = True, doYields = False):
        """
            This method will dip into the local map db and return locations by systemID.
            Nothing will get primed as stuff has already been primed for the clients current system and there's no
            reason to bloat up memory usage because the user is browsing far-away systems.
            
            We cannot access this data from cfg because locations are not indexed by their location. That way lies madness.
        """
        if boot.role != 'client':
            raise RuntimeError('GetLocationsLocalBySystem::Non-clientbased call made!!')
        solarSystemObjectRowDescriptor = blue.DBRowDescriptor((('groupID', const.DBTYPE_I4),
         ('typeID', const.DBTYPE_I4),
         ('itemID', const.DBTYPE_I4),
         ('itemName', const.DBTYPE_WSTR),
         ('locationID', const.DBTYPE_I4),
         ('orbitID', const.DBTYPE_I4),
         ('connector', const.DBTYPE_BOOL),
         ('x', const.DBTYPE_R5),
         ('y', const.DBTYPE_R5),
         ('z', const.DBTYPE_R5),
         ('celestialIndex', const.DBTYPE_I4),
         ('orbitIndex', const.DBTYPE_I4)))
        sql = ' SELECT *\n                    FROM celestials\n                   WHERE solarSystemID = %d' % solarSystemID
        data = []
        rs = self.mapObjectsDb.execute(sql)
        for row in rs:
            try:
                celestialName = self.GetCelestialNameFromLocalRow(row, requireLocalizedTexts)
                data.append(blue.DBRow(solarSystemObjectRowDescriptor, [row['groupID'],
                 row['typeID'],
                 row['celestialID'],
                 celestialName,
                 solarSystemID,
                 row['orbitID'],
                 0,
                 row['x'],
                 row['y'],
                 row['z'],
                 row['celestialIndex'],
                 row['orbitIndex']]))
            except IndexError as e:
                rowContents = 'Row: '
                if row:
                    rowContents = ', '.join([ '%s=%s' % (key, row[key]) for key in row.keys() ])
                error = 'GetLocationsLocalBySystem: Failed getting local celestial data!\nRow is: %s\nError is: %s' % (rowContents, e)
                self.LogError(error)

            if doYields:
                blue.synchro.Yield()

        sql = '\n                SELECT *\n                  FROM npcStations\n                 WHERE solarSystemID = %d\n              ' % solarSystemID
        rs = self.mapObjectsDb.execute(sql)
        for row in rs:
            try:
                celestialName = self.GetNPCStationNameFromLocalRow(row, requireLocalizedTexts)
                data.append(blue.DBRow(solarSystemObjectRowDescriptor, [cfg.invtypes.Get(row['typeID']).groupID,
                 row['typeID'],
                 row['stationID'],
                 celestialName,
                 solarSystemID,
                 row['orbitID'],
                 0,
                 row['x'],
                 row['y'],
                 row['z'],
                 row['celestialIndex'],
                 row['orbitIndex']]))
            except IndexError as e:
                rowContents = 'Row: '
                if row:
                    rowContents = ', '.join([ '%s=%s' % (key, row[key]) for key in row.keys() ])
                error = 'GetLocationsLocalBySystem: Failed getting local station data!\nRow is: %s\nError is: %s' % (rowContents, e)
                self.LogError(error)

            if doYields:
                blue.synchro.Yield()

        data = CRowset(solarSystemObjectRowDescriptor, data)
        return data

    @telemetry.ZONE_METHOD
    def GetLocationsLocal(self, keys):
        if boot.role != 'client':
            raise RuntimeError('GetLocationsLocal::Non-clientbased call made!!')
        rowDescriptor = self.GetLocationRowDescriptor()
        data = []
        keyString = ','.join([ str(x) for x in keys ])
        sql = 'SELECT *\n                   FROM celestials\n                  WHERE celestialID IN (%s)' % keyString
        rs = self.mapObjectsDb.execute(sql)
        for row in rs:
            celestialNameData = self._GetCelestialNameDataFromLocalRow(row)
            self.rawCelestialCache[row['celestialID']] = celestialNameData
            celestialName = localization.GetImportantByLabel(celestialNameData[0], **celestialNameData[1])
            data.append(blue.DBRow(rowDescriptor, [row['celestialID'],
             celestialName,
             row['x'],
             row['y'],
             row['z'],
             None]))

        data = CRowset(rowDescriptor, data)
        return (data.columns, data)

    @telemetry.ZONE_METHOD
    def GetNPCStationNameFromLocalRow(self, row, requireLocalizedTexts = True):
        """
            Formats NPC station names based on the owner and operation ID.
            
            Because this location formatter involves a generic string, we have to manually handle
            supporting bilingual functionality by generating the normal and english texts and passing
            them both into the localization system.
        """
        if not requireLocalizedTexts:
            return ''
        if row['useOperationName']:
            labelPath = 'UI/Locations/LocationNPCStationFormatter'
            operationNameID = cfg.staoperationtypes.Get(row['operationID']).operationNameID
            operationName = localization.GetByMessageID(operationNameID)
            operationNameEN = localization.GetByMessageID(operationNameID, localization.const.LOCALE_SHORT_ENGLISH)
        else:
            labelPath = 'UI/Locations/LocationNPCStationFormatter_NoOpName'
            operationName = ''
            operationNameEN = ''
        locName = localization.GetByLabel(labelPath, orbitID=row['orbitID'], corporationID=row['ownerID'], operationName=operationName)
        locNameEN = localization.GetByLabel(labelPath, localization.const.LOCALE_SHORT_ENGLISH, orbitID=row['orbitID'], corporationID=row['ownerID'], operationName=operationNameEN)
        return localization.FormatImportantString(locName, locNameEN)

    @telemetry.ZONE_METHOD
    def _GetCelestialNameDataFromLocalRow(self, row):
        """
            Utility method to get the cerberus elements which make up 
        """
        celestialGroupID = row['groupID']
        celestialNameID = row['celestialNameID']
        celestialNameData = (None, None)
        if celestialNameID is not None and celestialGroupID != const.groupStargate:
            celestialNameData = ('UI/Util/GenericText', {'text': celestialNameID})
        elif celestialGroupID == const.groupAsteroidBelt:
            celestialNameData = ('UI/Locations/LocationAsteroidBeltFormatter', {'solarSystemID': row['solarSystemID'],
              'romanCelestialIndex': formatUtil.IntToRoman(row['celestialIndex']),
              'typeID': row['typeID'],
              'orbitIndex': row['orbitIndex']})
        elif celestialGroupID == const.groupMoon:
            celestialNameData = ('UI/Locations/LocationMoonFormatter', {'solarSystemID': row['solarSystemID'],
              'romanCelestialIndex': formatUtil.IntToRoman(row['celestialIndex']),
              'orbitIndex': row['orbitIndex']})
        elif celestialGroupID == const.groupPlanet:
            celestialNameData = ('UI/Locations/LocationPlanetFormatter', {'solarSystemID': row['solarSystemID'],
              'romanCelestialIndex': formatUtil.IntToRoman(row['celestialIndex'])})
        elif celestialGroupID == const.groupStargate:
            celestialNameData = ('UI/Locations/LocationStargateFormatter', {'destinationSystemID': row['celestialNameID']})
        elif celestialGroupID == const.groupSun:
            celestialNameData = ('UI/Locations/LocationStarFormatter', {'solarSystemID': row['solarSystemID']})
        return celestialNameData

    @telemetry.ZONE_METHOD
    def GetCelestialNameFromLocalRow(self, row, requireLocalizedTexts = True):
        """
            Common method to resolve sqlite3 mapdb row to its celestial name.
        """
        if not requireLocalizedTexts:
            return ''
        lbl, kwargs = self._GetCelestialNameDataFromLocalRow(row)
        if lbl:
            return localization.GetByLabel(lbl, **kwargs)

    def ReloadLocalizedNames(self):
        """
            Reload any cfg object that depends on using localized names
        """
        self.LoadEveOwners()
        self.LoadEveLocations()

    def GetShipGroupByClassType(self):
        try:
            return self.shipGroupByClassType
        except AttributeError:
            self.shipGroupByClassType = {const.GROUP_CAPSULES: (const.groupCapsule,),
             const.GROUP_FRIGATES: (const.groupShuttle,
                                    const.groupRookieship,
                                    const.groupFrigate,
                                    const.groupAssaultShip,
                                    const.groupCovertOps,
                                    const.groupElectronicAttackShips,
                                    const.groupPrototypeExplorationShip,
                                    const.groupInterceptor,
                                    const.groupStealthBomber,
                                    const.groupExpeditionFrigate),
             const.GROUP_DESTROYERS: (const.groupDestroyer, const.groupInterdictor, const.groupTacticalDestroyer),
             const.GROUP_CRUISERS: (const.groupCruiser,
                                    const.groupStrategicCruiser,
                                    const.groupCombatReconShip,
                                    const.groupForceReconShip,
                                    const.groupHeavyAssaultShip,
                                    const.groupHeavyInterdictors,
                                    const.groupLogistics),
             const.GROUP_BATTLECRUISERS: (const.groupBattlecruiser, const.groupAttackBattlecruiser, const.groupCommandShip),
             const.GROUP_BATTLESHIPS: (const.groupBattleship, const.groupBlackOps, const.groupMarauders),
             const.GROUP_CAPITALSHIPS: (const.groupCarrier,
                                        const.groupCapitalIndustrialShip,
                                        const.groupDreadnought,
                                        const.groupTitan,
                                        const.groupSupercarrier),
             const.GROUP_INDUSTRIALS: (const.groupBlockadeRunner,
                                       const.groupExhumer,
                                       const.groupFreighter,
                                       const.groupIndustrial,
                                       const.groupIndustrialCommandShip,
                                       const.groupJumpFreighter,
                                       const.groupMiningBarge,
                                       const.groupTransportShip),
             const.GROUP_POS: tuple((groupObj.groupID for groupObj in self.groupsByCategories[const.categoryStructure]))}

        return self.shipGroupByClassType

    def GetShipClassTypeByGroupID(self, groupID):
        for classTypeID, groupIDs in self.GetShipGroupByClassType().iteritems():
            if groupID in groupIDs:
                return classTypeID

    def CheckLocalDBVersion(self):

        def IncorrectVersion():
            import carbonui.const as uiconst
            eve.Message('BadMapBulkVersion', {}, uiconst.OK)
            bluepy.Terminate()

        sql = 'SELECT * FROM version'
        try:
            versionCheck = self.localdb.execute(sql)
            if versionCheck.rowcount == 0:
                IncorrectVersion()
        except:
            IncorrectVersion()

        version = versionCheck.fetchone()
        if version['bulkVersion'] != BULKVERSION:
            IncorrectVersion()

    @telemetry.ZONE_METHOD
    def GetMoonMinerals(self, moonID):
        """
        Return a dict describing the minerals present in that moon.
        {typeID1:quantity1, typeID2:quantity2, ...}
        """
        if boot.role != 'server':
            raise RuntimeError('GetMoonMinerals: Only supported on server')
        try:
            return dict(self._moonMinerals[moonID])
        except KeyError:
            return {}

    @telemetry.ZONE_METHOD
    def GetMoonMineralQuantity(self, moonID, typeID):
        """
        Return the quantity of a particular mineral available from a moon.
        If the requested type is not present at the moon, return 0
        """
        if boot.role != 'server':
            raise RuntimeError('GetMoonMineralQuantity: Only supported on server')
        try:
            return self._moonMinerals[moonID][typeID]
        except KeyError:
            return 0


def GetStrippedEnglishMessage(messageID):
    """
        Returns the English-language messages, stripped of any hard-coded string formatting tags.
        Used for situations where we need the raw English name, such as invtypes._typeName.
        If the messageID is none or the message doesn't exist, this returns an empty string
    """
    msg = localization._GetRawByMessageID(messageID, 'en-us')
    if msg:
        regex = '</localized>|<localized>|<localized .*?>|<localized *=.*?>'
        return ''.join(re.split(regex, msg))
    else:
        return ''


class InvGroup(sysCfg.Row):
    __guid__ = 'eveCfg.InvGroup'

    def Parent(self):
        return cfg.invgroups.Get(self.parentID)

    def Category(self):
        return cfg.invcategories.Get(self.categoryID)

    def Types(self):
        data = []
        for t in cfg.invtypes:
            if t.groupID == self.id:
                data.append(t.line)

        return sysCfg.Recordset(InvType, 'typeID', (cfg.invtypes.header, data))

    def __getattr__(self, name):
        if name == '_groupName':
            return GetStrippedEnglishMessage(self.groupNameID)
        if name == 'name':
            name = 'groupName'
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'groupName':
            return localization.GetImportantByMessageID(self.groupNameID)
        return value

    def __str__(self):
        try:
            cat = self.Category()
            return 'InvGroup ID: %d, category: %d %s,  "%s"' % (self.groupID,
             cat.id,
             cat.name,
             self.groupName)
        except:
            sys.exc_clear()
            return 'InvGroup containing crappy data'


class InvCategory(sysCfg.Row):
    __guid__ = 'eveCfg.InvCategory'

    def __getattr__(self, name):
        if name == '_categoryName':
            return GetStrippedEnglishMessage(self.categoryNameID)
        if name == 'name' or name == 'description':
            name = 'categoryName'
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'categoryName':
            return localization.GetImportantByMessageID(self.categoryNameID)
        return value

    def __str__(self):
        return 'InvCategory ID: %d,   "%s"' % (self.categoryID, self.categoryName)

    def IsHardware(self):
        return self.id == const.categoryModule or self.id == const.categoryImplant or self.id == const.categorySubSystem


class InvType(sysCfg.Row):
    __guid__ = 'eveCfg.InvType'

    def Category(self):
        return cfg.invcategories.Get(self.categoryID)

    def Group(self):
        return cfg.invgroups.Get(self.groupID)

    def GetFSDType(self, typeID):
        typeIDObject = None
        if cfg.fsdTestTypeOverrides is not None:
            try:
                typeIDObject = cfg.fsdTypeOverrides.Get(typeID)
            except KeyError:
                typeIDObject = cfg.fsdTestTypeOverrides.Get(typeID)

        else:
            typeIDObject = cfg.fsdTypeOverrides.Get(typeID)
        return typeIDObject

    def GraphicID(self):
        graphicID = sysCfg.Row.__getattr__(self, 'graphicID')
        if cfg.fsdTypeOverrides is not None:
            try:
                with telemetry.TelemetryContext('eveCfg.InvType.typeID.graphicID'):
                    graphicID = self.GetFSDType(self.id).graphicID
            except KeyError:
                pass
            except AttributeError:
                pass

        return graphicID

    def Graphic(self):
        try:
            graphicID = self.GraphicID()
            if graphicID is not None:
                with telemetry.TelemetryContext('eveCfg.InvType.graphic'):
                    return cfg.graphics.Get(graphicID)
            else:
                return
        except Exception:
            return

    def GraphicFile(self):
        try:
            return self.Graphic().graphicFile
        except Exception:
            return ''

    def IconID(self):
        iconID = sysCfg.Row.__getattr__(self, 'iconID')
        if cfg.fsdTypeOverrides is not None:
            try:
                iconID = self.GetFSDType(self.id).iconID
            except KeyError:
                pass
            except AttributeError:
                pass

        return iconID

    def Icon(self):
        if self.id >= const.minDustTypeID:
            return cfg.fsdDustIcons.get(self.id, None)
        try:
            if self.iconID is not None:
                return cfg.icons.Get(self.iconID)
            return
        except Exception:
            return

    def IconFile(self):
        try:
            return cfg.icons.Get(self.iconID).iconFile
        except Exception:
            return ''

    def Radius(self):
        radius = sysCfg.Row.__getattr__(self, 'radius')
        if cfg.fsdTypeOverrides is not None:
            try:
                typeOverride = self.GetFSDType(self.id)
                return typeOverride.radius
            except KeyError:
                pass
            except AttributeError:
                pass

        return radius

    def SoundID(self):
        soundID = sysCfg.Row.__getattr__(self, 'soundID')
        if cfg.fsdTypeOverrides is not None:
            try:
                soundID = self.GetFSDType(self.id).soundID
            except KeyError:
                pass
            except AttributeError:
                pass

        return soundID

    def Sound(self):
        try:
            if self.soundID is not None:
                return cfg.sounds.Get(self.soundID)
            return
        except Exception:
            return

    def Illegality(self, factionID = None):
        """
        Returns the "illegality" of the type, either as a map of factionID:effect or as a single effect category.
        None means the type is considered legal by the faction.
        """
        if factionID:
            return cfg.invcontrabandFactionsByType.get(self.id, {}).get(factionID, None)
        else:
            return cfg.invcontrabandFactionsByType.get(self.id, {})

    def HardwareType(self):
        raise RuntimeError('Not implemented at the moment')

    def ShipType(self):
        return cfg.shiptypes.Get(self.id)

    @property
    def adjustedAveragePrice(self):
        try:
            return cfg._averageMarketPrice[self.typeID].adjustedPrice
        except KeyError:
            return None

    @property
    def averagePrice(self):
        try:
            return cfg._averageMarketPrice[self.typeID].averagePrice
        except KeyError:
            return None

    def GetLocalized(self, name, languageID = None):
        if name == '_typeName':
            return GetStrippedEnglishMessage(self.typeNameID)
        if name == 'name':
            name = 'typeName'
        if name == 'categoryID':
            return cfg.invgroups.Get(self.groupID).categoryID
        elif name == 'graphicID':
            return self.GraphicID()
        elif name == 'soundID':
            return self.SoundID()
        elif name == 'iconID':
            return self.IconID()
        elif name == 'radius':
            return self.Radius()
        elif name == 'typeName':
            return localization.GetImportantByMessageID(self.typeNameID)
        elif name == 'typeNameTranslatedOnly':
            return localization.GetByMessageID(self.typeNameID)
        elif name == 'description':
            return localization.GetByMessageID(self.descriptionID, languageID)
        else:
            return sysCfg.Row.__getattr__(self, name)

    def __getattr__(self, name):
        return self.GetLocalized(name)

    def GetRawName(self, languageID = None):
        return localization.GetByMessageID(self.typeNameID, languageID)

    def __str__(self):
        return 'InvType ID: %d, group: %d,  "%s"' % (self.typeID, self.groupID, self.typeName)


class Region(sysCfg.Row):
    __guid__ = 'eveCfg.Region'

    def __getattr__(self, name):
        if name == 'regionName':
            if self.regionID < const.mapWormholeRegionMin:
                return sysCfg.Row.__getattr__(self, 'regionName')
            else:
                return 'Unknown'
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'Region ID: %d, name: %s' % (self.regionID, self.regionName)


class Constellation(sysCfg.Row):
    __guid__ = 'eveCfg.Constellation'

    def __getattr__(self, name):
        if name == 'constellationName':
            if self.constellationID < const.mapWormholeConstellationMin:
                return sysCfg.Row.__getattr__(self, 'constellationName')
            else:
                return 'Unknown'
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'Constellation ID: %d, name: %s' % (self.constellationID, self.constellationName)


class SolarSystem(sysCfg.Row):
    __guid__ = 'eveCfg.SolarSystem'

    def __getattr__(self, name):
        if name == 'pseudoSecurity':
            value = sysCfg.Row.__getattr__(self, 'security')
            if value > 0.0 and value < 0.05:
                return 0.05
            else:
                return value
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'SolarSystem ID: %d, name: %s' % (self.solarSystemID, self.solarSystemName)


def StackSize(item):
    """
    Returns the number of items in a stack in a blue.DBRow obtained from 
    the inventory system.  
    Intended as a callable for the '.stacksize' virtual column. 
    Other uses are at the callers risk.
    """
    if item[const.ixQuantity] < 0:
        return 1
    return item[const.ixQuantity]


def Singleton(item):
    """
    Returns non-zero if blue.DBRow item, obtained from the inventory system, is 
    a singleton, zero otherwise.
    Intended as a callable for the '.singleton' virtual column. Other uses are at the
    callers risk.
    """
    if item[const.ixQuantity] < 0:
        return -item[const.ixQuantity]
    if 30000000 <= item[const.ixLocationID] < 40000000:
        return 1
    return 0


def RamActivityVirtualColumn(row):
    return cfg.ramaltypes.Get(row.assemblyLineTypeID).activityID


def IsSystem(ownerID):
    return ownerID <= 10000


def IsDustType(typeID):
    return typeID > const.minDustTypeID


def IsNPCCorporation(ownerID):
    return ownerID < 2000000 and ownerID >= 1000000


def IsNPCCharacter(ownerID):
    return ownerID < 4000000 and ownerID >= 3000000


def IsSystemOrNPC(ownerID):
    return ownerID < 90000000


def IsFaction(ownerID):
    if ownerID >= 500000 and ownerID < 1000000:
        return 1
    else:
        return 0


def IsCorporation(ownerID):
    if ownerID >= 1000000 and ownerID < 2000000:
        return 1
    if ownerID < 98000000 or ownerID > 2147483647:
        return 0
    if ownerID < 99000000:
        return 1
    if ownerID < 100000000:
        return 0
    if boot.role == 'server' and sm.GetService('standing2').IsKnownToBeAPlayerCorp(ownerID):
        return 1
    try:
        return cfg.eveowners.Get(ownerID).IsCorporation()
    except KeyError:
        return 0


def IsCharacter(ownerID):
    if ownerID >= 3000000 and ownerID < 4000000:
        return 1
    if ownerID < 90000000 or ownerID > 2147483647:
        return 0
    if ownerID < 98000000:
        return 1
    if ownerID < 100000000:
        return 0
    if boot.role == 'server' and sm.GetService('standing2').IsKnownToBeAPlayerCorp(ownerID):
        return 0
    try:
        return cfg.eveowners.Get(ownerID).IsCharacter()
    except KeyError:
        return 0


def IsPlayerAvatar(itemID):
    return IsCharacter(itemID)


def IsOwner(ownerID, fetch = 1):
    if ownerID >= 500000 and ownerID < 1000000 or ownerID >= 1000000 and ownerID < 2000000 or ownerID >= 3000000 and ownerID < 4000000:
        return 1
    if IsNPC(ownerID):
        return 0
    if ownerID < 90000000 or ownerID > 2147483647:
        return 0
    if ownerID < 100000000:
        return 1
    if fetch:
        try:
            oi = cfg.eveowners.Get(ownerID)
        except KeyError:
            return 0

        if oi.groupID in (const.groupCharacter, const.groupCorporation, const.groupAlliance):
            return 1
        else:
            return 0
    else:
        return 0


def IsAlliance(ownerID):
    if ownerID < 99000000 or ownerID > 2147483647:
        return 0
    if ownerID < 100000000:
        return 1
    if boot.role == 'server' and sm.GetService('standing2').IsKnownToBeAPlayerCorp(ownerID):
        return 0
    try:
        return cfg.eveowners.Get(ownerID).IsAlliance()
    except KeyError:
        return 0


def IsUniverseCelestial(itemID):
    return itemID >= const.minUniverseCelestial and itemID <= const.maxUniverseCelestial


def IsDistrict(itemID):
    return itemID >= const.minDistrict and itemID <= const.maxDistrict


def IsStargate(itemID):
    return itemID >= 50000000 and itemID < 60000000


def IsWorldSpace(itemID):
    return itemID >= const.mapWorldSpaceMin and itemID < const.mapWorldSpaceMax


def IsOutpost(itemID):
    return itemID >= 61000000 and itemID < 64000000


def IsTrading(itemID):
    return itemID >= 64000000 and itemID < 66000000


def IsOfficeFolder(itemID):
    return itemID >= 66000000 and itemID < 68000000


def IsFactoryFolder(itemID):
    return itemID >= 68000000 and itemID < 70000000


def IsUniverseAsteroid(itemID):
    return itemID >= 70000000 and itemID < 80000000


def IsJunkLocation(locationID):
    if locationID >= 2000:
        return 0
    elif locationID in (6, 8, 10, 23, 25):
        return 1
    elif locationID > 1000 and locationID < 2000:
        return 1
    else:
        return 0


def IsControlBunker(itemID):
    return itemID >= 80000000 and itemID < 80100000


def IsPlayerItem(itemID):
    return itemID >= const.minPlayerItem and itemID < const.minFakeItem


def IsFakeItem(itemID):
    return itemID > const.minFakeItem


def IsNewbieSystem(itemID):
    default = [30002547,
     30001392,
     30002715,
     30003489,
     30005305,
     30004971,
     30001672,
     30002505,
     30000141,
     30003410,
     30005042,
     30001407]
    return itemID in default


def IsStructure(categoryID):
    return categoryID in (const.categorySovereigntyStructure, const.categoryStructure)


def IsOrbital(categoryID):
    return categoryID == const.categoryOrbital


def IsPreviewable(typeID):
    """ Should it be possible to open up a 3D-preview window for an item of this type? """
    type = cfg.invtypes.GetIfExists(typeID)
    if type is None:
        return False
    groupID = type.groupID
    categoryID = type.categoryID
    return categoryID in const.previewCategories or groupID in const.previewGroups


def IsApparel(typeID):
    typeInfo = cfg.invtypes.GetIfExists(typeID)
    if typeInfo is None:
        return False
    return typeInfo.categoryID == const.categoryApparel


def IsBlueprint(typeID):
    typeInfo = cfg.invtypes.GetIfExists(typeID)
    if typeInfo is None:
        return False
    return typeInfo.categoryID == const.categoryBlueprint


def IsPlaceable(typeID):
    type = cfg.invtypes.GetIfExists(typeID)
    if type is None:
        return False
    return const.categoryPlaceables == type.categoryID


def IsEveUser(userID):
    if userID < const.minDustUser:
        return True
    return False


def IsDustUser(userID):
    if userID > const.minDustUser:
        return True
    return False


def IsDustCharacter(characterID):
    if characterID > const.minDustCharacter and characterID < const.maxDustCharacter:
        return True
    return False


def IsEvePlayerCharacter(ownerID):
    return IsCharacter(ownerID) and not IsDustCharacter(ownerID) and not IsNPC(ownerID)


def IsPlayerOwner(ownerID):
    if ownerID >= const.minPlayerOwner and ownerID <= const.maxPlayerOwner:
        return True
    return False


def GetCharacterType(characterID):
    if IsEveUser(characterID):
        return 'capsuleer'
    elif IsDustCharacter(characterID):
        return 'mercenary'
    else:
        return 'unknown'


def IsOutlawStatus(securityStatus):
    return round(securityStatus, 1) <= const.outlawSecurityStatus


OWNER_NAME_OVERRIDES = {OWNER_AURA_IDENTIFIER: 'UI/Agents/AuraAgentName',
 OWNER_SYSTEM_IDENTIFIER: 'UI/Chat/ChatEngine/EveSystem'}

class EveOwners(sysCfg.Row):
    __guid__ = 'cfg.EveOwners'

    def __getattr__(self, name):
        if name == 'name' or name == 'description':
            name = 'ownerName'
        elif name == 'groupID':
            if self.typeID is not None:
                return cfg.invtypes.Get(self.typeID).groupID
            return
        if name == 'ownerName' and boot.role != 'client' and self.ownerNameID is not None:
            return localization.GetByMessageID(self.ownerNameID)
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'EveOwner ID: %d, "%s"' % (self.ownerID, self.ownerName)

    def GetRawName(self, languageID = None):
        if self.ownerNameID is not None:
            if self.ownerNameID in OWNER_NAME_OVERRIDES:
                return localization.GetByLabel(OWNER_NAME_OVERRIDES[self.ownerNameID], languageID)
            return localization.GetByMessageID(self.ownerNameID, languageID)
        return self.name

    def IsSystem(self):
        return self.ownerID <= 15

    def IsNPC(self):
        return IsNPC(self.ownerID)

    def IsCharacter(self):
        return self.groupID == const.groupCharacter

    def IsCorporation(self):
        return self.groupID == const.groupCorporation

    def IsAlliance(self):
        return self.typeID == const.typeAlliance

    def IsFaction(self):
        return self.groupID == const.groupFaction

    def Type(self):
        return cfg.invtypes.Get(self.typeID)

    def Group(self):
        return cfg.invgroups.Get(self.groupID)


class CrpTickerNames(sysCfg.Row):
    __guid__ = 'cfg.CrpTickerNames'

    def __getattr__(self, name):
        if name == 'name' or name == 'description':
            return self.tickerName
        else:
            return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'CorpTicker ID: %d, "%s"' % (self.corporationID, self.tickerName)


class DgmAttribute(sysCfg.Row):
    __guid__ = 'cfg.DgmAttribute'

    def __getattr__(self, name):
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'displayName':
            if len(value) == 0:
                value = self.attributeName
            value = localization.GetByMessageID(self.displayNameID)
        return value


class DgmEffect(sysCfg.Row):
    __guid__ = 'cfg.DgmEffect'

    def __getattr__(self, name):
        if name == 'displayName':
            return localization.GetByMessageID(self.displayNameID)
        if name == 'description':
            return localization.GetByMessageID(self.descriptionID)
        return sysCfg.Row.__getattr__(self, name)


class DgmUnit(sysCfg.Row):
    __guid__ = 'cfg.DgmUnit'

    def __getattr__(self, name):
        if name == 'displayName':
            return localization.GetByMessageID(self.displayNameID)
        if name == 'description':
            return localization.GetByMessageID(self.descriptionID)
        return sysCfg.Row.__getattr__(self, name)


class AllShortNames(sysCfg.Row):
    __guid__ = 'cfg.AllShortNames'

    def __getattr__(self, name):
        if name == 'name' or name == 'description':
            return self.shortName
        else:
            return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'AllianceShortName ID: %d, "%s"' % (self.allianceID, self.shortName)


class EveLocations(sysCfg.Row):
    __guid__ = 'dbrow.Location'

    def __setattr__(self, name, value):
        if name in ('id', 'header', 'line', 'locationName'):
            self.__dict__[name] = value
        else:
            raise RuntimeError('ReadOnly', name)

    def __getattr__(self, name):
        if name == 'name' or name == 'description' or name == 'locationName':
            locationName = sysCfg.Row.__getattr__(self, 'locationName')
            if (locationName is None or len(locationName) == 0) and self.locationNameID is not None:
                if isinstance(self.locationNameID, (int, long)):
                    locationName = localization.GetImportantByMessageID(self.locationNameID)
                elif isinstance(self.locationNameID, tuple):
                    locationName = localization.GetImportantByLabel(self.locationNameID[0], **self.locationNameID[1])
                if boot.role == 'client':
                    setattr(self, 'locationName', locationName)
            elif boot.role != 'client' and self.locationNameID is not None:
                locationName = localization.GetByMessageID(self.locationNameID)
            return locationName
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'EveLocation ID: %d, "%s"' % (self.locationID, self.locationName)

    def GetRawName(self, languageID = None):
        if self.locationNameID is not None:
            return localization.GetByMessageID(self.locationNameID, languageID)
        if self.locationID in cfg.rawCelestialCache:
            lbl, kwargs = cfg.rawCelestialCache[self.locationID]
            return localization.GetByLabel(lbl, languageID, **kwargs)
        return self.name

    def Station(self):
        return cfg.GetSvc('stationSvc').GetStation(self.id)


class RamCompletedStatus(sysCfg.Row):
    __guid__ = 'cfg.RamCompletedStatus'

    def __getattr__(self, name):
        if name == 'name':
            name = 'completedStatusText'
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'completedStatusText':
            value = localization.GetByMessageID(self.completedStatusTextID)
        elif name == 'description':
            return localization.GetByMessageID(self.descriptionID)
        return value

    def __str__(self):
        try:
            return 'RamCompletedStatus ID: %d, "%s"' % (self.completedStatus, self.completedStatusText)
        except:
            sys.exc_clear()
            return 'RamCompletedStatus containing crappy data'


class RamActivity(sysCfg.Row):
    __guid__ = 'cfg.RamActivity'

    def __getattr__(self, name):
        if name in ('activityName', 'name'):
            return localization.GetByMessageID(self.activityNameID)
        if name == 'description':
            return localization.GetByMessageID(self.descriptionID)
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        try:
            return 'RamActivity ID: %d, "%s"' % (self.activityID, self.activityName)
        except:
            sys.exc_clear()
            return 'RamActivity containing crappy data'


class MapCelestialDescription(sysCfg.Row):
    __guid__ = 'cfg.MapCelestialDescription'

    def __getattr__(self, name):
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'description':
            value = localization.GetByMessageID(self.descriptionID)
        return value

    def __str__(self):
        return 'MapCelestialDescriptions ID: %d' % self.itemID


class InvMetaGroup(sysCfg.Row):
    __guid__ = 'cfg.InvMetaGroup'

    def __getattr__(self, name):
        if name == '_metaGroupName':
            return GetStrippedEnglishMessage(self.metaGroupNameID)
        if name == 'name':
            name = 'metaGroupName'
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'metaGroupName':
            return localization.GetByMessageID(self.metaGroupNameID)
        return value

    def __str__(self):
        try:
            cat = self.Category()
            return 'InvMetaGroup ID: %d, "%s", "%s", "%s"' % (self.metaGroupID,
             cat.id,
             cat.name,
             self.metaGroupName)
        except:
            sys.exc_clear()
            return 'InvMetaGroup containing crappy data'


class Schematic(sysCfg.Row):
    __guid__ = 'cfg.Schematic'

    def __getattr__(self, name):
        if name == 'schematicName':
            return localization.GetByMessageID(self.schematicNameID)
        return sysCfg.Row.__getattr__(self, name)

    def __str__(self):
        return 'Schematic: %s (%d)' % (self.schematicName, self.schematicID)

    def __cmp__(self, other):
        if type(other) == types.IntType:
            return types.IntType.__cmp__(self.schematicID, other)
        else:
            return sysCfg.Row.__cmp__(self, other)


class Billtype(sysCfg.Row):
    __guid__ = 'cfg.Billtype'

    def __getattr__(self, name):
        value = sysCfg.Row.__getattr__(self, name)
        if name == 'billTypeName':
            value = localization.GetByMessageID(self.billTypeNameID)
        return value

    def __str__(self):
        return 'Billtype ID: %d' % self.billTypeID


class InvItem2(sysCfg.Row):
    __guid__ = 'eveCfg.InvItem2'

    def __init__(self, recordset, key, customfields = None):
        sysCfg.Row.__init__(self, recordset, key)
        self.__dict__['customfields'] = customfields

    def __getattr__(self, name):
        customfields = self.__dict__['customfields']
        if customfields is not None and name in customfields:
            fieldindex = customfields.index(name)
            return sysCfg.Row.__getattr__(self, 'customInfo')[fieldindex]
        else:
            return sysCfg.Row.__getattr__(self, name)

    def __repr__(self):
        ret = sysCfg.Row.__repr__(self)
        fields = self.customfields
        if fields is not None:
            for i in xrange(len(fields)):
                ret = ret + '%s:%s%s\r\n' % (fields[i], ' ' * (23 - len(fields[i])), self.__getattr__(fields[i]))

        return ret

    def Type(self):
        return cfg.invtypes.Get(self.typeID)

    def Group(self):
        return cfg.invgroups.Get(self.groupID)

    def Category(self):
        return cfg.invcategories.Get(self.categoryID)

    def Owner(self):
        return cfg.eveowners.Get(self.ownerID)

    def Location(self):
        return cfg.evelocations.Get(self.locationID)


class InvBall(InvItem2):

    def __init__(self, recordset, key, fields = []):
        InvItem2.__init__(self, recordset, key, ['x',
         'y',
         'z',
         'radius'] + fields)

    def __getattr__(self, name):
        if name == 'name':
            return cfg.evelocations.Get(self.itemID).name
        elif name == 'description':
            return cfg.evelocations.Get(self.itemID).description
        else:
            return InvItem2.__getattr__(self, name)


class PropertyBag():

    def __init__(self):
        self.Reset()

    def LoadFromMoniker(self, moniker_dict):
        import base64
        import cPickle
        self.__dict__['bag'] = cPickle.loads(base64.decodestring(moniker_dict))

    def GetMoniker(self):
        import base64
        import cPickle
        tupl = (self.__guid__, base64.encodestring(cPickle.dumps(self.__dict__['bag'])))
        return base64.encodestring(cPickle.dumps(tupl, 1)).rstrip()

    def AddProperty(self, propertyName, propertyValue):
        self.__dict__['bag'][propertyName] = propertyValue

    def HasProperty(self, propertyName):
        return self.__dict__['bag'].has_key(propertyName)

    def GetProperty(self, propertyName):
        if self.__dict__['bag'].has_key(propertyName):
            return self.__dict__['bag'][propertyName]

    def RemoveProperty(self, propertyName):
        if self.__dict__['bag'].has_key(propertyName):
            del self.__dict__['bag'][propertyName]

    def GetProperties(self):
        return self.__dict__['bag'].items()

    def Reset(self):
        self.__dict__['bag'] = {}


class OverviewDefault(sysCfg.Row):
    __guid__ = 'eveCfg.OverviewDefault'

    def __getattr__(self, name):
        if name == '_overviewName':
            return sysCfg.Row.__getattr__(self, 'overviewName')
        if name in ('name', 'overviewName'):
            return localization.GetByMessageID(self.overviewNameID)
        value = sysCfg.Row.__getattr__(self, name)
        return value

    def __str__(self):
        return 'DefaultOverview ID: %d, "%s"' % (self.overviewID, self.overviewName)


class Position(sysCfg.Row):
    __guid__ = 'cfg.Position'

    @property
    def latitude(self):
        return self.x

    @property
    def longitude(self):
        return self.y

    @property
    def radius(self):
        return self.z


class Faction(sysCfg.Row):
    __guid__ = 'cfg.Faction'

    def __getattr__(self, name):
        if name == 'factionName':
            return localization.GetImportantByMessageID(self.factionNameID)
        return sysCfg.Row.__getattr__(self, name)


class Race(sysCfg.Row):
    __guid__ = 'cfg.Race'

    def __getattr__(self, name):
        if name == 'raceName':
            return localization.GetImportantByMessageID(self.raceNameID)
        return sysCfg.Row.__getattr__(self, name)


def _LoadMessagesFromFSD():
    return fsdBinaryLoader.LoadFSDDataForCFG('res:/staticdata/dialogs.static', 'res:/staticdata/dialogs.schema', optimize=False)


def IsWarInHostileState(row):
    return evewar.util.IsWarInHostileState(row, blue.os.GetWallclockTime())


def IsWarActive(row):
    if row.timeFinished is None or blue.os.GetWallclockTime() < row.timeFinished:
        return 1
    return 0


def IsAllyActive(row, time = None):
    if time is None:
        time = blue.os.GetWallclockTime()
    return row.timeStarted < time < row.timeFinished


def IsAtWar(wars, entities):
    return evewar.util.IsAtWar(wars, entities, blue.os.GetWallclockTime())


def IsPolarisFrigate(typeID):
    return typeID in (const.typePolarisCenturion,
     const.typePolarisCenturionFrigate,
     const.typePolarisInspectorFrigate,
     const.typePolarisLegatusFrigate)


def GetReprocessingOptions(types):
    options = []
    optionTypes = {}
    noneTypes = [const.typeCredits, const.typeBookmark, const.typeBiomass]
    noneGroups = [const.groupRookieship, const.groupMineral]
    noneCategories = [const.categoryBlueprint, const.categoryReaction]
    for key in types.iterkeys():
        typeID = key
        isRecyclabe = 0
        isRefinable = 0
        typeInfo = cfg.invtypes.Get(typeID)
        if typeID not in noneTypes and typeInfo.groupID not in noneGroups and typeInfo.categoryID not in noneCategories:
            if typeID in cfg.invtypematerials:
                materials = cfg.invtypematerials[typeID]
                if len(materials) > 0:
                    if typeInfo.categoryID == const.categoryAsteroid or typeInfo.groupID == const.groupHarvestableCloud:
                        isRefinable = 1
                    else:
                        isRecyclabe = 1
        options.append(utillib.KeyVal(typeID=typeID, isRecyclable=isRecyclabe, isRefinable=isRefinable))

    for option in options:
        optionTypes[option.typeID] = option

    return optionTypes


def MakeConstantName(val, prefix):
    """
    Takes a name and turns it into a Python legal variable name.
    This involves removing all the homoerotica in the name like unicode characters or other non legal variable name characters.
    """
    name = val.replace(' ', '')
    if name == '':
        name = 'invalidName_' + val
    name = prefix + name[0].upper() + name[1:]
    ret = ''
    okey = range(ord('a'), ord('z') + 1) + range(ord('A'), ord('Z') + 1) + range(ord('0'), ord('9') + 1)
    for ch in name:
        if ord(ch) in okey:
            ret += ch

    if ret == '':
        ret = 'invalidName_' + ret
    elif ord(ret[0]) in range(ord('0'), ord('9') + 1):
        ret = '_' + ret
    return ret


def IsFlagSubSystem(flag):
    return flag >= const.flagSubSystemSlot0 and flag <= const.flagSubSystemSlot7


def GetShipFlagLocationName(flag):
    if flag >= const.flagHiSlot0 and flag <= const.flagHiSlot7:
        locationName = localization.GetByLabel('UI/Ship/HighSlot')
    elif flag >= const.flagMedSlot0 and flag <= const.flagMedSlot7:
        locationName = localization.GetByLabel('UI/Ship/MediumSlot')
    elif flag >= const.flagLoSlot0 and flag <= const.flagLoSlot7:
        locationName = localization.GetByLabel('UI/Ship/LowSlot')
    elif flag >= const.flagRigSlot0 and flag <= const.flagRigSlot7:
        locationName = localization.GetByLabel('UI/Ship/RigSlot')
    elif flag >= const.flagSubSystemSlot0 and flag <= const.flagSubSystemSlot7:
        locationName = localization.GetByLabel('UI/Ship/Subsystem')
    elif flag == const.flagCargo:
        locationName = localization.GetByLabel('UI/Ship/CargoHold')
    elif flag == const.flagDroneBay:
        locationName = localization.GetByLabel('UI/Ship/DroneBay')
    elif flag == const.flagShipHangar:
        locationName = localization.GetByLabel('UI/Ship/ShipMaintenanceBay')
    elif flag == const.flagHangar or flag >= const.flagCorpSAG2 and flag <= const.flagCorpSAG7:
        locationName = localization.GetByLabel('UI/Corporations/Common/CorporateHangar')
    elif flag == const.flagSpecializedFuelBay:
        locationName = localization.GetByLabel('UI/Ship/FuelBay')
    elif flag == const.flagSpecializedOreHold:
        locationName = localization.GetByLabel('UI/Ship/OreHold')
    elif flag == const.flagSpecializedGasHold:
        locationName = localization.GetByLabel('UI/Ship/GasHold')
    elif flag == const.flagSpecializedMineralHold:
        locationName = localization.GetByLabel('UI/Ship/MineralHold')
    elif flag == const.flagSpecializedSalvageHold:
        locationName = localization.GetByLabel('UI/Ship/SalvageHold')
    elif flag == const.flagSpecializedShipHold:
        locationName = localization.GetByLabel('UI/Ship/ShipHold')
    elif flag == const.flagSpecializedSmallShipHold:
        locationName = localization.GetByLabel('UI/Ship/SmallShipHold')
    elif flag == const.flagSpecializedMediumShipHold:
        locationName = localization.GetByLabel('UI/Ship/MediumShipHold')
    elif flag == const.flagSpecializedLargeShipHold:
        locationName = localization.GetByLabel('UI/Ship/LargeShipHold')
    elif flag == const.flagSpecializedIndustrialShipHold:
        locationName = localization.GetByLabel('UI/Ship/IndustrialShipHold')
    elif flag == const.flagSpecializedAmmoHold:
        locationName = localization.GetByLabel('UI/Ship/AmmoHold')
    elif flag == const.flagSpecializedCommandCenterHold:
        locationName = localization.GetByLabel('UI/Ship/CommandCenterHold')
    elif flag == const.flagSpecializedPlanetaryCommoditiesHold:
        locationName = localization.GetByLabel('UI/Ship/PlanetaryCommoditiesHold')
    elif flag == const.flagSpecializedMaterialBay:
        locationName = localization.GetByLabel('UI/Ship/MaterialBay')
    else:
        locationName = ''
    return locationName


def GetPlanetWarpInPoint(planetID, locVec, r):
    dx = float(locVec[0])
    dz = float(locVec[2])
    f = float(dz) / float(math.sqrt(dx ** 2 + dz ** 2))
    if dz > 0 and dx > 0 or dz < 0 and dx > 0:
        f *= -1.0
    theta = math.asin(f)
    myRandom = random.Random(planetID)
    rr = (myRandom.random() - 1.0) / 3.0
    theta += rr
    offset = 1000000
    FACTOR = 20.0
    dd = math.pow((FACTOR - 5.0 * math.log10(r / 1000000) - 0.5) / FACTOR, FACTOR) * FACTOR
    dd = min(10.0, max(0.0, dd))
    dd += 0.5
    offset += r * dd
    d = r + offset
    x = 1000000
    z = 0
    x = math.sin(theta) * d
    z = math.cos(theta) * d
    y = r * math.sin(rr) * 0.5
    return utillib.KeyVal(x=x, y=y, z=z)


def GraphicFile(graphicID):
    try:
        return cfg.graphics.Get(graphicID).graphicFile
    except Exception:
        return ''


def IconFile(iconID):
    try:
        return cfg.icons.Get(iconID).iconFile
    except Exception:
        return ''


def GetActiveShip():
    """
        This is a client only function but we lack a proper place to put there.
    """
    if session.stationid2:
        shipID = sm.GetService('clientDogmaIM').GetDogmaLocation().shipID
    else:
        shipID = session.shipid
    return shipID


def IsBookmarkModerator(corpRole):
    return corpRole & const.corpRoleChatManager == const.corpRoleChatManager


BULKVERSION = 3
BULKDEFINITIONS = {'typeSkillReqs': {'source': 'inventory.typesBySkillLevelVx',
                   'keys': [('skillTypeID', 'integer'),
                            ('skillLevel', 'integer'),
                            ('typeID', 'integer'),
                            ('marketGroupID', 'integer'),
                            ('marketGroupNameID', 'integer'),
                            ('metaLevel', 'integer')],
                   'indexes': [['skillTypeID']]},
 'marketGroups': {'source': 'inventory.marketGroups',
                  'keys': [('marketGroupID', 'integer PRIMARY KEY'),
                           ('parentGroupID', 'integer'),
                           ('marketGroupNameID', 'integer'),
                           ('descriptionID', 'integer'),
                           ('iconID', 'integer')],
                  'indexes': [['parentGroupID']]}}
bulkDataTableDefinitions = BULKDEFINITIONS
bulkDataVersion = BULKVERSION
