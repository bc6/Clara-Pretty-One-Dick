#Embedded file name: eve/client/script/ui/shared/mapView/hexagonal\hexCell.py
import math
import random
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.base import Base, ReverseScaleDpi
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.frame import Frame
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from eve.client.script.ui.control.eveLabel import EveLabelSmall
import carbonui.const as uiconst
from eve.client.script.ui.shared.mapView.hexagonal.hexMap import HexMap
from eve.common.script.sys.eveCfg import IsRegion
import hexUtil

class HexCell(Container):
    default_pickRadius = -1
    default_opacity = 1.0
    default_align = uiconst.CENTER
    default_state = uiconst.UI_PICKCHILDREN
    isFlatTop = True
    editMode = False
    hexGrid = None
    hexSize = 16.0
    hexGridSize = 32.0
    gridPosition = (0, 0)
    outline = None
    positionLabel = None
    objectID = None
    outlineColor = (1, 1, 1, 1)
    subMap = None
    lazyLoadThread = None
    OnDragCallback = None
    OnDragEndCallback = None
    OnMouseDownCallback = None
    OnMouseUpCallback = None
    OnMouseWheelCallback = None
    globalScaling = 1.0
    localScaling = 1.0
    mapsize = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.editMode = attributes.editMode
        self.hexGrid = attributes.hexGrid
        self.hexSize = attributes.hexSize or self.hexSize
        self.hexGridSize = attributes.hexGridSize or self.hexGridSize
        self.isFlatTop = attributes.isFlatTop or self.isFlatTop
        self.sizeUnscaled = hexUtil.hex_slot_size(self.isFlatTop, self.hexSize)
        self.width, self.height = self.sizeUnscaled
        if settings.user.ui.Get('mapDebugShowIDs', 0):
            self.positionLabel = EveLabelSmall(parent=self, align=uiconst.CENTERTOP)
        self.backgroundSprite = Sprite(bgParent=self, texturePath='res:/UI/Texture/classes/HexMap/baseHexUnderlaySmall.png', color=self.hexGrid.mainColor)
        if self.editMode:
            self.state = uiconst.UI_NORMAL

    def Close(self, *args):
        Container.Close(self, *args)
        self.hexGrid = None
        self.OnMouseDownCallback = None
        self.OnMouseUpCallback = None
        self.OnMouseWheelCallback = None

    def SetMapGridSize(self, mapsize):
        self.mapsize = mapsize

    def UpdateAlignment(self, budgetLeft = 0, budgetTop = 0, budgetWidth = 0, budgetHeight = 0, updateChildrenOnly = False):
        ret = Container.UpdateAlignment(self, budgetLeft, budgetTop, budgetWidth, budgetHeight, updateChildrenOnly)
        return ret

    def TraverseHexCell(self, viewportRect, scaling):
        self.globalScaling = scaling
        self._latestViewportData = viewportRect
        w, h = self.sizeUnscaled
        self.width = w * self.globalScaling * self.localScaling
        self.height = h * self.globalScaling * self.localScaling
        if self.gridPosition:
            self.MoveToCR(*self.gridPosition)
        vX, vY, vW, vH = viewportRect
        l = vX + self.left - self.width / 2 + self.parent.width / 2
        r = l + self.width
        t = vY + self.top - self.height / 2 + self.parent.height / 2
        b = t + self.height
        if self.width < 50:
            self.backgroundSprite.texturePath = 'res:/UI/Texture/classes/HexMap/baseHexUnderlaySmall.png'
        elif self.width < 100:
            self.backgroundSprite.texturePath = 'res:/UI/Texture/classes/HexMap/baseHexUnderlayMedium.png'
        else:
            self.backgroundSprite.texturePath = 'res:/UI/Texture/classes/HexMap/baseHexUnderlay.png'
        if (r >= 0 and l <= vW or r >= vW and l <= 0) and (b >= 0 and t <= vH or b >= vH and t <= 0):
            self.display = True
            if self.height < self.hexSize / 2:
                if self.positionLabel:
                    self.positionLabel.display = False
            elif self.positionLabel:
                self.positionLabel.display = True
            if self.height >= 96:
                if not self.editMode and not self.lazyLoadThread and not self.subMap:
                    self.lazyLoadThread = AutoTimer(50 + random.randint(1, 500), self.LoadContent)
                if self.subMap:
                    width, height = hexUtil.hex_slot_size(self.isFlatTop, self.hexSize * 1000.0)
                    self.subMap.localScaling = height / float(self.subMap.sizeUnscaled[1]) / 1000.0
                    self.subMap.width = self.subMap.sizeUnscaled[0] * self.globalScaling * self.subMap.localScaling
                    self.subMap.height = self.subMap.sizeUnscaled[1] * self.globalScaling * self.subMap.localScaling
                    left = (self.parent.width - self.width) / 2 + self.left
                    top = (self.parent.height - self.height) / 2 + self.top
                    self.subMap.TraverseHexMap((vX + left,
                     vY + top,
                     vW,
                     vH), scaling=self.globalScaling * self.localScaling)
            else:
                self.UnloadContent()
        else:
            self.display = False
            self.UnloadContent()

    def GetMap(self):
        return self.subMap

    def LoadContent(self):
        self.lazyLoadThread = None
        if self.objectID is None or self.objectID not in uicore.mapObjectDataByID:
            return
        if not self.display or not self.parent:
            return
        if self.subMap is None:
            from eve.client.script.ui.shared.mapView.hexagonal.hexMap import HexMap
            self.subMap = HexMap(parent=self, parentMap=self.hexGrid, align=uiconst.CENTER, setMapSize=self.mapsize)
            self.subMap.opacity = 0
            self.subMap.LoadMapData(self.objectID)
            self.subMap.state = uiconst.UI_DISABLED
            self.state = uiconst.UI_DISABLED
            width, height = hexUtil.hex_slot_size(self.isFlatTop, self.hexSize * 1000.0)
            self.subMap.localScaling = height / float(self.subMap.sizeUnscaled[1]) / 1000.0
            self.subMap.width = self.subMap.sizeUnscaled[0] * self.globalScaling * self.subMap.localScaling
            self.subMap.height = self.subMap.sizeUnscaled[1] * self.globalScaling * self.subMap.localScaling
            vX, vY, vW, vH = self._latestViewportData
            left = (self.parent.width - self.width) / 2 + self.left
            top = (self.parent.height - self.height) / 2 + self.top
            self.subMap.TraverseHexMap((vX + left,
             vY + top,
             vW,
             vH), scaling=self.globalScaling * self.localScaling)
            uicore.animations.FadeTo(self.subMap, startVal=0.0, endVal=1.0)
        self.subMap.display = True

    def UnloadContent(self):
        self.lazyLoadThread = None
        if self.subMap:
            self.subMap.Close()
            self.subMap = None

    def MoveToXYZ(self, x, y, z):
        """Move in 'cube' coordinate system"""
        column, row = hexUtil.cube_to_axial_coordinate(x, y, z)
        self.MoveToCR(column, row)

    def OffsetCR(self, offsetColumn, offsetRow):
        column, row = self.gridPosition
        oddColumnOffset = offsetColumn & 1
        if oddColumnOffset and not column & 1:
            offsetRow -= 1
        self.MoveToCR(column + offsetColumn, row + offsetRow)

    def MoveToCR(self, column, row):
        """Move in 'column/row' coordinate system"""
        cX, cY = hexUtil.hex_slot_center_position(column, row, self.isFlatTop, self.hexGridSize)
        self.left = cX * self.globalScaling * self.localScaling
        self.top = cY * self.globalScaling * self.localScaling
        self.gridPosition = (column, row)
        if self.positionLabel:
            parentID = uicore.mapObjectParentByID.get(self.objectID, None)
            self.positionLabel.text = '%s<br>%s<br>%s/%s' % (self.objectID,
             parentID,
             column,
             row)

    def GetGridPosition(self):
        return self.gridPosition

    def GetCenterPosition(self):
        return (self.left + self.width / 2, self.top + self.height / 2)

    def GetPosition(self):
        return (self.left, self.top)

    def GetNeighborsInRange(self, startRange = 0, endRange = 1):
        startpos = self.gridPosition
        for i in xrange(startRange):
            startpos = hexUtil.neighbour_axial(startpos, 4, self.isFlatTop)

        ret = []
        for i in xrange(startRange, endRange):
            startpos = hexUtil.neighbour_axial(startpos, 4, self.isFlatTop)
            cr = startpos
            for direction in xrange(6):
                for length in xrange(i + 1):
                    cr = hexUtil.neighbour_axial(cr, direction, self.isFlatTop)
                    ret.append(cr)

        return ret

    def GetSlotNeighborsInDirection(self, column_row, directions = (0, 1, 2, 3, 4, 5), startRange = 0, endRange = 10):
        ret = []
        for direction in directions:
            cr = column_row
            for i in xrange(startRange):
                cr = hexUtil.neighbour_axial(cr, direction, self.isFlatTop)

            for length in xrange(startRange, endRange):
                cr = hexUtil.neighbour_axial(cr, direction, self.isFlatTop)
                ret.append(cr)

        return ret

    def OnMouseDown(self, mouseButton, *args):
        if self.editMode:
            self.dragThread = AutoTimer(1, self.DragHexCell)

    def OnMouseUp(self, mouseButton, *args):
        if self.OnMouseUpCallback:
            self.OnMouseUpCallback(mouseButton, self)

    def OnMouseWheel(self, dz):
        if self.OnMouseWheelCallback:
            self.OnMouseWheelCallback(dz, self)

    def OnDblClick(self, *args):
        if self.objectID and not self.editMode:
            mapRoot = self.FindTopLevelMap()
            if mapRoot:
                mapRoot.LoadMapData(self.objectID)

    def DragHexCell(self):
        if not uicore.uilib.leftbtn:
            self.dragThread = None
            if self.OnDragEndCallback:
                self.OnDragEndCallback(self)
            return
        pl, pt = self.parent.GetAbsolutePosition()
        self.left = uicore.uilib.x - pl - self.parent.width / 2
        self.top = uicore.uilib.y - pt - self.parent.height / 2
        if self.OnDragCallback:
            self.OnDragCallback()

    def FindTopLevelMap(self):
        check = self
        while check:
            if isinstance(check, HexMap) and not check.isChild:
                return check
            check = check.parent

    def DrawOutline(self, margin = 0):
        if self.outline:
            outline = self.outline
        else:
            outline = VectorLineTrace(parent=self, lineWidth=1, idx=0)
            outline.isLoop = True
            self.outline = outline
        outline.Flush()
        self.cornerPoints = []
        colors = [(1, 0, 0, 1),
         (1, 1, 1, 1),
         (0, 1, 0, 1),
         (1, 1, 1, 1),
         (0, 0, 1, 1),
         (1, 1, 1, 1)]
        for i in xrange(6):
            if self.isFlatTop:
                outlineRad = self.displayWidth * 0.5 - margin
                angle = 2.0 * math.pi / 6.0 * i
            else:
                outlineRad = self.displayHeight * 0.5 - margin
                angle = 2.0 * math.pi / 6.0 * (i + 0.5)
            x_i = ReverseScaleDpi(self.displayWidth * 0.5 + outlineRad * math.cos(angle))
            y_i = ReverseScaleDpi(self.displayHeight * 0.5 + outlineRad * math.sin(angle))
            outline.AddPoint((x_i, y_i), colors[i])
            self.cornerPoints.append((x_i, y_i))

    def Hilite(self):
        self.outline.lineWidth = 3

    @apply
    def displayRect():
        fget = Base.displayRect.fget

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

        return property(**locals())

    @apply
    def position():
        doc = '(ui) position of hexMap'

        def fget(self):
            return (self._left, self._top)

        def fset(self, value):
            self.left = value[0]
            self.top = value[1]

        return property(**locals())

    @apply
    def size():
        doc = '(ui) size of hexMap'

        def fget(self):
            return (self._width, self._height)

        def fset(self, value):
            self.width = value[0]
            self.height = value[1]

        return property(**locals())
