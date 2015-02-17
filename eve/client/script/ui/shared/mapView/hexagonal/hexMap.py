#Embedded file name: eve/client/script/ui/shared/mapView/hexagonal\hexMap.py
import math
import logging
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.base import ScaleDpi, ReverseScaleDpi, Base
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from carbonui.primitives.container import Container
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.shared.mapView.hexagonal import hexUtil
import carbonui.const as uiconst
import geo2
from eve.client.script.ui.shared.mapView.hexagonal.hexMapLine import HexMapLine
from evePathfinder.core import EvePathfinderCore
from evePathfinder.pathfinder import ClientPathfinder
from evePathfinder.pathfinderconst import ROUTE_TYPE_SHORTEST, DEFAULT_SECURITY_PENALTY_VALUE
from evePathfinder.stateinterface import StandardPathfinderInterface, GetCurrentStateHash
import trinity
import uthread
import blue
import pyEvePathfinder
from eve.common.script.sys.eveCfg import IsConstellation, IsRegion
from eve.client.script.ui.shared.mapView.hexagonal.hexMapUtil import PrepareCombinedMap, GetPlotDataForObject, GetHexMapSizeForObject
logger = logging.getLogger(__name__)

class HexMap(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_PICKCHILDREN
    isChild = False
    isCombinedMap = False
    isFlatTop = True
    editMode = False
    parentMap = None
    gridSprite = None
    _morphGlobalScaling = 0.0
    _morphGlobalScalingValues = None
    globalScaling = 1.0
    localScaling = 1.0
    mapsize = 3
    setMapSize = None
    objectID = None
    objectData = None
    objectByID = None
    connectionsByID = None
    hexGridConnectionsByID = {}
    markersByID = None
    colorsInverted = False
    slotsByPosition = None
    hexGridSize = 48.0
    sizeUnscaled = None
    outline = None

    def ApplyAttributes(self, attributes):
        self.parentMap = attributes.parentMap
        self.isChild = bool(self.parentMap)
        self.editMode = attributes.editMode
        self.hexGridSize = attributes.hexGridSize or self.hexGridSize
        self.setMapSize = attributes.setMapSize
        if self.parentMap:
            self.colorsInverted = not self.parentMap.colorsInverted
        Container.ApplyAttributes(self, attributes)
        if self.colorsInverted:
            self.mainColor = (0, 0, 0, 1)
            self.blockColor = (0.75, 0.75, 0.75, 1)
        else:
            self.mainColor = (0.75, 0.75, 0.75, 1)
            self.blockColor = (0, 0, 0, 1)
        Fill(parent=self, align=uiconst.CENTER, pos=(0, 0, 10, 2), color=(1, 0, 0, 1))
        Fill(parent=self, align=uiconst.CENTER, pos=(0, 0, 2, 10), color=(1, 0, 0, 1))

    def Close(self, *args):
        Container.Close(self, *args)
        self.parentMap = None

    @apply
    def morphGlobalScaling():

        def fget(self):
            return self._morphGlobalScaling

        def fset(self, value):
            if value != self._morphGlobalScaling:
                self._morphGlobalScaling = value
                self.globalScaling = value
                w = self.sizeUnscaled[0] * value
                h = self.sizeUnscaled[1] * value
                if self._morphGlobalScalingValues:
                    preMouse, preAbs, parentAbsolute = self._morphGlobalScalingValues
                    pl, pt, pw, ph = preAbs
                    proportionalX = (preMouse[0] - pl) / float(pw)
                    proportionalY = (preMouse[1] - pt) / float(ph)
                    left = preMouse[0] - parentAbsolute[0] - proportionalX * w
                    top = preMouse[1] - parentAbsolute[1] - proportionalY * h
                else:
                    left = self.left
                    top = self.top
                self.pos = (left,
                 top,
                 w,
                 h)
                self.TraverseHexMap()

        return property(**locals())

    def UpdateChildren(self):
        pass

    def TraverseHexMap(self, viewportRect = None, scaling = None):
        if not self.parent:
            return
        if scaling is None:
            scaling = self.globalScaling
        self.globalScaling = scaling
        if self.objectByID:
            if viewportRect is None:
                viewportRect = (self.left,
                 self.top,
                 ReverseScaleDpi(self.parent.displayWidth),
                 ReverseScaleDpi(self.parent.displayHeight))
            else:
                vX, vY, vW, vH = viewportRect
                viewportRect = (vX + self.left,
                 vY + self.top,
                 vW,
                 vH)
            for objectID, hexCell in self.objectByID.iteritems():
                hexCell.TraverseHexCell(viewportRect, self.globalScaling * self.localScaling)

            self.UpdateJumpLines()

    def UpdateAlignment(self, budgetLeft = 0, budgetTop = 0, budgetWidth = 0, budgetHeight = 0, updateChildrenOnly = False):
        ret = Container.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight, updateChildrenOnly)
        return ret

    @apply
    def display():
        fget = Base.display.fget

        def fset(self, value):
            if value != self._display:
                Base.display.fset(self, value)

        return property(**locals())

    @apply
    def displayRect():
        fget = Container.displayRect.fget

        def fset(self, value):
            pW, pH = self._displayWidth, self._displayHeight
            displayX, displayY, displayWidth, displayHeight = value
            self._displayX = int(round(displayX))
            self._displayY = int(round(displayY))
            self._displayWidth = int(round(displayX + displayWidth)) - self._displayX
            self._displayHeight = int(round(displayY + displayHeight)) - self._displayY
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight
            if self._displayWidth != pW or self._displayHeight != pH:
                if self._backgroundlist and len(self.background):
                    self.UpdateBackgrounds()
                if self.outline:
                    self.DrawOutline()
                if self.gridSprite:
                    baseCellSize = hexUtil.hex_slot_size(self.isFlatTop, self.hexGridSize)
                    tileTextureWidth = 288.0
                    tileTextureHeight = 333.0
                    textureScaling = tileTextureHeight / baseCellSize[1]
                    self.gridSprite.rectSecondary = ((self.sizeUnscaled[0] * 2 % (self.hexGridSize * 6) - self.hexGridSize) * textureScaling + self.hexGridSize * textureScaling * 0.75,
                     0.0,
                     tileTextureWidth / self.globalScaling / self.localScaling * textureScaling * 0.5,
                     tileTextureHeight / self.globalScaling / self.localScaling * textureScaling * 0.5)

        return property(**locals())

    def FlushMap(self):
        if self.objectByID:
            for each in self.objectByID.values():
                each.Close()

        if self.connectionsByID:
            for each in self.connectionsByID.values():
                each.Close()

        if self.hexGridConnectionsByID:
            for line1, line2 in self.hexGridConnectionsByID.values():
                line1.Close()
                line2.Close()

        if self.markersByID:
            for each in self.markersByID.values():
                each.Close()

        self.objectByID = {}
        self.connectionsByID = {}
        self.hexGridConnectionsByID = {}
        self.markersByID = {}
        self.slotsByPosition = {}

    def GetVectorBetweenObjectsOnSameLevel(self, fromObjectID, toObjectID, parentObjectID, i = 0):
        plotData = GetPlotDataForObject(parentObjectID, ignoreFixed=False)
        if fromObjectID in plotData:
            column1, row1 = plotData[fromObjectID]
            fromPos = hexUtil.hex_slot_center_position(column1, row1, self.isFlatTop, self.hexGridSize)
        elif self.parentMap and fromObjectID in self.parentMap.markersByID:
            fromPos = self.parentMap.markersByID[fromObjectID].unscaledPosition
        else:
            return
        if toObjectID in plotData:
            column2, row2 = plotData[toObjectID]
            toPos = hexUtil.hex_slot_center_position(column2, row2, self.isFlatTop, self.hexGridSize)
        elif self.parentMap and toObjectID in self.parentMap.markersByID:
            toPos = self.parentMap.markersByID[toObjectID].unscaledPosition
        else:
            return
        diffVec = geo2.Vec2Subtract(toPos, fromPos)
        diffVec = geo2.Vec2Scale(diffVec, 100000000000.0)
        cornerPoints = []
        for i in xrange(6):
            if self.isFlatTop:
                outlineRad = self.width * 0.5
                angle = 2.0 * math.pi / 6.0 * i
            else:
                outlineRad = self.height * 0.5
                angle = 2.0 * math.pi / 6.0 * (i + 0.5)
            x_i = outlineRad * math.cos(angle)
            y_i = outlineRad * math.sin(angle)
            cornerPoints.append((x_i, y_i))

        for i in xrange(6):
            p1 = cornerPoints[i]
            p2 = cornerPoints[i - 1]
            crossPoint = hexUtil.intersect_line_segments((p1, p2), ((0.0, 0.0), diffVec))
            if crossPoint:
                return crossPoint

    def LoadExitPoints(self, exitData, parentID):
        for exitID in exitData:
            if self.objectID not in exitID:
                continue
            a, b = exitID
            if a == self.objectID:
                toID = b
            else:
                toID = a
            crossPoint = self.GetVectorBetweenObjectsOnSameLevel(self.objectID, toID, parentID)
            if IsRegion(toID):
                color = (1, 0, 0, 1)
            elif IsConstellation(toID):
                color = (0, 1, 0, 1)
            else:
                color = (0, 0, 1, 1)
            if crossPoint:
                marker = self.AddMarker(toID, crossPoint[0], crossPoint[1], color=color, size=8)
                marker.state = uiconst.UI_NORMAL
                marker.hint = '%s' % toID

    def LoadMapData(self, objectID, loadLayout = True, ignoreFixedLayout = None, loadCombined = False):
        if objectID not in uicore.mapObjectDataByID:
            return
        loadCombined = loadCombined or settings.user.ui.Get('mapLoadCombined', 0)
        if loadCombined and IsRegion(objectID):
            self.isCombinedMap = True
            layoutData, connectionData, exitConnectionData, size = PrepareCombinedMap(objectID)
            objectData = layoutData.keys()
            plotData = layoutData
        else:
            self.isCombinedMap = False
            objectData = uicore.mapObjectDataByID[objectID]
            connectionData = uicore.mapConnectionDataByID.get(objectID, [])
            plotData = GetPlotDataForObject(objectID, ignoreFixedLayout)
            if plotData:
                size = GetHexMapSizeForObject(objectID)
            else:
                size = 10
            exitConnectionData = []
        self.objectID = objectID
        self.exitConnectionData = exitConnectionData
        self.FlushMap()
        from eve.client.script.ui.shared.mapView.hexagonal.hexCell import HexCell
        for childObjectID in objectData:
            hexCell = HexCell(parent=self, hexGrid=self, hexSize=self.hexGridSize * 0.5, hexGridSize=self.hexGridSize, opacity=1.0, state=uiconst.UI_NORMAL, isFlatTop=self.isFlatTop, editMode=self.editMode, idx=0)
            hexCell.OnMouseWheelCallback = self.OnMouseWheel
            hexCell.OnDragCallback = self.OnHexCellDrag
            hexCell.OnDragEndCallback = self.OnHexCellEndDrag
            hexCell.renderObject.pickRadius = -1
            hexCell.objectID = childObjectID
            self.objectByID[childObjectID] = hexCell

        if loadLayout:
            if plotData:
                try:
                    for _objectID in objectData:
                        hexCell = self.objectByID[_objectID]
                        col, row = plotData[_objectID]
                        hexCell.MoveToCR(col, row)

                except KeyError as e:
                    if ignoreFixedLayout is None:
                        return self.LoadMapData(objectID, ignoreFixedLayout=True)
                    return

            else:
                return
            self.SetMapSize(size)
        loadExitpoints = settings.user.ui.Get('mapDebugShowExitPoints', 0)
        if loadExitpoints:
            self.DrawOutline()
            parentID = uicore.mapObjectParentByID.get(self.objectID, None)
            if parentID and parentID in uicore.mapConnectionDataByID:
                parentConnections = uicore.mapConnectionDataByID[parentID]
                self.LoadExitPoints(parentConnections, parentID)
        loadHexLines = settings.user.ui.Get('mapDebugLoadHexLines', 0)
        self.LoadConnections(connectionData, createHexLines=loadHexLines)
        self.LoadConnections(self.exitConnectionData, createHexLines=loadHexLines)
        if loadHexLines:
            self.UpdateJumpLines(refreshLayout=True)
        if not self.isChild:
            self.TraverseHexMap()

    def LoadConnections(self, connectionData, createHexLines = False):
        for fromID, toID in connectionData:
            if (fromID, toID) in self.connectionsByID or (toID, fromID) in self.connectionsByID:
                continue
            self.connectionsByID[fromID, toID] = VectorLineTrace(parent=self)
            if createHexLines and fromID in self.objectByID and toID in self.objectByID:
                self.hexGridConnectionsByID[fromID, toID] = (HexMapLine(parent=self), HexMapLine(parent=self))

    def GetCurrentLayout(self):
        layoutByObjectID = {}
        for objectID, uiObject in self.objectByID.iteritems():
            layoutByObjectID[objectID] = uiObject.GetGridPosition()

        return layoutByObjectID

    def GetOccupiedSlots(self):
        occupied = []
        for objectID, uiObject in self.objectByID.iteritems():
            if uiObject.GetGridPosition():
                occupied.append(uiObject.GetGridPosition())

        return occupied

    def GetAxialCoordinateFromMousePosition(self):
        absLeft, absTop, absWidth, absHeight = self.GetAbsolute()
        pickX, pickY = uicore.uilib.x - absLeft - absWidth / 2, uicore.uilib.y - absTop - absHeight / 2
        return self.GetAxialCoordinateFromUIPosition(pickX, pickY)

    def GetAxialCoordinateFromUIPosition(self, x, y):
        px_hx = hexUtil.pixel_to_hex(x, y, self.hexGridSize, isFlatTop=self.isFlatTop)
        ax_cu = hexUtil.axial_to_cube_coordinate(*px_hx)
        ax_cu_rounded = hexUtil.hex_round(*ax_cu)
        if self.isFlatTop:
            cu_ax = hexUtil.cube_to_odd_q_axial_coordinate(*ax_cu_rounded)
        else:
            cu_ax = hexUtil.cube_to_odd_r_axial_coordinate(*ax_cu_rounded)
        return cu_ax

    def OnHexCellDrag(self, *args):
        self.TraverseHexMap()

    def OnHexCellEndDrag(self, hexCell, *args):
        if self.globalScaling != 1.0:
            return
        CR = self.GetAxialCoordinateFromMousePosition()
        hexCell.MoveToCR(*CR)
        self.UpdateJumpLines(refreshLayout=True)
        self.TraverseHexMap()
        if not self.isCombinedMap:
            positions = {}
            for objectID, hexCell in self.objectByID.iteritems():
                positions[objectID] = hexCell.GetGridPosition()

            handmade = settings.user.ui.Get('mapHexLayout', {})
            handmade[self.objectID] = positions
            settings.user.ui.Set('mapHexLayout', handmade)

    def OnMouseWheel(self, dz, *args):
        if self.isChild:
            return
        preAbsolute = self.GetAbsolute()
        parentAbsolute = self.parent.GetAbsolute()
        preMouse = (uicore.uilib.x, uicore.uilib.y)
        if dz < 0:
            globalScaling = min(8192.0, self.globalScaling * 4)
        else:
            globalScaling = max(0.125, self.globalScaling / 4)
        self._morphGlobalScalingValues = (preMouse, preAbsolute, parentAbsolute)
        uicore.animations.MorphScalar(self, 'morphGlobalScaling', startVal=self.globalScaling, endVal=globalScaling, duration=0.5)

    def OnMouseDown(self, mouseButton, *args):
        if self.isChild:
            return
        if self.editMode:
            ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
            if ctrl:
                positions = {}
                for objectID, hexCell in self.objectByID.iteritems():
                    positions[objectID] = hexCell.GetGridPosition()

                print self.objectID, ':', positions
                print '----'
                print sorted(positions.values())
        self.initDragData = (self.left,
         self.top,
         uicore.uilib.x,
         uicore.uilib.y)
        self.dragThread = AutoTimer(1, self.DragMap)

    def OnMouseUp(self, mouseButton, *args):
        if self.isChild:
            return

    def DragMap(self):
        if not uicore.uilib.leftbtn:
            self.dragThread = None
        initLeft, initTop, initMouseX, initMouseY = self.initDragData
        dX = initMouseX - uicore.uilib.x
        dY = initMouseY - uicore.uilib.y
        parentWidth = ScaleDpi(self.parent.displayWidth)
        parentHeight = ScaleDpi(self.parent.displayHeight)
        w, h = self.width, self.height
        self.left = min(parentWidth / 2, max(parentWidth / 2 - w, initLeft - dX))
        self.top = min(parentHeight / 2, max(parentHeight / 2 - h, initTop - dY))
        self.TraverseHexMap()

    def UpdateJumpLines(self, refreshLayout = False):
        if self.markersByID:
            for markerID, marker in self.markersByID.iteritems():
                marker.left = marker.unscaledPosition[0] * self.globalScaling * self.localScaling
                marker.top = marker.unscaledPosition[1] * self.globalScaling * self.localScaling

        if self.connectionsByID:
            for (fromID, toID), line in self.connectionsByID.iteritems():
                if fromID < 1000:
                    continue
                line.Flush()
                isExit = False
                lineColor = self.mainColor
                fromObj = self.objectByID.get(fromID, None)
                if fromObj is None and fromID in self.markersByID:
                    fromObj = self.markersByID.get(fromID, None)
                    isExit = True
                    lineColor = (1, 0, 0, 1)
                toObj = self.objectByID.get(toID, None)
                if toObj is None and toID in self.markersByID:
                    toObj = self.markersByID.get(toID, None)
                    isExit = True
                    lineColor = (1, 0, 0, 1)
                if fromObj and toObj:
                    p1, p2 = self.ApplyLineMargin((fromObj.left + self.width / 2.0, fromObj.top + self.height / 2.0), (toObj.left + self.width / 2.0, toObj.top + self.height / 2.0), fromObj.hexSize * self.globalScaling * self.localScaling, toObj.hexSize * self.globalScaling * self.localScaling)
                    if p1 and p2:
                        line.AddPoint(p1, getattr(line, 'lineColor', lineColor))
                        line.AddPoint(p2, getattr(line, 'lineColor', lineColor))

        if self.hexGridConnectionsByID:
            if refreshLayout:
                self.RefreshHexGridConnectionsLayout()
            for (fromID, toID), lines in self.hexGridConnectionsByID.iteritems():
                line, line2 = lines
                line.Flush()
                line2.Flush()
                if line.positionsUnscaled:
                    line.display = True
                    line.display = True
                    line.lineWidth = line.lineWidthUnscaled * self.globalScaling * self.localScaling
                    line2.lineWidth = line.lineWidth * 1.6
                    line.AddPoints(line.positionsUnscaled, scaling=self.globalScaling * self.localScaling)
                    line2.AddPoints(line.positionsUnscaled, scaling=self.globalScaling * self.localScaling)
                else:
                    line.display = False
                    line.display = False

    def ApplyLineMargin(self, p1, p2, radius1, radius2):
        v = geo2.Vec2Subtract(p1, p2)
        vn = geo2.Vec2Normalize(v)
        l = geo2.Vec2Length(v)
        if not l:
            return (None, None)
        s = (radius1 + radius2) / l
        mp1 = geo2.Vec2Subtract(p1, geo2.Vec2Scale(vn, radius1))
        mp2 = geo2.Vec2Add(p2, geo2.Vec2Scale(vn, radius2))
        return (mp1, mp2)

    def SetMapSize(self, size):
        size = self.setMapSize or size
        size += size & 1
        self.mapsize = size
        baseSize = hexUtil.hex_slot_size(self.isFlatTop, self.hexGridSize * size)
        if baseSize != (self.width, self.height):
            self.sizeUnscaled = baseSize
            self.morphGlobalScaling = 0.0
            self.morphGlobalScaling = 1.0

    def DrawOutline(self):
        if self.outline:
            outline = self.outline
        else:
            outline = VectorLineTrace(parent=self, lineWidth=2)
            outline.isLoop = True
            self.outline = outline
        outline.Flush()
        for i in xrange(6):
            if self.isFlatTop:
                outlineRad = self.displayWidth * 0.5
                angle = 2.0 * math.pi / 6.0 * i
            else:
                outlineRad = self.displayHeight * 0.5
                angle = 2.0 * math.pi / 6.0 * (i + 0.5)
            x_i = ReverseScaleDpi(self.displayWidth * 0.5 + outlineRad * math.cos(angle))
            y_i = ReverseScaleDpi(self.displayHeight * 0.5 + outlineRad * math.sin(angle))
            outline.AddPoint((x_i, y_i), (1, 0, 0, 0.8))

    def AddMarker(self, markerID, x, y, color = (1, 1, 1, 0.5), size = 10):
        marker = Container(parent=self, align=uiconst.CENTER, pos=(x,
         y,
         size,
         size), idx=0)
        marker.markerID = markerID
        self.markersByID[markerID] = marker
        marker.unscaledPosition = (x, y)
        marker.hexSize = 1
        Fill(bgParent=marker, color=color)
        return marker

    def PreparePathFinder(self):
        xStep, yStep = hexUtil.hex_slot_size(self.isFlatTop, self.hexGridSize / 2.0)
        xRange = int(self.width / xStep)
        yRange = int(self.height / yStep)
        xRange = xRange - xRange % 3 + 3
        yRange = yRange - yRange % 3 + 3
        pathMap = pyEvePathfinder.EveMap()
        pathMap.CreateRegion(-1)
        pathMap.CreateConstellation(-2, -1)
        self.pathMap = pathMap
        pathfinder = EvePathfinderCore(pathMap)
        pathfinderState = HexMapPathfinderInterface()
        self.avoidPathFinderState = HexMapPathfinderInterface()

        def ConvertPathFinderIDMock(ret):
            return ret

        self.pathfinderHandler = ClientPathfinder(pathfinder, pathfinderState, self.avoidPathFinderState, ConvertPathFinderIDMock, ConvertPathFinderIDMock)
        self.avoidPathFinderState.blockedSpots = []
        self.avoidPathFinderState.usedSpots = []
        if getattr(self, 'pathFindingPairs', None):
            for i in xrange(yRange * xRange):
                pathMap.CreateSolarSystem(i, -2, -1)

            self.AddToPathFinding(self.pathFindingPairs)
            return
        self.column_row_to_pathfinder = column_row_to_pathfinder = {}
        self.pathfinder_to_xy = pathfinder_to_xy = []
        self.pathfinderIndexGrid = indexGrid = []
        self.pathFindingPairs = pathFindingPairs = set()
        self.pathFindingPairSequence = pathFindingPairSequence = {}
        showDebug = not self.isChild and settings.user.ui.Get('mapDebugSubdivision', 0)
        self.pathfinderSize = (xRange, yRange)
        i = 0
        for y in xrange(yRange):
            row = []
            indexGrid.append(row)
            yOdd = y & 1
            for x in xrange(xRange):
                row.append(i)
                posX = x * xStep
                posY = y * yStep
                if y % 2:
                    posX += xStep / 2
                isPrimary = not (x - yOdd + self.mapsize / 2 % 3) % 3
                if isPrimary:
                    px_hx = hexUtil.pixel_to_hex(posX - self.width / 2, posY - self.height / 2, self.hexGridSize, isFlatTop=self.isFlatTop)
                    ax_cu = hexUtil.axial_to_cube_coordinate(*px_hx)
                    ax_cu_rounded = hexUtil.hex_round(*ax_cu)
                    cu_ax = hexUtil.cube_to_odd_q_axial_coordinate(*ax_cu_rounded)
                    column_row_to_pathfinder[cu_ax] = i
                for cMod, rMod in ((-1, 0), (-1 + yOdd, -1), (yOdd, -1)):
                    cIndex = x + cMod
                    rIndex = y + rMod
                    if rIndex >= 0 and cIndex >= 0:
                        try:
                            pathFindingPairs.add((i, indexGrid[rIndex][cIndex]))
                        except IndexError:
                            pass

                if showDebug:
                    if isPrimary:
                        textColor = (1, 0, 0, 1)
                    else:
                        textColor = (0, 1, 0, 1)
                    EveLabelSmall(parent=self, text=str(i), left=posX - self.width / 2, top=posY - self.height / 2, align=uiconst.CENTER, color=textColor)
                pathfinder_to_xy.append((posX, posY))
                pathMap.CreateSolarSystem(i, -2, -1)
                i += 1

        self.AddToPathFinding(self.pathFindingPairs, showDebug)

    def RefreshHexGridConnectionsLayout(self):
        self.PreparePathFinder()
        busyPrimary = [ each.GetGridPosition() for objectID, each in self.objectByID.iteritems() ]
        self.avoidPathFinderState.usedSpots = []
        if self.hexGridConnectionsByID:
            connectionIDs = self.hexGridConnectionsByID.keys()
            unresolved = self.UpdateHexGridConnections(connectionIDs, busyPrimary)
            if unresolved:
                self.LoadExtraPrimaryConnections()
                unresolved = self.UpdateHexGridConnections(unresolved[:], busyPrimary)
                if unresolved:
                    print 'STILL UNRESOLVED !!!!', len(unresolved)

    def LoadExtraPrimaryConnections(self):
        print 'LoadExtraPrimaryConnections'
        xRange, yRange = self.pathfinderSize
        indexGrid = self.pathfinderIndexGrid
        pathFindingPairs = set()
        showDebug = False
        i = 0
        for y in xrange(yRange):
            yOdd = y & 1
            for x in xrange(xRange):
                isPrimary = not (x - yOdd + self.mapsize / 2 % 3) % 3
                if isPrimary:
                    for cMod, rMod in ((-2 + yOdd, -1), (0, -2), (1 + yOdd, -1)):
                        cIndex = x + cMod
                        rIndex = y + rMod
                        if rIndex >= 0 and cIndex >= 0:
                            try:
                                fromIndex, toIndex = i, indexGrid[rIndex][cIndex]
                                pathFindingPairs.add((fromIndex, toIndex))
                                fromIndex, toIndex = sorted((fromIndex, toIndex))
                                if rMod == 0:
                                    self.pathFindingPairSequence[fromIndex, toIndex] = range(fromIndex, toIndex + 1)
                            except IndexError:
                                pass

                i += 1

        self.AddToPathFinding(pathFindingPairs, showDebug, groupID=-1)

    def AddToPathFinding(self, pathFindingPairs, showDebug = False, groupID = 0, debugColor = None):
        pathfinder_to_xy = self.pathfinder_to_xy
        for _p1, _p2 in pathFindingPairs:
            self.pathMap.AddJump(_p1, _p2, groupID)
            self.pathMap.AddJump(_p2, _p1, groupID)
            if (showDebug or debugColor) and not self.isChild:
                self._DebugDrawLine(pathfinder_to_xy[_p1], pathfinder_to_xy[_p2], debugColor or (1, 0, 0, 0.5))

        self.pathMap.Finalize()

    def UpdateHexGridConnections(self, connectionIDs, busyPrimary, lineColor = None):
        column_row_to_pathfinder = self.column_row_to_pathfinder
        pathfinder_to_xy = self.pathfinder_to_xy
        unresolvedConnections = []
        for fromID, toID in connectionIDs:
            fromObj = self.objectByID.get(fromID, None) or self.markersByID.get(fromID, None)
            toObj = self.objectByID.get(toID, None) or self.markersByID.get(toID, None)
            if not hasattr(fromObj, 'GetGridPosition'):
                continue
            if not hasattr(toObj, 'GetGridPosition'):
                continue
            cr1 = fromObj.GetGridPosition()
            cr2 = toObj.GetGridPosition()
            self.avoidPathFinderState.blockedSpots = [ column_row_to_pathfinder[cr] for cr in busyPrimary if cr not in (cr1, cr2) ]
            line, line2 = self.hexGridConnectionsByID[fromID, toID]
            path = self.pathfinderHandler.GetAutopilotPathBetween(column_row_to_pathfinder[cr1], column_row_to_pathfinder[cr2])
            if not path:
                unresolvedConnections.append((fromID, toID))
                line.positionsUnscaled = None
                line2.positionsUnscaled = None
                if (fromID, toID) in self.connectionsByID:
                    self.connectionsByID[fromID, toID].lineColor = (1, 0, 0, 1)
                continue
            if (fromID, toID) in self.connectionsByID:
                self.connectionsByID[fromID, toID].lineColor = (0, 0, 0, 0)
            line.lineColor = lineColor or self.mainColor
            line.lineWidthUnscaled = 4.0
            line2.lineColor = self.blockColor
            line.positionsUnscaled = []
            for i, pointIndex in enumerate(path):
                self.avoidPathFinderState.usedSpots.append(pointIndex)
                try:
                    nextPointIndex = path[i + 1]
                    jumpKey1 = (pointIndex, nextPointIndex)
                    jumpKey2 = (nextPointIndex, pointIndex)
                    occupy = self.pathFindingPairSequence.get(jumpKey1, None) or self.pathFindingPairSequence.get(jumpKey2, None)
                    if occupy:
                        for each in occupy:
                            if each not in self.avoidPathFinderState.usedSpots:
                                self.avoidPathFinderState.usedSpots.append(each)

                except IndexError:
                    pass

                pos = pathfinder_to_xy[pointIndex]
                line.positionsUnscaled.append(pos)

        return unresolvedConnections

    def _DebugDrawLine(self, p1, p2, color = (1, 0, 0, 0.8), margin = 10):
        if margin:
            p1, p2 = self.ApplyLineMargin(p1, p2, margin, margin)
        line = VectorLineTrace(parent=self, lineWidth=1, idx=0)
        x1, y1 = p1
        x2, y2 = p2
        line.AddPoint((x1, y1), color)
        line.AddPoint((x2, y2), color)
        return line


class HexMapPathfinderInterface(StandardPathfinderInterface):

    def __init__(self):
        StandardPathfinderInterface.__init__(self)
        self.blockedSpots = []
        self.usedSpots = []

    def GetAvoidanceList(self):
        return self.blockedSpots + self.usedSpots

    def GetSecurityPenalty(self):
        return 0.0
