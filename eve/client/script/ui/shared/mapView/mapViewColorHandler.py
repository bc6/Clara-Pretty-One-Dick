#Embedded file name: eve/client/script/ui/shared/mapView\mapViewColorHandler.py
"""
Color handlers for starmap star coloring.

def ColorStarsByStuff(colorInfo, starColorMode [, arg1, arg1, ...]):
    # colorInfo = util.KeyVal(
        solarSystemDict={},     => systemID : (size, ratio (age), commentCallback, color), if color is non ratio will pick an intrpolated color provided by colorList
                                       commentCallback is: (callable, argsList).  It is executed when user mouseovers a solarsystem
        colorList=None,         => list of tuple colors used to when no unique color is used for entry
        legend=set())           => set of (sortKey, text, tuple-color) for use in the star color legend tab
"""
from eve.client.script.ui.util.uix import EditStationName
from eve.common.script.sys.eveCfg import IsFaction, GetActiveShip, CanUseAgent
import math
import geo2
import mapcommon
from mapcommon import LegendItem
from collections import defaultdict
import talecommon.const as taleConst
import localization
import logging
log = logging.getLogger(__name__)
import eveLocalization
import localization.const as locconst
from localization.parser import _Tokenize
TEMPSTRINGS = {'UI/Map/ColorModeHandler/stationsCount': u'{[numeric]count, decimalPlaces=0} {[numeric]count -> "station", "stations"} in system',
 'UI/Map/ColorModeHandler/stationsMany': u'{[numeric]maxCount, decimalPlaces=0} stations',
 'UI/Map/ColorModeHandler/dungeonDedLegendHint': u'{dungeonName}{dedName}',
 'UI/Map/ColorModeHandler/dungeonDedDifficulty': u' (DED: {[numeric]count, decimalPlaces=0})',
 'UI/Map/ColorModeHandler/visitedLastVisit': u'{[numeric]count, decimalPlaces=0} visits. Last Visited {[datetime]lastVisit, date=short, time=none}',
 'UI/Map/ColorModeHandler/pilotsInSpace': u'{[numeric]count, decimalPlaces=0} {[numeric]count -> "pilot", "pilots"} in system',
 'UI/Map/ColorModeHandler/pilotsInStation': u'{[numeric]count, decimalPlaces=0} {[numeric]count -> "pilot", "pilots"} docked in station',
 'UI/Map/ColorModeHandler/jumpsLastHour': u'{[numeric]count, decimalPlaces=0} {[numeric]count -> "jump", "jumps"} in the last hour',
 'UI/Map/ColorModeHandler/killsShipsInLast': u'{[numeric]count, decimalPlaces=0} ships destroyed in the last {[numeric]hours, decimalPlaces=0} {[numeric]hours -> "Hour", "Hours"}',
 'UI/Map/ColorModeHandler/killsPodInLast': u'{[numeric]count, decimalPlaces=0} {[numeric]count -> "pod", "pods"} killed in the last {[numeric]hours, decimalPlaces=0} {[numeric]hours -> "Hour", "Hours"}',
 'UI/Map/ColorModeHandler/killsFactionInLast': u'{{[numeric]count, decimalPlaces=0} {[numeric]count -> "faction ship", "faction ships"} destroyed in the last {[numeric]hours, decimalPlaces=0} {[numeric]hours -> "Hour", "Hours"}',
 'UI/Map/StarModeHandler/industryCostModifier': u'System Cost Index: {[numeric]index, decimalPlaces=2}'}

def GetByLabelTemp(label, **kwargs):
    englishText = TEMPSTRINGS.get(label, None)
    if not englishText:
        return ''
    tags = _Tokenize(englishText)
    parsedText = eveLocalization.Parse(englishText, locconst.LOCALE_SHORT_ENGLISH, tags, **kwargs)
    return parsedText


BASE5_COLORRANGE = [(1.0, 1.0, 0.8313725490196079, 1.0),
 (0.996078431372549, 0.8509803921568627, 0.5568627450980392, 1.0),
 (0.996078431372549, 0.6, 0.1607843137254902, 1.0),
 (0.8509803921568627, 0.37254901960784315, 0.054901960784313725, 1.0),
 (0.6, 0.20392156862745098, 0.01568627450980392, 1.0)]
BASE3_COLORRANGE = [(1.0, 0.9686274509803922, 0.7372549019607844, 1.0), (0.996078431372549, 0.7686274509803922, 0.30980392156862746, 1.0), (0.8509803921568627, 0.37254901960784315, 0.054901960784313725, 1.0)]
BASE11_COLORRANGE = [(165, 0, 38),
 (215, 48, 39),
 (244, 109, 67),
 (253, 174, 97),
 (254, 224, 139),
 (255, 255, 191),
 (217, 239, 139),
 (166, 217, 106),
 (102, 189, 99),
 (26, 152, 80),
 (0, 104, 55)]
BASE4_ORANGES_COLORRANGE = [(0.996078431372549, 0.9294117647058824, 0.8705882352941177, 1.0),
 (0.9921568627450981, 0.7450980392156863, 0.5215686274509804, 1.0),
 (0.9921568627450981, 0.5529411764705883, 0.23529411764705882, 1.0),
 (0.8509803921568627, 0.2784313725490196, 0.00392156862745098, 1.0)]
NEG_NEU_POS_3RANGE = [(0.9882352941176471, 0.5529411764705883, 0.34901960784313724, 1.0), (1.0, 1.0, 0.7490196078431373, 1.0), (0.5686274509803921, 0.8117647058823529, 0.3764705882352941, 1.0)]
HOT_COLD_2RANGE = [(0.9882352941176471, 0.5529411764705883, 0.34901960784313724, 1.0), (0.0, 1.0, 0.0, 1.0)]
COLORCURVE_SECURITY = [(1.0, 0.0, 0.0, 1.0),
 (0.9, 0.2, 0.0, 1.0),
 (1.0, 0.3, 0.0, 1.0),
 (1.0, 0.4, 0.0, 1.0),
 (0.9, 0.5, 0.0, 1.0),
 (1.0, 1.0, 0.0, 1.0),
 (0.6, 1.0, 0.2, 1.0),
 (0.0, 1.0, 0.0, 1.0),
 (0.0, 1.0, 0.3, 1.0),
 (0.3, 1.0, 0.8, 1.0),
 (0.2, 1.0, 1.0, 1.0)]
COLOR_STANDINGS_NEUTRAL = (0.25, 0.25, 0.25, 1.0)
COLOR_STANDINGS_GOOD = (0.0, 1.0, 0.0, 1.0)
COLOR_STANDINGS_BAD = (1.0, 0.0, 0.0, 1.0)
NEUTRAL_COLOR = (0.25, 0.25, 0.25, 1.0)
DEFAULT_MAX_COLOR = BASE5_COLORRANGE[-1]
COLOR_ASSETS = BASE5_COLORRANGE[-1]
COLOR_DEVINDEX = BASE5_COLORRANGE[-1]
CONFISCATED_COLOR = (0.8, 0.4, 0.0, 1.0)
ATTACKED_COLOR = (1.0, 0.0, 0.0, 1.0)
COLOR_ORANGE = (1.0, 0.4, 0.0, 1.0)
COLOR_GREEN = (0.2, 1.0, 1.0, 1.0)
COLOR_RED = (1.0, 0.0, 0.0, 1.0)
COLOR_YELLOW = (1.0, 1.0, 0.0, 1.0)
STAR_SIZE_UNIFORM = 0.5
STAR_COLORTYPE_PASSIVE = 0
STAR_COLORTYPE_DATA = 1

def GetBase11ColorByID(objectID):
    return BASE11_COLORRANGE[objectID % 11]


def ColorStarsByDevIndex(colorInfo, starColorMode, indexID, indexName):
    sovSvc = sm.GetService('sov')
    indexData = sovSvc.GetAllDevelopmentIndicesMapped()
    color = COLOR_DEVINDEX
    hintFunc = lambda indexName, level: localization.GetByLabel('UI/Map/StarModeHandler/devIndxLevel', indexName=indexName, level=level)
    maxLevel = 0
    for solarSystemID, info in indexData.iteritems():
        levelInfo = sovSvc.GetIndexLevel(info[indexID], indexID)
        maxLevel = max(maxLevel, levelInfo.level)

    for solarSystemID, info in indexData.iteritems():
        levelInfo = sovSvc.GetIndexLevel(info[indexID], indexID)
        if levelInfo.level == 0:
            continue
        colorInfo.solarSystemDict[solarSystemID] = (levelInfo.level / float(maxLevel),
         None,
         (hintFunc, (indexName, levelInfo.level)),
         color)

    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/devIndxDevloped'), color, data=None))
    colorInfo.colorType = STAR_COLORTYPE_DATA


def ColorStarsByAssets(colorInfo, starColorMode):
    myassets = sm.GetService('assets').GetAll('allitems', blueprintOnly=0, isCorp=0)
    assetColor = COLOR_ASSETS
    bySystemID = {}
    stuffToPrime = []
    for solarsystemID, station in myassets:
        stuffToPrime.append(station.stationID)
        stuffToPrime.append(solarsystemID)
        if solarsystemID not in bySystemID:
            bySystemID[solarsystemID] = []
        bySystemID[solarsystemID].append(station)

    if stuffToPrime:
        cfg.evelocations.Prime(stuffToPrime)

    def hintFunc(stationData):
        hint = ''
        for stationID, itemCount in stationData:
            shortStationName = EditStationName(cfg.evelocations.Get(stationID).name, usename=1)
            subc = localization.GetByLabel('UI/Map/StarModeHandler/StationNameWithItemCount', shortStationName=shortStationName, numItems=itemCount)
            if hint:
                hint += '<br>'
            hint += '<url=localsvc:service=assets&method=Show&stationID=%d>%s</url>' % (stationID, subc)

        return hint

    maxValue = 0
    for solarsystemID, stations in bySystemID.iteritems():
        itemCount = sum((station.itemCount for station in stations))
        maxValue = max(maxValue, itemCount)

    for solarsystemID, stations in bySystemID.iteritems():
        itemCount = sum((station.itemCount for station in stations))
        stationData = [ (station.stationID, station.itemCount) for station in stations ]
        colorInfo.solarSystemDict[solarsystemID] = (itemCount / float(maxValue),
         None,
         (hintFunc, (stationData,)),
         assetColor)

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/assetsNoAssets'), NEUTRAL_COLOR, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/assetsHasAssets'), assetColor, data=None))


def ColorStarsByVisited(colorInfo, starColorMode):
    history = sm.RemoteSvc('map').GetSolarSystemVisits()
    visited = []
    maxValue = 0
    for entry in history:
        visited.append((entry.lastDateTime, entry.solarSystemID, entry.visits))
        maxValue = max(maxValue, entry.visits)

    visited.sort()
    if len(visited):
        divisor = 1.0 / float(len(visited))
    hintFunc = lambda solarSystemID, visits, lastDateTime: GetByLabelTemp('UI/Map/ColorModeHandler/visitedLastVisit', count=visits, lastVisit=lastDateTime)
    for i, (lastDateTime, solarSystemID, visits) in enumerate(visited):
        colorInfo.solarSystemDict[solarSystemID] = (visits / float(maxValue),
         float(i) * divisor,
         (hintFunc, (solarSystemID, visits, lastDateTime)),
         None)

    colorInfo.colorList = BASE3_COLORRANGE
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/visitedShortest'), colorInfo.colorList[0], data=None))
    colorInfo.legend.add(LegendItem(2, localization.GetByLabel('UI/Map/StarModeHandler/visitedLongest'), colorInfo.colorList[2], data=None))
    colorInfo.colorType = STAR_COLORTYPE_DATA


def ColorStarsBySecurity(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        secStatus = starmap.map.GetSecurityStatus(solarSystemID)
        colorInfo.solarSystemDict[solarSystemID] = (STAR_SIZE_UNIFORM,
         secStatus,
         None,
         None)

    colorInfo.colorList = COLORCURVE_SECURITY
    for i in xrange(0, 11):
        lbl = localization.GetByLabel('UI/Map/StarModeHandler/securityLegendItem', level=1.0 - i * 0.1)
        colorInfo.legend.add(LegendItem(i, lbl, COLORCURVE_SECURITY[10 - i], data=None))


def ColorStarsBySovChanges(colorInfo, starColorMode, changeMode):
    if changeMode in (mapcommon.SOV_CHANGES_OUTPOST_GAIN, mapcommon.SOV_CHANGES_SOV_GAIN):
        color = NEG_NEU_POS_3RANGE[2]
    elif changeMode in (mapcommon.SOV_CHANGES_OUTPOST_LOST, mapcommon.SOV_CHANGES_SOV_LOST):
        color = NEG_NEU_POS_3RANGE[0]
    else:
        color = NEG_NEU_POS_3RANGE[1]
    changes = GetSovChangeList(changeMode)
    hintFunc = lambda comments: '<br><br>'.join(comments)
    maxValue = max([ len(comments) for solarSystemID, comments in changes.iteritems() ])
    for solarSystemID, comments in changes.iteritems():
        colorInfo.solarSystemDict[solarSystemID] = (len(comments) / float(maxValue), None(hintFunc, (comments,)), color)

    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/sovereigntyNoSovChanges'), NEUTRAL_COLOR, None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/sovereigntySovChanges'), color, None))
    colorInfo.colorType = STAR_COLORTYPE_DATA


def GetSovChangeList(changeMode):
    """
    get all changes and prepare for star coloring, mostly by generating the mouse over hint list
    """
    data = sm.GetService('sov').GetRecentActivity()
    changes = []
    resultMap = {}
    toPrime = set()
    for item in data:
        if item.stationID is None:
            if bool(changeMode & mapcommon.SOV_CHANGES_SOV_GAIN) and item.ownerID is not None:
                changes.append((item.solarSystemID, 'UI/Map/StarModeHandler/sovereigntySovGained', (None, item.ownerID)))
                toPrime.add(item.ownerID)
            elif bool(changeMode & mapcommon.SOV_CHANGES_SOV_LOST) and item.oldOwnerID is not None:
                changes.append((item.solarSystemID, 'UI/Map/StarModeHandler/sovereigntySovLost', (item.oldOwnerID, None)))
                toPrime.add(item.oldOwnerID)
        elif bool(changeMode & mapcommon.SOV_CHANGES_SOV_GAIN) and item.oldOwnerID is None:
            changes.append((item.solarSystemID, 'UI/Map/StarModeHandler/sovereigntyNewOutpost', (None, item.ownerID)))
            toPrime.add(item.ownerID)
        elif bool(changeMode & mapcommon.SOV_CHANGES_SOV_GAIN) and item.ownerID is not None:
            changes.append((item.solarSystemID, 'UI/Map/StarModeHandler/sovereigntyConqueredOutpost', (item.ownerID, item.oldOwnerID)))
            toPrime.add(item.ownerID)
            toPrime.add(item.oldOwnerID)

    cfg.eveowners.Prime(list(toPrime))
    for solarSystemID, text, owners in changes:
        oldOwner = '' if owners[0] is None else cfg.eveowners.Get(owners[0]).ownerName
        owner = '' if owners[1] is None else cfg.eveowners.Get(owners[1]).ownerName
        if solarSystemID not in resultMap:
            resultMap[solarSystemID] = []
        resultMap[solarSystemID].append(localization.GetByLabel(text, owner=owner, oldOwner=oldOwner))

    return resultMap


def ColorStarsByFactionStandings(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    colorByFaction = {}
    neutral = COLOR_STANDINGS_NEUTRAL
    for factionID in starmap.GetAllFactionsAndAlliances():
        colorByFaction[factionID] = starmap.GetColorByStandings(factionID)

    lbl = localization.GetByLabel('UI/Map/StarModeHandler/factionStandings')
    hintFunc = lambda : lbl
    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        color = colorByFaction.get(solarSystem.factionID, neutral)
        colorInfo.solarSystemDict[solarSystemID] = (STAR_SIZE_UNIFORM,
         None,
         (hintFunc, ()),
         color)

    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/factionGoodStandings'), COLOR_STANDINGS_GOOD, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/factionNeutralStandings'), COLOR_STANDINGS_NEUTRAL, data=None))
    colorInfo.legend.add(LegendItem(2, localization.GetByLabel('UI/Map/StarModeHandler/factionBadStandings'), COLOR_STANDINGS_BAD, data=None))


def ColorStarsByFaction(colorInfo, starColorMode):
    factionID = starColorMode[1]
    starmap = sm.GetService('starmap')
    allianceSolarSystems = starmap.GetAllianceSolarSystems()
    sovBySolarSystemID = {}
    toPrime = set()
    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        if factionID == mapcommon.STARMODE_FILTER_EMPIRE:
            secClass = starmap.map.GetSecurityStatus(solarSystemID)
            if not IsFaction(solarSystem.factionID) or secClass == const.securityClassZeroSec:
                continue
        sovHolderID = starmap._GetFactionIDFromSolarSystem(allianceSolarSystems, solarSystemID)
        if sovHolderID is None:
            continue
        if factionID >= 0 and sovHolderID != factionID:
            continue
        sovBySolarSystemID[solarSystemID] = sovHolderID
        toPrime.add(sovHolderID)

    cfg.eveowners.Prime(list(toPrime))
    hintFunc = lambda name: localization.GetByLabel('UI/Map/StarModeHandler/factionSovereignty', name=name)
    for solarSystemID, sovHolderID in sovBySolarSystemID.iteritems():
        name = cfg.eveowners.Get(sovHolderID).name
        col = GetBase11ColorByID(sovHolderID)
        colorInfo.solarSystemDict[solarSystemID] = (STAR_SIZE_UNIFORM,
         None,
         (hintFunc, (name,)),
         col)
        colorInfo.legend.add(LegendItem(None, name, col, data=sovHolderID))


def ColorStarsByMilitia(colorInfo, starColorMode):
    factionID = starColorMode[1]
    if factionID < -1:
        log.error('Invalid factionID %s' % factionID)
        return
    facWar = sm.GetService('facwar')
    starmap = sm.GetService('starmap')
    facWarSolarSystemsOccupiers = facWar.GetFacWarSystemsOccupiers()
    warFactions = facWar.GetWarFactions()
    colByFaction = {fID:GetBase11ColorByID(fID) for fID in warFactions}
    nameByFaction = {fID:cfg.eveowners.Get(fID).name for fID in warFactions}
    maxPointsByFaction = {fID:1 for fID in warFactions}
    maxThresholdByFaction = {fID:1 for fID in warFactions}
    facWarData = starmap.GetFacWarData()
    occupiedSystems = {}
    for systemID, currentOccupierID in facWarSolarSystemsOccupiers.iteritems():
        if currentOccupierID == factionID or factionID == -1:
            if systemID in facWarData:
                threshold, points, occupierID = facWarData[systemID]
                if occupierID is not None and occupierID != currentOccupierID:
                    state = const.contestionStateCaptured
                elif threshold > points:
                    if points == 0:
                        state = const.contestionStateNone
                    else:
                        state = const.contestionStateContested
                else:
                    state = const.contestionStateVulnerable
                maxThresholdByFaction[currentOccupierID] = max(threshold, maxThresholdByFaction[currentOccupierID])
                maxPointsByFaction[currentOccupierID] = max(points, maxPointsByFaction[currentOccupierID])
            else:
                points, state = 0, const.contestionStateNone
            occupiedSystems[systemID] = (currentOccupierID, points, state)

    hintFunc = lambda name, status: localization.GetByLabel('UI/Map/StarModeHandler/militiaSystemStatus', name=name, status=status)
    multiplierByFaction = {fID:max(1.0, maxThresholdByFaction[fID] / maxPointsByFaction[fID]) for fID in maxThresholdByFaction.keys()}
    starmap = sm.GetService('starmap')
    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        if solarSystemID in occupiedSystems:
            solarsystem = starmap.map.GetItem(solarSystemID)
            if solarsystem is None:
                continue
            occupierID, points, state = occupiedSystems[solarSystemID]
            size = multiplierByFaction[occupierID] * float(points)
            statusText = sm.GetService('infoPanel').GetSolarSystemStatusText(state, True)
            colorInfo.solarSystemDict[solarSystemID] = (size,
             size,
             (hintFunc, (nameByFaction[occupierID], statusText)),
             colByFaction[occupierID])
            colorInfo.legend.add(LegendItem(None, nameByFaction[occupierID], colByFaction[occupierID], data=occupierID))

    colorInfo.colorList = BASE3_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA


def ColorStarsByRegion(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    hintFunc = lambda name: localization.GetByLabel('UI/Map/StarModeHandler/regionNameEntry', name=name)
    for regionID, region in starmap.GetKnownUniverseRegions().iteritems():
        regionName = cfg.evelocations.Get(regionID).name
        col = BASE5_COLORRANGE[regionID % len(BASE5_COLORRANGE)]
        for solarSystemID in region.solarSystemIDs:
            colorInfo.solarSystemDict[solarSystemID] = (STAR_SIZE_UNIFORM,
             None,
             (hintFunc, (regionName,)),
             col)

        colorInfo.legend.add(LegendItem(None, regionName, col, data=regionID))


def HintCargoIllegality(attackTypeIDs, confiscateTypeIDs):
    systemDescription = ''
    for typeID in attackTypeIDs:
        if systemDescription != '':
            systemDescription += '<br>'
        systemDescription += localization.GetByLabel('UI/Map/StarModeHandler/legalityAttackHint', stuff=cfg.invtypes.Get(typeID).name)

    for typeID in confiscateTypeIDs:
        if systemDescription != '':
            systemDescription += '<br>'
        systemDescription += localization.GetByLabel('UI/Map/StarModeHandler/legalityConfiscateHint', item=cfg.invtypes.Get(typeID).name)

    return systemDescription


def ColorStarsByCargoIllegality(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    invCache = sm.GetService('invCache')
    activeShipID = GetActiveShip()
    if activeShipID is None:
        shipCargo = []
    else:
        inv = invCache.GetInventoryFromId(activeShipID, locationID=session.stationid2)
        shipCargo = inv.List()
    factionIllegality = {}
    while len(shipCargo) > 0:
        item = shipCargo.pop(0)
        if item.groupID in [const.groupCargoContainer,
         const.groupSecureCargoContainer,
         const.groupAuditLogSecureContainer,
         const.groupFreightContainer]:
            shipCargo.extend(invCache.GetInventoryFromId(item.itemID).List())
        itemIllegalities = cfg.invtypes.Get(item.typeID).Illegality()
        if itemIllegalities:
            for factionID, illegality in itemIllegalities.iteritems():
                if factionID not in factionIllegality:
                    factionIllegality[factionID] = {}
                if item.typeID not in factionIllegality[factionID]:
                    factionIllegality[factionID][item.typeID] = [max(0.0, illegality.confiscateMinSec), max(0.0, illegality.attackMinSec)]

    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        colour = None
        factionID = solarSystem.factionID
        if factionID is None or factionID not in factionIllegality:
            continue
        systemIllegality = False
        attackTypeIDs = []
        confiscateTypeIDs = []
        securityStatus = starmap.map.GetSecurityStatus(solarSystemID)
        for typeID in factionIllegality[factionID]:
            if securityStatus >= factionIllegality[factionID][typeID][1]:
                systemIllegality = True
                if not colour or colour[0] < 2:
                    colour = (2, ATTACKED_COLOR)
                attackTypeIDs.append(typeID)
            elif securityStatus >= factionIllegality[factionID][typeID][0]:
                systemIllegality = True
                if not colour:
                    colour = (1, CONFISCATED_COLOR)
                confiscateTypeIDs.append(typeID)

        if systemIllegality:
            colorInfo.solarSystemDict[solarSystemID] = (STAR_SIZE_UNIFORM,
             0.0,
             (HintCargoIllegality, (attackTypeIDs, confiscateTypeIDs)),
             colour[1])

    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/legalityNoConsequences'), NEUTRAL_COLOR, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/legalityConfiscate'), CONFISCATED_COLOR, data=None))
    colorInfo.legend.add(LegendItem(2, localization.GetByLabel('UI/Map/StarModeHandler/legalityWillAttack'), ATTACKED_COLOR, data=None))


def ColorStarsByNumPilots(colorInfo, starColorMode):
    sol, sta, statDivisor = sm.ProxySvc('machoNet').GetClusterGameStatistics('EVE', ({}, {}, 0))
    pilotcountDict = {}
    maxCount = 0
    for sfoo in sol.iterkeys():
        solarSystemID = sfoo + 30000000
        amount_docked = sta.get(sfoo, 0) / statDivisor
        amount_inspace = (sol.get(sfoo, 0) - sta.get(sfoo, 0)) / statDivisor
        if starColorMode == mapcommon.STARMODE_PLAYERCOUNT:
            amount = amount_inspace
        else:
            amount = amount_docked
        pilotcountDict[solarSystemID] = amount
        if amount > maxCount:
            maxCount = amount

    if starColorMode == mapcommon.STARMODE_PLAYERCOUNT:
        hintFunc = lambda count, solarSystemID: GetByLabelTemp('UI/Map/ColorModeHandler/pilotsInSpace', count=count)
    else:
        hintFunc = lambda count, solarSystemID: GetByLabelTemp('UI/Map/ColorModeHandler/pilotsInStation', count=count)
    if maxCount:
        for solarSystemID, pilotCount in pilotcountDict.iteritems():
            if pilotCount == 0:
                continue
            sizeFactor = colorCurveValue = pilotCount / float(maxCount)
            colorInfo.solarSystemDict[solarSystemID] = (sizeFactor,
             colorCurveValue,
             (hintFunc, (pilotCount, solarSystemID)),
             None)

    colorInfo.colorList = BASE3_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/pilotsMany', maxCount=maxCount), colorInfo.colorList[-1], data=None))


def ColorStarsByStationCount(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    if starmap.stationCountCache is None:
        starmap.stationCountCache = sm.RemoteSvc('map').GetStationCount()
    history = starmap.stationCountCache
    maxCount = max([ amount for solarSystemID, amount in history ])
    hintFunc = lambda count, solarSystemID: GetByLabelTemp('UI/Map/ColorModeHandler/stationsCount', count=count)
    for solarSystemID, amount in history:
        sizeFactor = colorFactor = float(amount) / maxCount
        colorInfo.solarSystemDict[solarSystemID] = (sizeFactor,
         colorFactor,
         (hintFunc, (amount, solarSystemID)),
         None)

    colorInfo.colorList = BASE3_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(2, GetByLabelTemp('UI/Map/ColorModeHandler/stationsMany', maxCount=maxCount), colorInfo.colorList[-1], data=None))


def HintDungeons(dungeons):
    comments = []
    for dungeonID, difficulty, dungeonName in dungeons:
        ded = ''
        if difficulty:
            ded = GetByLabelTemp('UI/Map/ColorModeHandler/dungeonDedDifficulty', count=difficulty)
        comments.append(GetByLabelTemp('UI/Map/ColorModeHandler/dungeonDedLegendHint', dungeonName=dungeonName, dedName=ded))

    return '<br>'.join(comments)


def ColorStarsByDungeons(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    if starColorMode == mapcommon.STARMODE_DUNGEONS:
        dungeons = sm.RemoteSvc('map').GetDeadspaceComplexMap(eve.session.languageID)
    elif starColorMode == mapcommon.STARMODE_DUNGEONSAGENTS:
        dungeons = sm.RemoteSvc('map').GetDeadspaceAgentsMap(eve.session.languageID)
    if dungeons is None:
        return
    solmap = {}
    for solarSystemID, dungeonID, difficulty, dungeonName in dungeons:
        solmap.setdefault(solarSystemID, []).append((dungeonID, difficulty, dungeonName))

    maxDungeons = max([ len(solarSystemDungeons) for solarSystemID, solarSystemDungeons in solmap.iteritems() ])
    for solarSystemID, solarSystemDungeons in solmap.iteritems():
        maxDifficulty = 1
        for dungeonID, difficulty, dungeonName in solarSystemDungeons:
            if difficulty:
                maxDifficulty = max(maxDifficulty, difficulty)

        maxDifficulty = (10 - maxDifficulty) / 9.0
        colorInfo.solarSystemDict[solarSystemID] = (len(solarSystemDungeons) / float(maxDungeons),
         maxDifficulty,
         (HintDungeons, (solarSystemDungeons,)),
         None)

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.colorList = COLORCURVE_SECURITY
    colorCurve = starmap.GetColorCurve(COLORCURVE_SECURITY)
    for i in xrange(0, 10):
        lbl = localization.GetByLabel('UI/Map/StarModeHandler/dungeonDedLegendDiffaculty', difficulty=i + 1)
        colorInfo.legend.add(LegendItem(i, lbl, starmap.GetColorCurveValue(colorCurve, (9 - i) / 9.0), data=None))


def ColorStarsByJumps1Hour(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatJumps, 1)
    history = []
    for entry in historyDB:
        if entry.value1 > 0:
            history.append((entry.solarSystemID, entry.value1))

    maxCount = 0
    for solarSystemID, amount in history:
        if amount > maxCount:
            maxCount = amount

    if maxCount > 1:
        divisor = 1.0 / math.log(pow(float(maxCount), 4.0))
        hintFunc = lambda count, solarSystemID: GetByLabelTemp('UI/Map/ColorModeHandler/jumpsLastHour', count=count)
        for solarSystemID, amount in history:
            colorInfo.solarSystemDict[solarSystemID] = (amount / float(maxCount),
             amount / float(maxCount),
             (hintFunc, (amount, solarSystemID)),
             None)

    colorInfo.colorList = BASE4_ORANGES_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/jumpsNumber', count=0), colorInfo.colorList[0], data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/jumpsNumber', count=maxCount), colorInfo.colorList[-1], data=None))


def ColorStarsByKills(colorInfo, starColorMode, statID, hours):
    historyDB = sm.RemoteSvc('map').GetHistory(statID, hours)
    history = []
    for entry in historyDB:
        if entry.value1 - entry.value2 > 0:
            history.append((entry.solarSystemID, entry.value1 - entry.value2))

    maxCount = 0
    for solarSystemID, amount in history:
        if amount > maxCount:
            maxCount = amount

    if maxCount > 0:
        divisor = 1.0 / float(maxCount)
    hintFunc = lambda count, solarSystemID, hours: GetByLabelTemp('UI/Map/ColorModeHandler/killsShipsInLast', count=count, hours=hours)
    for solarSystemID, amount in history:
        age = divisor * float(amount)
        colorInfo.solarSystemDict[solarSystemID] = (amount / float(maxCount),
         age,
         (hintFunc, (amount, solarSystemID, hours)),
         None)

    colorInfo.colorList = BASE4_ORANGES_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/killsNumber', count=0), colorInfo.colorList[0], data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/killsNumber', count=maxCount), colorInfo.colorList[-1], data=None))


def ColorStarsByPodKills(colorInfo, starColorMode):
    if starColorMode == mapcommon.STARMODE_PODKILLS24HR:
        hours = 24
        historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatKills, 24)
    else:
        hours = 1
        historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatKills, 1)
    history = []
    for entry in historyDB:
        if entry.value3 > 0:
            history.append((entry.solarSystemID, entry.value3))

    maxCount = 0
    for solarSystemID, amount in history:
        if amount > maxCount:
            maxCount = amount

    divisor = 0.0
    if maxCount > 0:
        divisor = 1.0 / float(maxCount)
    hintFunc = lambda solarSystemID, hours, count: GetByLabelTemp('UI/Map/ColorModeHandler/killsPodInLast', hours=hours, count=count)
    for solarSystemID, amount in history:
        age = divisor * float(amount)
        colorInfo.solarSystemDict[solarSystemID] = (amount / float(maxCount),
         age,
         (hintFunc, (solarSystemID, hours, amount)),
         None)

    colorInfo.colorList = BASE4_ORANGES_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/killsPodNumber', count=0), colorInfo.colorList[0], data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/killsPodNumber', count=maxCount), colorInfo.colorList[-1], data=None))


def ColorStarsByFactionKills(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    hours = 24
    historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatKills, hours)
    history = []
    for entry in historyDB:
        if entry.value2 > 0:
            history.append((entry.solarSystemID, entry.value2))

    maxCount = 0
    for solarSystemID, amount in history:
        if amount > maxCount:
            maxCount = amount

    divisor = 0.0
    if maxCount > 0:
        divisor = 1.0 / float(maxCount)
    hintFunc = lambda solarSystemID, hours, count: GetByLabelTemp('UI/Map/ColorModeHandler/killsFactionInLast', hours=hours, count=count)
    for solarSystemID, amount in history:
        age = divisor * float(amount)
        colorInfo.solarSystemDict[solarSystemID] = (amount / float(maxCount),
         age,
         (hintFunc, (solarSystemID, hours, amount)),
         None)

    colorInfo.colorList = BASE4_ORANGES_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/killsNumber', count=0), colorInfo.colorList[0], data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/killsNumber', count=maxCount), colorInfo.colorList[-1], data=None))


def ColorStarsByCynosuralFields(colorInfo, starColorMode):
    fields = sm.RemoteSvc('map').GetBeaconCount()
    orange = COLOR_ORANGE
    green = COLOR_GREEN
    red = COLOR_RED
    hintFuncTotal = lambda count: localization.GetByLabel('UI/Map/StarModeHandler/cynoActiveFieldsGeneratorsNumber', count=count)
    hintFuncModule = lambda count: localization.GetByLabel('UI/Map/StarModeHandler/cynoActiveFieldsNumber', count=count)
    hintFuncStructure = lambda count: localization.GetByLabel('UI/Map/StarModeHandler/cynoActiveGeneratorNumber', count=count)
    maxModule = 0
    maxStructure = 0
    for solarSystemID, cnt in fields.iteritems():
        moduleCnt, structureCnt = cnt
        maxModule = max(maxModule, moduleCnt)
        maxStructure = max(maxStructure, structureCnt)

    for solarSystemID, cnt in fields.iteritems():
        moduleCnt, structureCnt = cnt
        if moduleCnt > 0 and structureCnt > 0:
            ttlcnt = moduleCnt + structureCnt
            colorInfo.solarSystemDict[solarSystemID] = (ttlcnt / float(maxModule + maxStructure),
             1.0,
             (hintFuncTotal, (ttlcnt,)),
             red)
        elif moduleCnt:
            colorInfo.solarSystemDict[solarSystemID] = (moduleCnt / float(maxModule),
             1.0,
             (hintFuncModule, (moduleCnt,)),
             green)
        elif structureCnt:
            colorInfo.solarSystemDict[solarSystemID] = (structureCnt / float(maxStructure),
             1.0,
             (hintFuncStructure, (structureCnt,)),
             orange)

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/cynoActiveFields'), green, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/cynoActiveGenerators'), orange, data=None))
    colorInfo.legend.add(LegendItem(2, localization.GetByLabel('UI/Map/StarModeHandler/cynoActiveFieldsGenerators'), red, data=None))


def ColorStarsByCorpAssets(colorInfo, starColorMode, assetKey, legendName):
    rows = sm.RemoteSvc('corpmgr').GetAssetInventory(eve.session.corpid, assetKey)
    solarsystems = {}
    stuffToPrime = []
    for row in rows:
        stationID = row.locationID
        try:
            solarsystemID = sm.GetService('ui').GetStation(row.locationID).solarSystemID
        except:
            solarsystemID = row.locationID

        if solarsystemID not in solarsystems:
            solarsystems[solarsystemID] = {}
            stuffToPrime.append(solarsystemID)
        if stationID not in solarsystems[solarsystemID]:
            solarsystems[solarsystemID][stationID] = []
            stuffToPrime.append(stationID)
        solarsystems[solarsystemID][stationID].append(row)

    cfg.evelocations.Prime(stuffToPrime)
    hintFunc = lambda stationIDs: '<br>'.join([ cfg.evelocations.Get(stationID).name for stationID in stationIDs ])
    for solarsystemID, stations in solarsystems.iteritems():
        colorInfo.solarSystemDict[solarsystemID] = (STAR_SIZE_UNIFORM,
         1.0,
         (hintFunc, (stations.keys(),)),
         DEFAULT_MAX_COLOR)

    colorInfo.legend.add(LegendItem(1, legendName, DEFAULT_MAX_COLOR, data=None))


def ColorStarsByServices(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    serviceTypeID = starColorMode[1]
    stations, opservices, services = sm.RemoteSvc('map').GetStationExtraInfo()
    opservDict = {}
    stationIDs = []
    solarsystems = {}
    for each in opservices:
        if each.operationID not in opservDict:
            opservDict[each.operationID] = []
        opservDict[each.operationID].append(each.serviceID)

    if starmap.warFactionByOwner is None and serviceTypeID == const.stationServiceNavyOffices:
        starmap.warFactionByOwner = {}
        factions = sm.GetService('facwar').GetWarFactions().keys()
        for stationRow in stations:
            ownerID = stationRow.ownerID
            if ownerID not in starmap.warFactionByOwner:
                faction = sm.GetService('faction').GetFaction(ownerID)
                if faction and faction in factions:
                    starmap.warFactionByOwner[ownerID] = faction

    if serviceTypeID == const.stationServiceSecurityOffice:
        secOfficeSvc = sm.GetService('securityOfficeSvc')
    for stationRow in stations:
        solarSystemID = stationRow.solarSystemID
        if stationRow.operationID == None:
            continue
        if serviceTypeID not in opservDict[stationRow.operationID]:
            continue
        if serviceTypeID == const.stationServiceNavyOffices and stationRow.ownerID not in starmap.warFactionByOwner:
            continue
        if serviceTypeID == const.stationServiceSecurityOffice and not secOfficeSvc.CanAccessServiceInStation(stationRow.stationID):
            continue
        if solarSystemID not in solarsystems:
            solarsystems[solarSystemID] = []
        solarsystems[solarSystemID].append(stationRow.stationID)
        stationIDs.append(stationRow.stationID)

    cfg.evelocations.Prime(stationIDs)

    def hintFunc2(stationIDs):
        hint = ''
        for stationID in stationIDs:
            station = sm.StartService('ui').GetStation(stationID)
            stationName = cfg.evelocations.Get(stationID).name
            stationTypeID = station.stationTypeID
            if hint:
                hint += '<br>'
            hint += '<url=showinfo:%d//%d>%s</url>' % (stationTypeID, stationID, stationName)

        return hint

    for solarsystemID, stationIDs in solarsystems.iteritems():
        colorInfo.solarSystemDict[solarsystemID] = (STAR_SIZE_UNIFORM,
         1.0,
         (hintFunc2, (stationIDs,)),
         DEFAULT_MAX_COLOR)

    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/serviceNoneHere'), NEUTRAL_COLOR, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/serviceHasServices'), DEFAULT_MAX_COLOR, data=None))


def ColorStarsByFleetMembers(colorInfo, starColorMode):
    fleetComposition = sm.GetService('fleet').GetFleetComposition()
    if fleetComposition is not None:
        solarsystems = {}
        for each in fleetComposition:
            if each.solarSystemID not in solarsystems:
                solarsystems[each.solarSystemID] = []
            solarsystems[each.solarSystemID].append(each.characterID)

        hintFunc = lambda characterIDs: '<br>'.join([ cfg.eveowners.Get(characterID).name for characterID in characterIDs ])
        for locationID, charIDs in solarsystems.iteritems():
            colorInfo.solarSystemDict[locationID] = (STAR_SIZE_UNIFORM,
             1.0,
             (hintFunc, (charIDs,)),
             DEFAULT_MAX_COLOR)

    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/fleetNoMembers'), NEUTRAL_COLOR, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/fleetHasMembers'), DEFAULT_MAX_COLOR, data=None))


def ColorStarsByCorpMembers(colorInfo, starColorMode):
    corp = sm.RemoteSvc('map').GetMyExtraMapInfo()
    if corp is not None:
        solarsystems = {}
        for each in corp:
            solarsystems.setdefault(each.locationID, []).append(each.characterID)

        hintFunc = lambda characterIDs: '<br>'.join([ cfg.eveowners.Get(characterID).name for characterID in characterIDs ])
        for locationID, charIDs in solarsystems.iteritems():
            colorInfo.solarSystemDict[locationID] = (STAR_SIZE_UNIFORM,
             1.0,
             (hintFunc, (charIDs,)),
             DEFAULT_MAX_COLOR)

    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/corpHasMembers'), DEFAULT_MAX_COLOR, data=None))


def HintMyAgents2(stations, npcDivisions):
    caption = ''
    for stationID, agents in stations.iteritems():
        for agent in agents:
            agentOwner = cfg.eveowners.Get(agent.agentID)
            agentString = localization.GetByLabel('UI/Map/StarModeHandler/agentCaptionDetails', divisionName=npcDivisions[agent.divisionID].divisionName, agentName=agentOwner.name, level=agent.level)
            if caption:
                caption += '<br>'
            caption += '<url=showinfo:%d//%d>%s</url>' % (agentOwner.typeID, agent.agentID, agentString)

    return caption


def ColorStarsByMyAgents(colorInfo, starColorMode):
    standingInfo = sm.RemoteSvc('map').GetMyExtraMapInfoAgents().Index('fromID')
    solarsystems = {}
    valid = (const.agentTypeBasicAgent, const.agentTypeResearchAgent, const.agentTypeFactionalWarfareAgent)
    agentsByID = sm.GetService('agents').GetAgentsByID()
    facWarService = sm.GetService('facwar')
    skills = {}
    for agentID in agentsByID:
        agent = agentsByID[agentID]
        fa = standingInfo.get(agent.factionID, 0.0)
        if fa:
            fa = fa.rank * 10.0
        co = standingInfo.get(agent.corporationID, 0.0)
        if co:
            co = co.rank * 10.0
        ca = standingInfo.get(agent.agentID, 0.0)
        if ca:
            ca = ca.rank * 10.0
        isLimitedToFacWar = False
        if agent.agentTypeID == const.agentTypeFactionalWarfareAgent and facWarService.GetCorporationWarFactionID(agent.corporationID) != session.warfactionid:
            isLimitedToFacWar = True
        if agent.agentTypeID in valid and CanUseAgent(agent.level, agent.agentTypeID, fa, co, ca, agent.corporationID, agent.factionID, skills) and isLimitedToFacWar == False:
            if agent.stationID:
                if agent.solarsystemID not in solarsystems:
                    solarsystems[agent.solarsystemID] = {}
                if agent.stationID not in solarsystems[agent.solarsystemID]:
                    solarsystems[agent.solarsystemID][agent.stationID] = []
                solarsystems[agent.solarsystemID][agent.stationID].append(agent)

    hintFunc = HintMyAgents2
    npcDivisions = sm.GetService('agents').GetDivisions()
    maxTotal = 0
    for solarsystemID, stations in solarsystems.iteritems():
        totalAgents = sum((len(agents) for agents in stations.itervalues()))
        maxTotal = max(maxTotal, totalAgents)

    for solarsystemID, stations in solarsystems.iteritems():
        totalAgents = sum((len(agents) for agents in stations.itervalues()))
        colorInfo.solarSystemDict[solarsystemID] = (totalAgents / float(maxTotal),
         None,
         (hintFunc, (stations, npcDivisions)),
         DEFAULT_MAX_COLOR)

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/agentSomeHere'), DEFAULT_MAX_COLOR, data=None))


def ColorStarsByAvoidedSystems(colorInfo, starColorMode):
    avoidanceSolarSystemIDs = sm.GetService('clientPathfinderService').GetExpandedAvoidanceItems()
    hintFunc = lambda : localization.GetByLabel('UI/Map/StarModeHandler/advoidSystemOnList')
    for solarSystemID in avoidanceSolarSystemIDs:
        colorInfo.solarSystemDict[solarSystemID] = (1.0,
         1.0,
         (hintFunc, ()),
         DEFAULT_MAX_COLOR)

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/advoidNotAdvoided'), NEUTRAL_COLOR, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/advoidAdvoided'), DEFAULT_MAX_COLOR, data=None))


def ColorStarsByRealSunColor(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        colorInfo.solarSystemDict[solarSystemID] = (STAR_SIZE_UNIFORM,
         0.0,
         None,
         solarSystem.star.color)

    for typeID, sunType in mapcommon.SUN_DATA.iteritems():
        name = cfg.invtypes.Get(typeID).typeName
        colorInfo.legend.add(LegendItem(name, name, sunType.color, data=None))


def ColorStarsByPIScanRange(colorInfo, starColorMode):
    starmap = sm.GetService('starmap')
    playerLoc = cfg.evelocations.Get(session.solarsystemid2)
    playerPos = (playerLoc.x, playerLoc.y, playerLoc.z)
    skills = sm.GetService('skills').MySkillLevelsByID()
    remoteSensing = skills.get(const.typeRemoteSensing, 0)
    hintFunc = lambda range: localization.GetByLabel('UI/Map/StarModeHandler/scanHintDistance', range=range)
    for solarSystemID, solarSystem in starmap.GetKnownUniverseSolarSystems().iteritems():
        systemLoc = cfg.evelocations.Get(solarSystemID)
        systemPos = (systemLoc.x, systemLoc.y, systemLoc.z)
        dist = geo2.Vec3Distance(playerPos, systemPos) / const.LIGHTYEAR
        proximity = None
        for i, each in enumerate(const.planetResourceScanningRanges):
            if not i >= 5 - remoteSensing:
                continue
            if each >= dist:
                proximity = i

        if proximity is not None:
            colorInfo.solarSystemDict[solarSystemID] = (0.5 + 0.1 * proximity,
             0.2 * proximity,
             (hintFunc, (dist,)),
             None)

    colorInfo.colorList = BASE5_COLORRANGE
    colorCurve = starmap.GetColorCurve(colorInfo.colorList)
    for i, each in enumerate(const.planetResourceScanningRanges):
        if not i >= 5 - remoteSensing:
            continue
        lbl = localization.GetByLabel('UI/Map/StarModeHandler/scanLegendDistance', range=const.planetResourceScanningRanges[i])
        colorInfo.legend.add(LegendItem(i, lbl, starmap.GetColorCurveValue(colorCurve, 1.0 / 5.0 * i), data=None))


def ColorStarsByPlanetType(colorInfo, starColorMode):
    planetTypeID = starColorMode[1]
    starmap = sm.GetService('starmap')
    systems = defaultdict(int)
    maxCount = 0
    for solarSystemID, d in starmap.GetKnownUniverseSolarSystems().iteritems():
        if planetTypeID in d.planetCountByType:
            systems[solarSystemID] = v = d.planetCountByType[planetTypeID]
            maxCount = max(maxCount, v)
        else:
            systems[solarSystemID] = 0

    planetTypeName = cfg.invtypes.Get(planetTypeID).typeName
    caption = planetTypeName + ': %d'
    hintFunc = lambda count: caption % count
    for solarSystemID, count in systems.iteritems():
        if count:
            colorInfo.solarSystemDict[solarSystemID] = (count / float(maxCount),
             count / float(maxCount),
             (hintFunc, (count,)),
             None)

    colorInfo.colorList = BASE3_COLORRANGE
    colorInfo.colorType = STAR_COLORTYPE_DATA
    if maxCount > 1:
        colorInfo.legend.add(LegendItem(0, caption % 1, colorInfo.colorList[0], data=None))
    colorInfo.legend.add(LegendItem(1, caption % maxCount, colorInfo.colorList[-1], data=None))


def ColorStarsByMyColonies(colorInfo, starColorMode):
    planetSvc = sm.GetService('planetSvc')
    planetRows = planetSvc.GetMyPlanets()
    if len(planetRows):
        systems = defaultdict(int)
        for row in planetRows:
            systems[row.solarSystemID] += 1

        maxCount = max(systems.itervalues())
        divisor = 1.0 if maxCount == 1 else 1.0 / (maxCount - 1)
        hintFunc = lambda count: localization.GetByLabel('UI/Map/StarModeHandler/planetsColoniesCount', count=count)
        for solarSystemID, count in systems.iteritems():
            colorInfo.solarSystemDict[solarSystemID] = (count / float(maxCount),
             count / float(maxCount),
             (hintFunc, (count,)),
             None)

        colorInfo.colorList = BASE3_COLORRANGE
        colorInfo.colorType = STAR_COLORTYPE_DATA
        if maxCount > 1:
            colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/planetsColoniesCount', count=1), colorInfo.colorList[0], data=None))
        colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/planetsColoniesCount', count=maxCount), colorInfo.colorList[-1], data=None))


def ColorStarsByIncursions(colorInfo, starColorMode):
    ms = session.ConnectToRemoteService('map')
    participatingSystems = ms.GetSystemsInIncursions()
    hintFuncStaging = lambda : localization.GetByLabel('UI/Map/StarModeHandler/incursionStageing')
    hintFuncActive = lambda : localization.GetByLabel('UI/Map/StarModeHandler/incursionPraticipant')
    for solarSystemID, sceneType in participatingSystems:
        if sceneType == taleConst.scenesTypes.staging:
            colorInfo.solarSystemDict[solarSystemID] = (1.0,
             0,
             (hintFuncStaging, ()),
             BASE3_COLORRANGE[0])
        elif sceneType == taleConst.scenesTypes.vanguard:
            colorInfo.solarSystemDict[solarSystemID] = (0.5,
             1,
             (hintFuncActive, ()),
             BASE3_COLORRANGE[-1])

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/incursionStageing'), BASE3_COLORRANGE[0], data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/incursionPraticipant'), BASE3_COLORRANGE[-1], data=None))


def ColorStarsByIncursionsGM(colorInfo, starColorMode):
    ms = session.ConnectToRemoteService('map')
    participatingSystems = ms.GetSystemsInIncursionsGM()
    green = COLOR_GREEN
    yellow = COLOR_YELLOW
    orange = COLOR_ORANGE
    red = COLOR_RED
    hintFuncStaging = lambda : localization.GetByLabel('UI/Map/StarModeHandler/incursionStageing')
    hintFuncVanguard = lambda : localization.GetByLabel('UI/Map/StarModeHandler/incursionVanguard')
    hintFuncAssault = lambda : localization.GetByLabel('UI/Map/StarModeHandler/incursionAssault')
    hintFuncHq = lambda : localization.GetByLabel('UI/Map/StarModeHandler/incursionHQ')
    for solarSystemID, sceneType in participatingSystems:
        if sceneType == taleConst.scenesTypes.staging:
            colorInfo.solarSystemDict[solarSystemID] = (1.0,
             0,
             (hintFuncStaging, ()),
             green)
        elif sceneType == taleConst.scenesTypes.vanguard:
            colorInfo.solarSystemDict[solarSystemID] = (0.5,
             1,
             (hintFuncVanguard, ()),
             yellow)
        elif sceneType == taleConst.scenesTypes.assault:
            colorInfo.solarSystemDict[solarSystemID] = (0.5,
             2,
             (hintFuncAssault, ()),
             orange)
        elif sceneType == taleConst.scenesTypes.headquarters:
            colorInfo.solarSystemDict[solarSystemID] = (0.5,
             3,
             (hintFuncHq, ()),
             red)

    colorInfo.colorType = STAR_COLORTYPE_DATA
    colorInfo.legend.add(LegendItem(0, localization.GetByLabel('UI/Map/StarModeHandler/incursionStageing'), green, data=None))
    colorInfo.legend.add(LegendItem(1, localization.GetByLabel('UI/Map/StarModeHandler/incursionVanguard'), yellow, data=None))
    colorInfo.legend.add(LegendItem(2, localization.GetByLabel('UI/Map/StarModeHandler/incursionAssault'), orange, data=None))
    colorInfo.legend.add(LegendItem(3, localization.GetByLabel('UI/Map/StarModeHandler/incursionHQ'), red, data=None))


def ColorStarsByJobs24Hours(colorInfo, starColorMode, activityID):
    systemRows = sm.RemoteSvc('map').GetIndustryJobsOverLast24Hours(activityID)
    if systemRows:
        maxJobs = max((r.noOfJobs for r in systemRows))
        intensityFunc = lambda value: value / maxJobs
        colorScalarFunc = lambda value: value / maxJobs
        hintFunc = lambda solarSystemID, value: (lambda : localization.GetByLabel('UI/Map/StarModeHandler/jobsStartedLast24Hours', noOfJobs=value), ())
        jobsBySystem = {row.solarSystemID:row.noOfJobs for row in systemRows}
        colorInfo.solarSystemDict.update(_GetColorDict(jobsBySystem, intensityFunc, colorScalarFunc, hintFunc))
        colorInfo.colorList = BASE3_COLORRANGE
        colorInfo.colorType = STAR_COLORTYPE_DATA


def ColorStarsByIndustryCostModifier(colorInfo, starColorMode, activityID):
    systemRows = sm.RemoteSvc('map').GetIndustryCostModifier(activityID)
    minValue = min(systemRows.values())
    maxValue = max(systemRows.values())
    colorScalarFunc = lambda value: (value - minValue) / (maxValue - minValue)
    hintFunc = lambda solarSystemID, value: (lambda : GetByLabelTemp('UI/Map/StarModeHandler/industryCostModifier', index=value * 100.0), ())
    colorInfo.solarSystemDict.update(_GetColorDict(systemRows, colorScalarFunc, colorScalarFunc, hintFunc))
    colorInfo.colorList = ((0.5, 0.32, 0.0, 1.0), (0.7, 0.0, 0.01, 1.0))
    colorInfo.colorType = STAR_COLORTYPE_DATA


def _GetColorDict(valueBySolarSystem, intensityFunc, colorScalarFunc, hintFunc):
    """
    Updates the colorInfo with
    
    :param dict[int, float] valueBySolarSystem: maps solar system IDs with value
    :param func intensityFunc: maps value to intensity (size) of the dot
    :param func colorScalarFunc: maps value to the color of the dot
    :param func hintFunc: maps the solar system ID and value to the hint info
    
    :rtype: dict[int, tuple]
    """
    colorInfoBySolarSystemID = {}
    for solarSystemID, value in valueBySolarSystem.iteritems():
        colorInfoBySolarSystemID[solarSystemID] = (colorScalarFunc(value),
         intensityFunc(value),
         hintFunc(solarSystemID, value),
         None)

    return colorInfoBySolarSystemID
