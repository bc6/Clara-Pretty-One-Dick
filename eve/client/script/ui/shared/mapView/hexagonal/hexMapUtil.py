#Embedded file name: eve/client/script/ui/shared/mapView/hexagonal\hexMapUtil.py
import geo2
import blue
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.line import Line
from eve.client.script.ui.control.buttons import Button
from eve.client.script.ui.control.checkbox import Checkbox
from eve.client.script.ui.control.eveLabel import EveLabelMedium, EveLabelLarge
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from eve.common.script.sys.eveCfg import IsRegion
import uthread
import sys
import carbonui.const as uiconst
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.shared.mapView.hexagonal import hexUtil
FIXED_LAYOUT_BY_ID = {9: {10000001: (-4, 1),
     10000002: (0, -2),
     10000003: (-1, -4),
     10000004: (9, -1),
     10000005: (-9, 0),
     10000006: (-7, -1),
     10000007: (-7, -4),
     10000008: (-6, -1),
     10000009: (-8, -2),
     10000010: (-2, -5),
     10000011: (-5, -2),
     10000012: (-6, 1),
     10000013: (-3, -4),
     10000014: (-2, 3),
     10000015: (-2, -6),
     10000016: (0, -5),
     10000017: (9, 1),
     10000018: (-5, -5),
     10000019: (10, 0),
     10000020: (6, 4),
     10000021: (-6, -5),
     10000022: (-2, 5),
     10000023: (1, -7),
     10000025: (-5, 7),
     10000027: (-4, -3),
     10000028: (-2, 0),
     10000029: (-2, -2),
     10000030: (0, 0),
     10000031: (-5, 3),
     10000032: (4, -1),
     10000033: (3, -4),
     10000034: (-2, -3),
     10000035: (0, -7),
     10000036: (0, 1),
     10000037: (8, -2),
     10000038: (2, 0),
     10000039: (-4, 4),
     10000040: (-4, -6),
     10000041: (4, -7),
     10000042: (0, -1),
     10000043: (3, 1),
     10000044: (7, -6),
     10000045: (-2, -7),
     10000046: (1, -8),
     10000047: (-1, 1),
     10000048: (4, -5),
     10000049: (4, 7),
     10000050: (1, 6),
     10000051: (3, -8),
     10000052: (7, -1),
     10000053: (-5, -8),
     10000054: (5, 1),
     10000055: (0, -8),
     10000056: (-5, 4),
     10000057: (1, -4),
     10000058: (2, -2),
     10000059: (-3, 6),
     10000060: (0, 3),
     10000061: (-7, 2),
     10000062: (-5, 5),
     10000063: (-1, 5),
     10000064: (8, -3),
     10000065: (8, 3),
     10000066: (-3, -6),
     10000067: (5, -3),
     10000068: (6, -5),
     10000069: (1, -6)},
 10000021: {20000258: (2, 1),
            20000259: (1, 0),
            20000260: (0, 1),
            20000261: (-1, 1),
            20000262: (-1, 0),
            20000263: (1, -1),
            20000264: (2, -1),
            20000265: (0, -1),
            20000266: (1, 1),
            20000267: (1, -2),
            20000268: (-1, -2),
            20000269: (-1, -1),
            20000270: (-2, -1)}}
SMALLID = -1
MEDIUMID = -2
LARGEID = -3
SLOT_PATTERN_SMALL = [(-3, -2),
 (-3, 0),
 (-2, 2),
 (0, -2),
 (0, 0),
 (2, 2),
 (3, -2),
 (3, 0)]
SLOT_PATTERN_MEDIUM = [(-5, -2),
 (-4, 2),
 (-3, -4),
 (-3, -1),
 (-2, 2),
 (-2, 4),
 (-1, -3),
 (0, -1),
 (0, 1),
 (0, 3),
 (1, -3),
 (2, 2),
 (2, 4),
 (3, -4),
 (3, -1),
 (4, 2),
 (5, -2)]
SLOT_PATTERN_LARGE = [(-6, -2),
 (-6, 0),
 (-5, -5),
 (-5, 2),
 (-4, 5),
 (-3, -7),
 (-3, -1),
 (-2, -5),
 (-2, 2),
 (-1, -8),
 (-1, 5),
 (0, -3),
 (0, 3),
 (1, -6),
 (1, -1),
 (2, -2),
 (2, 5),
 (3, -8),
 (3, 0),
 (5, -7),
 (5, -5),
 (5, -3),
 (5, 2),
 (5, 4),
 (6, 0),
 (8, -4),
 (8, -1),
 (8, 2),
 (8, 4)]
TESTLINEPLOT = -4
TESTLINEPLOT_PATTERN = [(-1, 0),
 (0, -1),
 (0, 0),
 (1, -1),
 (1, 0)]

class DebugMapBrowser(Window):
    default_windowID = 'DebugMapBrowser'
    default_caption = 'Map Debug View'
    autoLoadTimer = None
    loadedObjectID = None
    currentMap = None
    clipRect = None

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.SetTopparentHeight(0)
        uthread.new(self.LoadOptions)

    def LoadOptions(self):
        PrimeMapData()
        self.objectIDs = sorted(uicore.mapObjectDataByID.keys())
        main = self.GetMainArea()
        main.clipChildren = True
        main.padding = 6
        lg = LayoutGrid(parent=main, columns=3, cellPadding=2, align=uiconst.TOTOP)
        self.objectLabel = EveLabelLarge(bold=True)
        lg.AddCell(self.objectLabel, colSpan=lg.columns - 1)
        self.inputEdit = SinglelineEdit(OnReturn=self.OnInputConfirm, align=uiconst.TOPRIGHT)
        self.inputEdit.SetHistoryVisibility(True)
        lg.AddCell(self.inputEdit, colSpan=1)
        b = Button(func=self.BrowsePrev, label='Previous')
        lg.AddCell(b, colSpan=2)
        Button(parent=lg, func=self.BrowseNext, label='Next', align=uiconst.TOPRIGHT)
        lg.FillRow()
        lg.AddCell(Line(align=uiconst.TOTOP), colSpan=lg.columns, cellPadding=(0, 4, 0, 4))
        b = Button(func=self.BrowseNextLoop, label='Browse next loop', fixedwidth=240)
        lg.AddCell(b, colSpan=lg.columns)
        self.browseLoopButton = b
        settings.user.ui.Set('mapDebugViewRefreshLayout', 0)
        c = Checkbox(configName='mapDebugViewRefreshLayout', text='Refresh layouts', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugViewRefreshLayout', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugViewStopOnErrors', text='Stop on error', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugViewStopOnErrors', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugViewIgnoreFixed', text='Ignore fixed layouts', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugViewIgnoreFixed', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugViewEditEnabled', text='Editmode enabled', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugViewEditEnabled', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugSubdivision', text='Show Grid Subdivision', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugSubdivision', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapLoadCombined', text='Load Combined', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapLoadCombined', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugShowIDs', text='Show IDs', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugShowIDs', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugLoadHexLines', text='Load Hex Lines', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugLoadHexLines', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        c = Checkbox(configName='mapDebugShowExitPoints', text='Show Exit Points', align=uiconst.TOPLEFT, checked=settings.user.ui.Get('mapDebugShowExitPoints', 0), wrapLabel=False, callback=self.OnCheckBoxChange)
        lg.AddCell(c, colSpan=lg.columns)
        lg.FillRow()
        lg.AddCell(Line(align=uiconst.TOTOP), colSpan=lg.columns, cellPadding=(0, 4, 0, 4))
        b = Button(func=self.ScanCurrent, label='Scan Current', fixedwidth=240)
        lg.AddCell(b, colSpan=lg.columns)
        b = Button(func=self.AutoFitSize, label='Auto Fit', fixedwidth=240)
        lg.AddCell(b, colSpan=lg.columns)
        self.statsLabel = EveLabelMedium(parent=lg)
        lg.FillRow()
        self.clipRect = Container(parent=uicore.layer.main, align=uiconst.CENTER, width=800, height=600, clipChildren=True)
        Frame(bgParent=self.clipRect)
        Fill(bgParent=self.clipRect, color=(0, 0, 0, 1))
        self.LoadObjectID(loadObjectID=10000001)

    def Close(self, *args, **kwds):
        Window.Close(self, *args, **kwds)
        if self.currentMap and not self.currentMap.destroyed:
            self.currentMap.Close()
            self.currentMap = None
        if self.clipRect:
            self.clipRect.Close()
            self.clipRect = None

    def OnCheckBoxChange(self, *args, **kwds):
        if self.loadedObjectID:
            uthread.new(self.LoadObjectID, self.loadedObjectID)

    def LoadObjectID(self, loadObjectID, *args, **kwds):
        self.loadedObjectID = loadObjectID
        self.objectLabel.text = '%s %s/%s' % (loadObjectID, self.objectIDs.index(loadObjectID) + 1, len(self.objectIDs))
        if getattr(self, 'currentMap', None):
            self.currentMap.Close()
        inEditMode = settings.user.ui.Get('mapDebugViewEditEnabled', 0)
        from eve.client.script.ui.shared.mapView.hexagonal.hexMap import HexMap
        self.currentMap = HexMap(parent=self.clipRect, state=uiconst.UI_NORMAL, editMode=inEditMode)
        stopOnErrors = settings.user.ui.Get('mapDebugViewStopOnErrors', 0)
        ignoreFixed = settings.user.ui.Get('mapDebugViewIgnoreFixed', 0)
        refreshLayout = settings.user.ui.Get('mapDebugViewRefreshLayout', 0)
        if refreshLayout:
            refreshLayout = loadObjectID != const.locationUniverse
        if refreshLayout:
            resolved = PlotMapObjects(self.currentMap, loadObjectID)
            if not resolved and stopOnErrors:
                self.autoLoadTimer = None
        else:
            self.currentMap.LoadMapData(loadObjectID, ignoreFixedLayout=ignoreFixed)
            if loadObjectID > 9 and not settings.user.ui.Get('mapLoadCombined', 0):
                ol, ll, penalty = ScanAllOverlap(self.currentMap)
                if penalty:
                    print 'Loaded', loadObjectID, 'penalty', penalty
                    if stopOnErrors:
                        self.autoLoadTimer = None

    def BrowsePrev(self, *args, **kwds):
        self.autoLoadTimer = None
        if self.loadedObjectID:
            ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
            if ctrl:
                i = 1
            else:
                i = self.objectIDs.index(self.loadedObjectID)
            self.LoadObjectID(self.objectIDs[max(0, i - 1)])

    def BrowseNext(self, *args, **kwds):
        if self.destroyed:
            self.autoLoadTimer = None
            return
        if self.loadedObjectID:
            i = self.objectIDs.index(self.loadedObjectID)
            if i + 1 < len(self.objectIDs):
                self.LoadObjectID(self.objectIDs[i + 1])
                return True

    def AutoFitSize(self, *args):
        self._AutoFitSize(self, *args)

    def _AutoFitSize(self, *args):
        print 'meee'
        hexMap = self.currentMap
        layout = hexMap.GetCurrentLayout()
        newlayout, size = AutoFitLayout(layout)
        for objectID, column_row in newlayout.iteritems():
            hexCell = hexMap.objectByID[objectID]
            hexCell.MoveToCR(*column_row)

        hexMap.UpdateJumpLines()
        hexMap.SetMapSize(size)

    def ScanCurrent(self, *args):
        self._ScanCurrent(*args)

    def _ScanCurrent(self, *args):
        if self.currentMap:
            ol, ll, penalty = ScanAllOverlap(self.currentMap)
            print penalty

    def MakePattern(self, *args):
        pass

    def BrowseNextLoop(self, *args):
        if self.autoLoadTimer:
            self.browseLoopButton.SetLabel('Browse next loop')
            self.autoLoadTimer = None
        else:
            self.browseLoopButton.SetLabel('Stop')
            self.autoLoadTimer = AutoTimer(1, self.AutoBrowse)

    def AutoBrowse(self):
        stillLoading = self.BrowseNext()
        if not stillLoading:
            self.autoLoadTimer = None

    def OnInputConfirm(self, *args, **kwds):
        try:
            toInt = int(self.inputEdit.GetValue())
            if toInt in self.objectIDs:
                self.LoadObjectID(toInt)
        except:
            pass


def PrimeMapData():
    starmapService = sm.GetService('starmap')
    allRegions = starmapService.GetKnownUniverseRegions()
    allConstellations = starmapService.GetKnownUniverseConstellations()
    allSolarSystems = starmapService.GetKnownUniverseSolarSystems()
    data = {}
    jumpsByID = {}
    parentByID = {}
    exitConnectionsByID = {}
    regionJumps = []
    jumpsByID[const.locationUniverse] = regionJumps
    data[const.locationUniverse] = []
    for regionID, regionData in allRegions.iteritems():
        if regionID > const.mapWormholeRegionMin:
            continue
        data[const.locationUniverse].append(regionID)
        parentByID[regionID] = const.locationUniverse
        for neighbourRegionID in regionData.neighbours:
            if neighbourRegionID > const.mapWormholeRegionMin:
                continue
            jumpID = sorted((regionID, neighbourRegionID))
            if jumpID not in regionJumps:
                regionJumps.append(jumpID)

        jumps = []
        jumpsByID[regionID] = jumps
        data[regionID] = []
        exitJumps = []
        exitConnectionsByID[regionID] = exitJumps
        for constellationID in regionData.constellationIDs:
            if constellationID > const.mapWormholeConstellationMin:
                continue
            data[regionID].append(constellationID)
            parentByID[constellationID] = regionID
            constellation = allConstellations[constellationID]
            for neighbourID in constellation.neighbours:
                if neighbourID > const.mapWormholeConstellationMin:
                    continue
                neighbourRegionID = allConstellations[neighbourID].regionID
                if neighbourRegionID == constellation.regionID:
                    jumpID = sorted((constellationID, neighbourID))
                    if jumpID not in jumps:
                        jumps.append(jumpID)
                else:
                    jumpID = sorted((constellationID, neighbourRegionID))
                    if jumpID not in jumps:
                        jumps.append(jumpID)

            solarSystemJumps = []
            jumpsByID[constellationID] = solarSystemJumps
            data[constellationID] = []
            for solarSystemID in constellation.solarSystemIDs:
                if solarSystemID > const.mapWormholeSystemMin:
                    continue
                data[constellationID].append(solarSystemID)
                parentByID[solarSystemID] = constellationID
                solarSystemData = allSolarSystems[solarSystemID]
                for solarSystemNeighbourID in solarSystemData.neighbours:
                    if solarSystemNeighbourID > const.mapWormholeSystemMin:
                        continue
                    solarSystemNeighbourConstellationID = allSolarSystems[solarSystemNeighbourID].constellationID
                    solarSystemNeighbourRegionID = allSolarSystems[solarSystemNeighbourID].regionID
                    if solarSystemNeighbourConstellationID == solarSystemData.constellationID:
                        jumpID = sorted((solarSystemID, solarSystemNeighbourID))
                        if jumpID not in solarSystemJumps:
                            solarSystemJumps.append(jumpID)
                    else:
                        exitConnectionsByID[regionID].append((solarSystemID,
                         solarSystemData.constellationID,
                         solarSystemNeighbourID,
                         solarSystemNeighbourConstellationID))
                        if solarSystemNeighbourRegionID == solarSystemData.regionID:
                            jumpID = sorted((solarSystemID, solarSystemNeighbourConstellationID))
                            if jumpID not in solarSystemJumps:
                                solarSystemJumps.append(jumpID)
                        else:
                            jumpID = sorted((solarSystemID, solarSystemNeighbourRegionID))
                            if jumpID not in solarSystemJumps:
                                solarSystemJumps.append(jumpID)

    for pID, pattern in ((SMALLID, SLOT_PATTERN_SMALL),
     (MEDIUMID, SLOT_PATTERN_MEDIUM),
     (LARGEID, SLOT_PATTERN_LARGE),
     (TESTLINEPLOT, TESTLINEPLOT_PATTERN)):
        objs = {}
        conn = set()
        for i, pos in enumerate(pattern):
            objs[i] = pos
            for i2, pos2 in enumerate(pattern):
                if i != i2 and (i2, i) not in conn:
                    conn.add((i, i2))

        registeredPlot = settings.user.ui.Get('mapHexPlotData', {})
        registeredPlot[pID] = objs
        settings.user.ui.Set('mapHexPlotData', registeredPlot)
        data[pID] = objs
        jumpsByID[pID] = list(conn)

    uicore.mapObjectDataByID = data
    uicore.mapConnectionDataByID = jumpsByID
    uicore.mapObjectParentByID = parentByID
    uicore.mapExitConnectionsByID = exitConnectionsByID


def FindLeafs(hexMap, level = 0, leafList = None, connectionByObjectID = None):
    leafs = leafList or {}
    if connectionByObjectID is None:
        connectionByObjectID = {}
        for fromID, toID in hexMap.connectionsByID.iterkeys():
            if uicore.mapObjectParentByID[fromID] != hexMap.objectID:
                continue
            if uicore.mapObjectParentByID[toID] != hexMap.objectID:
                continue
            connectionByObjectID.setdefault(fromID, []).append(toID)
            connectionByObjectID.setdefault(toID, []).append(fromID)

    didFind = False
    for objectID in connectionByObjectID.keys():
        connections = connectionByObjectID[objectID]
        totalConnections = len(connections)
        if totalConnections == 1:
            connectionByObjectID[connections[0]].remove(objectID)
            leafs[objectID] = (connections[0], level)
            didFind = True
            connectionByObjectID.pop(objectID)

    if didFind:
        return FindLeafs(hexMap, level + 1, leafList=leafs, connectionByObjectID=connectionByObjectID)
    return (leafs, connectionByObjectID)


def ReattachLeafs(hexMap, leafs):
    pass


def TryRetractLeafs(hexMap, leafs, startPenalty = None, ignoreNoPenalty = False):
    ol, ll, bestPenalty = ScanAllOverlap(hexMap)
    byLevels = sorted([ (level, leafID, toObjectID) for leafID, (toObjectID, level) in leafs.iteritems() ], reverse=True)
    startRange = 0 if IsRegion(hexMap.objectID) else 1
    for level, leafID, toObjectID in byLevels:
        toObject = hexMap.objectByID.get(toObjectID, None)
        leafObject = hexMap.objectByID.get(leafID, None)
        if toObject and leafObject:
            occupied = hexMap.GetOccupiedSlots()
            initPos = leafObject.GetGridPosition()
            trySlots = toObject.GetNeighborsInRange(startRange=startRange, endRange=startRange + 1)
            bestPos = None
            for column_row in trySlots:
                if column_row in occupied:
                    continue
                leafObject.MoveToCR(*column_row)
                hexMap.UpdateJumpLines()
                ol, ll, penalty = ScanAllOverlap(hexMap)
                if penalty <= bestPenalty:
                    bestPos = column_row
                    bestPenalty = penalty
                if penalty == 0 and not ignoreNoPenalty:
                    return bestPenalty

            if bestPos:
                leafObject.MoveToCR(*bestPos)
            else:
                leafObject.MoveToCR(*initPos)
            hexMap.UpdateJumpLines()

    return bestPenalty


def PlotMapObjects(hexMap, objectID):
    if objectID == 9:
        return
    plotObjectID = objectID
    import random
    r = random.Random()
    r.seed(objectID)
    objectData = uicore.mapObjectDataByID[objectID]
    totalObjects = len(objectData)
    gap = 1 if IsRegion(objectID) else 2
    allSlots = [(0, 0)] + hexUtil.neighbours_amount_step((0, 0), totalObjects, gap, hexMap.isFlatTop, exact=True)
    minColumn = 100000000
    maxColumn = -100000000
    minRow = 100000000
    maxRow = -100000000
    for col, row in allSlots:
        minColumn = min(col, minColumn)
        maxColumn = max(col, maxColumn)
        minRow = min(row, minRow)
        maxRow = max(row, maxRow)

    radius = max(abs(minColumn), maxColumn, abs(minRow), maxRow)
    useExitPoint = settings.user.ui.Get('mapDebugShowExitPoints', 0)
    if useExitPoint:
        radius += 2
    size = radius * 2
    hexMap.SetMapSize(size)
    hexMap.LoadMapData(objectID, loadLayout=False)
    objectIDs = sorted(hexMap.objectByID.keys())
    print '--------------------------------'
    print 'Loaded', objectID, len(objectData), len(allSlots), allSlots
    bestLayout = None
    bestLayoutPenalty = sys.maxint
    hexMap.relocatedHexCells = []
    leafs, core = FindLeafs(hexMap)
    for s in xrange(1000):
        r.shuffle(allSlots)
        for i, objectID in enumerate(objectIDs):
            hexCell = hexMap.objectByID[objectID]
            x, y = allSlots[i]
            hexCell.MoveToCR(x, y)

        hexMap.UpdateJumpLines(refreshLayout=True)
        ol, penalty = ScanForObjectLineOverlaps(hexMap, stopAtPenalty=bestLayoutPenalty)
        if penalty >= bestLayoutPenalty:
            blue.synchro.Yield()
            continue
        ll, penalty = ScanForLineLineOverlaps(hexMap, startPenalty=penalty, stopAtPenalty=bestLayoutPenalty)
        if penalty >= bestLayoutPenalty:
            blue.synchro.Yield()
            continue
        blue.synchro.Yield()
        if 0 < penalty < 10:
            penalty = FixLayout(hexMap, bestLayoutPenalty, leafs, totalObjects)
        bestLayoutPenalty = penalty
        bestLayout = hexMap.GetCurrentLayout()
        print '  New penalty', penalty, s
        if bestLayoutPenalty == 0:
            break
        blue.synchro.Yield()

    for objectID in objectIDs:
        x, y = bestLayout[objectID]
        hexCell = hexMap.objectByID[objectID]
        hexCell.MoveToCR(x, y)

    hexMap.UpdateJumpLines(refreshLayout=True)
    bestLayoutPenalty = FixLayout(hexMap, bestLayoutPenalty, leafs, totalObjects)
    if bestLayoutPenalty == 0:
        handmade = settings.user.ui.Get('mapHexLayout', {})
        if plotObjectID in handmade:
            del handmade[plotObjectID]
        settings.user.ui.Set('mapHexLayout', handmade)
        print '  BINGO resolved %s in %s tries' % (plotObjectID, s)
    else:
        print '  Best Layout Penalty', plotObjectID, bestLayoutPenalty
    registeredPlot = settings.user.ui.Get('mapHexPlotData', {})
    registeredPlot[plotObjectID] = hexMap.GetCurrentLayout()
    settings.user.ui.Set('mapHexPlotData', registeredPlot)
    return bestLayoutPenalty == 0


def FixLayout(hexMap, bestLayoutPenalty, leafs, totalObjects):
    plotObjectID = hexMap.objectID
    leafPenalty = TryRetractLeafs(hexMap, leafs, ignoreNoPenalty=True)
    if bestLayoutPenalty:
        if leafPenalty < bestLayoutPenalty:
            bestLayoutPenalty = leafPenalty
            print '  Best Layout Penalty after leaf retract', plotObjectID, bestLayoutPenalty
        if bestLayoutPenalty:
            allSlots = [(0, 0)] + hexUtil.neighbours_amount_step((0, 0), totalObjects, 1, hexMap.isFlatTop)
            ol, ll, penalty = ScanAllOverlap(hexMap)
            for each in ol:
                resolved = RelocateObject(hexMap, each, allSlots, sleep=False)
                if resolved:
                    ol, ll, penalty = ScanAllOverlap(hexMap)
                    print '  Best Layout after object/line relocation', plotObjectID, penalty
                    if penalty < bestLayoutPenalty:
                        bestLayoutPenalty = penalty
                        if not penalty:
                            break

            relocateLineOwners = set()
            for linePair in ll:
                l1, l2 = linePair
                relocateLineOwners.add(l1[0])
                relocateLineOwners.add(l1[1])
                relocateLineOwners.add(l2[0])
                relocateLineOwners.add(l2[1])

            if relocateLineOwners:
                for lineOwnerID in relocateLineOwners:
                    if lineOwnerID in hexMap.objectByID:
                        hexCell = hexMap.objectByID[lineOwnerID]
                        resolved = RelocateObject(hexMap, hexCell, allSlots, sleep=False)
                        if resolved:
                            ol, ll, penalty = ScanAllOverlap(hexMap)
                            print '  Best Layout after line/line relocation', plotObjectID, penalty
                            if penalty < bestLayoutPenalty:
                                bestLayoutPenalty = penalty
                                if not penalty:
                                    break

    return bestLayoutPenalty


def PlotLayout(hexMap, objectID):
    if objectID == const.locationUniverse:
        return
    plotObjectID = objectID
    import random
    r = random.Random()
    r.seed(objectID)
    objectData = uicore.mapObjectDataByID[objectID]
    radiusStep = 2
    allSlots = [(0, 0)] + hexUtil.neighbours_amount_step((0, 0), len(objectData), radiusStep, True)
    minColumn = 100000000
    maxColumn = -100000000
    minRow = 100000000
    maxRow = -100000000
    for col, row in allSlots:
        minColumn = min(col, minColumn)
        maxColumn = max(col, maxColumn)
        minRow = min(row, minRow)
        maxRow = max(row, maxRow)

    radius = max(abs(minColumn), maxColumn, abs(minRow), maxRow)
    size = radius * 2
    hexMap.SetMapSize(size)
    slots = hexUtil.neighbours_from_pos((0, 0), 0, radius, hexMap.isFlatTop)
    hexMap.LoadMapData(objectID, loadLayout=False)
    objectIDs = sorted(hexMap.objectByID.keys())
    hexMap.relocatedHexCells = []
    layoutPenalty = sys.maxint
    bestLayout = None
    bestLayoutPenalty = None
    for s in xrange(2500):
        r.shuffle(allSlots)
        for i, objectID in enumerate(objectIDs):
            hexCell = hexMap.objectByID[objectID]
            x, y = allSlots[i]
            hexCell.MoveToCR(x, y)

        hexMap.UpdateJumpLines(refreshLayout=True)
        lineOverlapPenalty = ScanForHexLineOverlaps(hexMap, layoutPenalty)
        if not bestLayoutPenalty or lineOverlapPenalty < bestLayoutPenalty:
            bestLayoutPenalty = lineOverlapPenalty
            bestLayout = allSlots[:]
            print 'New best', bestLayoutPenalty
        if bestLayoutPenalty == 0:
            break
        blue.synchro.Yield()

    print 'Best result for ', plotObjectID, bestLayoutPenalty
    for i, objectID in enumerate(sorted(objectIDs)):
        hexCell = hexMap.objectByID[objectID]
        x, y = bestLayout[i]
        hexCell.MoveToCR(x, y)

    hexMap.UpdateJumpLines(refreshLayout=True)
    return bestLayoutPenalty == 0


def ResolveObjectLineOverlap(hexMap, objectLineOverlays, useSlots):
    someResolved = False
    for hexCell in objectLineOverlays:
        resolved = RelocateObject(hexMap, hexCell, useSlots, sleep=False)
        if resolved:
            someResolved = True
        blue.pyos.BeNice(10000)

    return someResolved


def ResolveLineLineOverlap(hexMap, lineOverlays, useSlots):
    done = []
    someResolved = False
    for connectionPair in lineOverlays:
        pairResolved = False
        for connectionID in connectionPair:
            for objectID in connectionID:
                if objectID in done or objectID not in hexMap.objectByID:
                    continue
                done.append(objectID)
                hexCell = hexMap.objectByID[objectID]
                resolved = RelocateObject(hexMap, hexCell, useSlots, sleep=False)
                if resolved:
                    pairResolved = True
                    someResolved = True
                    break
                blue.pyos.BeNice(1)

            if pairResolved:
                break

    return someResolved


def RelocateObject(hexMap, hexObject, useSlots, sleep = False):
    if sleep:
        blue.synchro.Sleep(500)
    hexMap.relocatedHexCells.append(hexObject)
    occupied = hexMap.GetOccupiedSlots()
    object_line_overlaps, line_line_overlaps, positionPenalty = ScanForOverlaps(hexMap)
    fallbackPosition = hexObject.GetGridPosition()
    for column_row in useSlots:
        if column_row in occupied:
            continue
        if sleep:
            blue.synchro.Sleep(5)
        hexObject.MoveToCR(*column_row)
        hexMap.UpdateJumpLines(refreshLayout=True)
        object_line_overlaps, line_line_overlaps, checkPositionPenalty = ScanForOverlaps(hexMap)
        if checkPositionPenalty < positionPenalty:
            fallbackPosition = column_row
            positionPenalty = checkPositionPenalty
            blue.pyos.BeNice(1)
            lineLineOverlapIDs = [ id for pair in line_line_overlaps for line in pair for id in line ]
            if hexObject not in object_line_overlaps and hexObject.objectID not in lineLineOverlapIDs:
                if sleep:
                    blue.synchro.Sleep(500)
                return True

    hexObject.MoveToCR(*fallbackPosition)
    hexMap.UpdateJumpLines(refreshLayout=True)
    if sleep:
        blue.synchro.Sleep(500)
    return False


def ScanAllOverlap(hexMap, stopAtPenalty = None):
    ol, penalty = ScanForObjectLineOverlaps(hexMap, stopAtPenalty=stopAtPenalty)
    ll, penalty = ScanForLineLineOverlaps(hexMap, startPenalty=penalty, stopAtPenalty=stopAtPenalty)
    return (ol, ll, penalty)


def ScanForOverlaps(hexMap, stopAtPenalty = None):
    penalty = 0
    ol, penalty = ScanForObjectLineOverlaps(hexMap, startPenalty=penalty, stopAtPenalty=stopAtPenalty)
    if stopAtPenalty is not None and penalty >= stopAtPenalty:
        return (ol, [], penalty)
    ll, penalty = ScanForLineLineOverlaps(hexMap, startPenalty=penalty, stopAtPenalty=stopAtPenalty)
    return (ol, ll, penalty)


def ScanForObjectLineOverlaps(hexMap, startPenalty = 0, stopAtPenalty = None):
    penalty = startPenalty
    object_line_overlaps = []
    objectIDs = sorted(hexMap.objectByID.keys())
    for objectID in objectIDs:
        uiObject = hexMap.objectByID[objectID]
        objPos = (uiObject.left + hexMap.width / 2.0, uiObject.top + hexMap.height / 2.0)
        for connectionID, line in hexMap.connectionsByID.iteritems():
            if objectID in connectionID:
                continue
            if not line.renderObject.vertices:
                continue
            p1x, p1y = line.renderObject.vertices[0].position
            p2x, p2y = line.renderObject.vertices[1].position
            pointOnLine = hexUtil.closest_point_on_seg((p1x, p1y), (p2x, p2y), objPos)
            dist_v = geo2.Vec2Subtract(pointOnLine, objPos)
            if geo2.Vec2Length(dist_v) < uiObject.hexSize:
                object_line_overlaps.append(uiObject)
                penalty += 100
                if stopAtPenalty is not None and penalty >= stopAtPenalty:
                    return (object_line_overlaps, penalty)

    return (object_line_overlaps, penalty)


def ScanForLineLineOverlaps(hexMap, startPenalty = 0, stopAtPenalty = None):
    penalty = startPenalty
    line_line_overlaps = []
    done = []
    lineIDs = hexMap.connectionsByID.keys()
    for connectionID1 in lineIDs:
        line1 = hexMap.connectionsByID[connectionID1]
        if not line1.renderObject.vertices:
            continue
        for connectionID2 in lineIDs:
            if connectionID1 == connectionID2:
                continue
            if (connectionID1, connectionID2) in done:
                continue
            line2 = hexMap.connectionsByID[connectionID2]
            if not line2.renderObject.vertices:
                continue
            done.append((connectionID1, connectionID2))
            done.append((connectionID2, connectionID1))
            p11 = line1.renderObject.vertices[0].position
            p12 = line1.renderObject.vertices[1].position
            p21 = line2.renderObject.vertices[0].position
            p22 = line2.renderObject.vertices[1].position
            try:
                crossPoint = hexUtil.intersect_line_segments((p11, p12), (p21, p22))
            except ValueError:
                crossPoint = True

            if crossPoint:
                line_line_overlaps.append((connectionID1, connectionID2))
                penalty += 1
                if stopAtPenalty is not None and penalty >= stopAtPenalty:
                    return (line_line_overlaps, penalty)

    return (line_line_overlaps, penalty)


def ScanForObjectObjectOverlaps(hexMap, startPenalty = None, stopAtPenalty = None):
    """Checks for selected overlaps in the drawing"""
    objectIDs = sorted(hexMap.objectByID.keys())
    object_object_overlaps = []
    occupied = []
    for objectID in objectIDs:
        hexCell = hexMap.objectByID[objectID]
        column_row = hexCell.GetGridPosition()
        if column_row in occupied:
            object_object_overlaps.append(hexCell)
            if stopOnFirst:
                break
        occupied.append(column_row)

    return object_object_overlaps


def ScanForHexLineOverlaps(hexMap, lastPenalty = None):
    done = []
    currentPenalty = 0
    lineIDs = hexMap.hexGridConnectionsByID.keys()
    for connectionID1 in lineIDs:
        line1, shadowLine = hexMap.hexGridConnectionsByID[connectionID1]
        for connectionID2 in lineIDs:
            if (connectionID1, connectionID2) in done:
                continue
            line2, shadowLine2 = hexMap.hexGridConnectionsByID[connectionID2]
            if line1 is line2:
                continue
            done.append((connectionID1, connectionID2))
            done.append((connectionID2, connectionID1))
            crossPoints = line1.GetCrossPointsWithLine(line2)
            currentPenalty += len(crossPoints)
            if lastPenalty is not None and currentPenalty > lastPenalty:
                return currentPenalty

    return currentPenalty


def GetPlotDataForObject(objectID, ignoreFixed = None):
    if ignoreFixed is None:
        ignoreFixed = settings.user.ui.Get('mapDebugViewIgnoreFixed', 0)
    registeredPlot = settings.user.ui.Get('mapHexPlotData', {})
    handmade = settings.user.ui.Get('mapHexLayout', {})
    if objectID == const.locationUniverse:
        plotData = FIXED_LAYOUT_BY_ID[objectID]
    elif not ignoreFixed and objectID in handmade:
        plotData = handmade[objectID]
    elif objectID in registeredPlot:
        plotData = registeredPlot[objectID]
    else:
        plotData = None
    return plotData


def GetHexMapBoundaries(objectID):
    minColumn = sys.maxint
    maxColumn = -sys.maxint
    minRow = sys.maxint
    maxRow = -sys.maxint
    plotData = GetPlotDataForObject(objectID)
    if plotData:
        for childID, column_row in plotData.iteritems():
            col, row = column_row
            minColumn = min(col, minColumn)
            maxColumn = max(col, maxColumn)
            minRow = min(row, minRow)
            maxRow = max(row, maxRow)

    else:
        raise RuntimeError('No map layout found for objectID %s' % objectID)
    return (minColumn,
     minRow,
     maxColumn,
     maxRow)


def GetHexMapSizeForObject(objectID):
    minColumn, minRow, maxColumn, maxRow = GetHexMapBoundaries(objectID)
    return int(round(max(abs(minColumn), maxColumn, abs(minRow), maxRow) + 0.5)) * 2


def PrepareCombinedMap(objectID):
    rootLayout = GetPlotDataForObject(objectID)
    rootLayout, rootsize = AutoFitLayout(rootLayout)
    isFlatTop = True
    maxChildSize = 0
    for childID, childGridPosition in rootLayout.iteritems():
        childLayout = GetPlotDataForObject(childID)
        childLayout, size = AutoFitLayout(childLayout)
        maxChildSize = max(maxChildSize, size)

    maxOffset = 0
    layoutData = {}
    connectionData = []
    exitConnectionData = []
    for childID, childGridPosition in rootLayout.iteritems():
        column, row = childGridPosition
        cX, cY = hexUtil.hex_slot_center_position(column, row, isFlatTop, maxChildSize / 2)
        px_hx = hexUtil.pixel_to_hex(cX, cY, 1, isFlatTop)
        ax_cu = hexUtil.axial_to_cube_coordinate(*px_hx)
        ax_cu_rounded = hexUtil.hex_round(*ax_cu)
        cu_ax = hexUtil.cube_to_odd_q_axial_coordinate(*ax_cu_rounded)
        childLayout = GetPlotDataForObject(childID)
        childLayout, size = AutoFitLayout(childLayout)
        connectionData += uicore.mapConnectionDataByID.get(childID, [])
        for grandChildID, grandChildGridPosition in childLayout.iteritems():
            childColumn = cu_ax[0] + grandChildGridPosition[0]
            childRow = cu_ax[1] + grandChildGridPosition[1]
            layoutData[grandChildID] = (childColumn, childRow)
            maxOffset = max(maxOffset, childColumn, abs(childColumn), childRow, abs(childRow))

    connections = uicore.mapExitConnectionsByID.get(objectID, None)
    if connections:
        for fromID, fromParentID, toID, toParentID in connections:
            exitConnectionData.append((fromID, toID))

    combinedLayout, size = AutoFitLayout(layoutData)
    return (combinedLayout,
     connectionData,
     exitConnectionData,
     size)


def AutoFitLayout(layout):
    minColumn = sys.maxint
    maxColumn = -sys.maxint
    minRow = sys.maxint
    maxRow = -sys.maxint
    for objectID, column_row in layout.iteritems():
        col, row = column_row
        minColumn = min(col, minColumn)
        maxColumn = max(col, maxColumn)
        minRow = min(row, minRow)
        maxRow = max(row, maxRow)

    offsetColumn, offsetRows = -(minColumn + maxColumn) / 2, -(minRow + maxRow) / 2
    oddColumnOffset = offsetColumn & 1
    newLayout = {}
    size = 0
    for objectID, (column, row) in layout.iteritems():
        if oddColumnOffset and not column & 1:
            row -= 1
        newLayout[objectID] = (column + offsetColumn, row + offsetRows)
        size = max(size, abs(column + offsetColumn), abs(row + offsetRows))

    size = int(round(size + 0.5)) * 2
    return (newLayout, size)
