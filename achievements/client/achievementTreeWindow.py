#Embedded file name: achievements/client\achievementTreeWindow.py
import weakref
from achievements.client.achievementGroupEntry import AchievementGroupEntry
from achievements.common.achievementGroups import achievementGroups, GetAchievementGroup
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.container import Container
from carbonui.primitives.layoutGrid import LayoutGrid
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.transform import Transform
from carbonui.primitives.vectorlinetrace import VectorLineTrace
from eve.client.script.ui.control.eveLabel import EveLabelMedium, EveLabelLarge, EveLabelSmall
from eve.client.script.ui.control.eveWindow import Window
import carbonui.const as uiconst
import math
import sys
from eve.client.script.ui.control.glowSprite import GlowSprite
from eve.client.script.ui.control.themeColored import SpriteThemeColored, ColorThemeMixin
from eve.client.script.ui.shared.infoPanels.infoPanelControls import InfoPanelLabel
from localization import GetByLabel
import trinity
import geo2
import eve.client.script.ui.eveFontConst as fontConst
LINE_SOLID = 1
LINE_DASHED = 2
LINE_DASHED_ACTIVE = 3
LINE_HIDDEN = 4
STATE_INCOMPLETE = 1
STATE_INPROGRESS = 2
STATE_COMPLETED = 3
SLOT_SIZE = 90
SLOT_SHOW_MOUSEOVER_INFO = False

def hex_slot_size(hexSize):
    width = hexSize * 2
    height = math.sqrt(3.0) / 2.0 * width
    return (width, height)


def hex_slot_center_position(column, row, hexSize):
    width, height = hex_slot_size(hexSize)
    centerX = 0.75 * width * column
    centerY = -(height * row + column % 2 * height * 0.5)
    return (centerX, centerY)


class ActiveAchievementInfo(Container):
    __notifyevents__ = ['OnAchievementTreeMouseOver']
    loadedAchievementGroupID = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.content = Container(parent=self, state=uiconst.UI_PICKCHILDREN, align=uiconst.TOALL)
        sm.RegisterNotify(self)
        if attributes.achievementGroupID:
            self.LoadAchievementGroup(attributes.achievementGroupID)

    def OnAchievementTreeMouseOver(self, groupID):
        if self.loadedAchievementGroupID != groupID:
            self.LoadAchievementGroup(groupID)

    def ReloadAchievementGroup(self):
        self.LoadAchievementGroup(self.loadedAchievementGroupID)

    def LoadAchievementGroup(self, groupID):
        self.loadedAchievementGroupID = groupID
        self.content.Flush()
        groupData = GetAchievementGroup(groupID)
        if groupData:
            AchievementGroupEntry(parent=self.content, groupInfo=groupData, align=uiconst.TOTOP, padding=(10, 4, 4, 0), markActive=True, animateIn=True)


class AchievementTreeLegend(LayoutGrid):
    default_columns = 2
    default_cellPadding = 3
    default_state = uiconst.UI_DISABLED

    def ApplyAttributes(self, attributes):
        LayoutGrid.ApplyAttributes(self, attributes)
        iconMap = [(GetByLabel('Achievements/UI/active'), 'res:/UI/Texture/classes/Achievements/iconActiveLegend.png'),
         (GetByLabel('Achievements/UI/incomplete'), 'res:/UI/Texture/classes/Achievements/iconIncomplete.png'),
         (GetByLabel('Achievements/UI/partial'), 'res:/UI/Texture/classes/Achievements/iconPartial.png'),
         (GetByLabel('Achievements/UI/complete'), 'res:/UI/Texture/classes/Achievements/iconComplete.png')]
        for label, texturePath in iconMap:
            EveLabelSmall(text=label, parent=self, align=uiconst.CENTERRIGHT)
            GlowSprite(texturePath=texturePath, parent=self, pos=(0, 0, 20, 20))


class AchievementTreeConnection(VectorLineTrace, ColorThemeMixin):
    default_lineWidth = 1.0
    default_colorType = uiconst.COLORTYPE_UIHILIGHTGLOW
    default_opacity = 1.0
    glowLine = None
    glowLineColor = (1, 1, 1, 0.5)
    localScale = 1.0
    __notifyevents__ = ['OnUIScalingChange']

    def ApplyAttributes(self, attributes):
        VectorLineTrace.ApplyAttributes(self, attributes)
        ColorThemeMixin.ApplyAttributes(self, attributes)
        self.lineType = LINE_SOLID
        self.fromID = attributes.fromID
        self.toID = attributes.toID
        self.glowLine = VectorLineTrace(parent=self.parent, lineWidth=20, spriteEffect=trinity.TR2_SFX_COPY, texturePath='res:/UI/Texture/classes/Achievements/lineGlow.png', name='glowLine', blendMode=trinity.TR2_SBM_ADDX2, opacity=0.3)
        sm.RegisterNotify(self)

    def Close(self, *args):
        if self.glowLine and not self.glowLine.destroyed:
            self.glowLine.Close()
        VectorLineTrace.Close(self, *args)

    def OnUIScalingChange(self, *args):
        self.PlotLineTrace()

    def UpdateFromToPosition(self, fromObject, toObject, localScale):
        self.localScale = localScale
        self.fromPosition = (fromObject.left + fromObject.width / 2, fromObject.top + fromObject.height / 2)
        self.toPosition = (toObject.left + toObject.width / 2, toObject.top + toObject.height / 2)
        self.PlotLineTrace()

    def SetLineType(self, lineType):
        self.lineType = lineType
        self.PlotLineTrace()

    def PlotLineTrace(self):
        self.Flush()
        if self.glowLine:
            self.glowLine.Flush()
        if self.lineType in (LINE_DASHED, LINE_DASHED_ACTIVE):
            self.PlotDashLine()
        elif self.lineType == LINE_SOLID:
            self.PlotSolidLine()
        else:
            return
        if self.lineType == LINE_DASHED_ACTIVE:
            vecDir = geo2.Vec2Subtract(self.toPosition, self.fromPosition)
            vecLength = geo2.Vec2Length(vecDir)
            vecDirNorm = geo2.Vec2Normalize(vecDir)
            r, g, b = self.GetRGB()
            GLOWCOLOR = (r,
             g,
             b,
             1.0)
            GAPCOLOR = (r,
             g,
             b,
             0.0)
            self.glowLine.AddPoint(self.fromPosition, GAPCOLOR)
            point = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, vecLength * 0.5))
            self.glowLine.AddPoint(point, GLOWCOLOR)
            self.glowLine.AddPoint(self.toPosition, GAPCOLOR)
            self.glowLine.textureWidth = vecLength
            uicore.animations.MorphScalar(self.glowLine, 'textureOffset', startVal=0.0, endVal=1.0, curveType=uiconst.ANIM_LINEAR, duration=2.0, loops=uiconst.ANIM_REPEAT)

    def PlotSolidLine(self):
        r, g, b = self.GetRGB()
        DASHCOLOR = (r,
         g,
         b,
         1.0)
        GAPCOLOR = (r,
         g,
         b,
         0.0)
        MARGIN = 16.0 * self.localScale
        vecDir = geo2.Vec2Subtract(self.toPosition, self.fromPosition)
        vecLength = geo2.Vec2Length(vecDir)
        vecDirNorm = geo2.Vec2Normalize(vecDir)
        startPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, MARGIN))
        self.AddPoint(startPoint, GAPCOLOR)
        startPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, MARGIN + 8))
        self.AddPoint(startPoint, DASHCOLOR)
        startPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, vecLength - MARGIN - 8))
        self.AddPoint(startPoint, DASHCOLOR)
        startPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, vecLength - MARGIN))
        self.AddPoint(startPoint, GAPCOLOR)

    def PlotDashLine(self):
        dashSize = 2.0
        gapSize = 7.0
        r, g, b = self.GetRGB()
        DASHCOLOR = (r,
         g,
         b,
         1.0)
        GAPCOLOR = (r,
         g,
         b,
         0.0)
        MARGIN = 16.0 * self.localScale
        vecDir = geo2.Vec2Subtract(self.toPosition, self.fromPosition)
        vecLength = geo2.Vec2Length(vecDir)
        vecDirNorm = geo2.Vec2Normalize(vecDir)
        p = MARGIN
        while p < vecLength - MARGIN:
            startPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, p - 0.5))
            self.AddPoint(startPoint, GAPCOLOR)
            fromPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, p))
            self.AddPoint(fromPoint, DASHCOLOR)
            p = min(vecLength - MARGIN, dashSize + p)
            toPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, p))
            self.AddPoint(toPoint, DASHCOLOR)
            endPoint = geo2.Vec2Add(self.fromPosition, geo2.Vec2Scale(vecDirNorm, p + 0.5))
            self.AddPoint(endPoint, GAPCOLOR)
            p += gapSize


class AchievementTreeSlot(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_pickRadius = -1
    nameLabel = None
    tooltipPanel = None
    localScale = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.achievementGroupID = attributes.achievementGroupID
        self.hexGridPosition = attributes.hexGridPosition
        self.nameLabel = InfoPanelLabel(parent=self.parent, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, idx=0)
        self.stateSprite = GlowSprite(parent=self, pos=(0, 0, 20, 20), align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.activeEffectSprite = SpriteThemeColored(parent=self, state=uiconst.UI_DISABLED, spriteEffect=trinity.TR2_SFX_MODULATE, blendMode=trinity.TR2_SBM_ADDX2, texturePath='res:/UI/Texture/classes/Achievements/hexPingGlow.png', textureSecondaryPath='res:/UI/Texture/classes/Achievements/hexPingMask.png', pos=(0, 0, 300, 300), align=uiconst.CENTER, opacity=0.0)
        self.activeStateSprite = SpriteThemeColored(parent=self, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Achievements/hexActive.png', pos=(0, 0, 200, 200), align=uiconst.CENTER, opacity=0.0, blendMode=trinity.TR2_SBM_ADDX2, colorType=uiconst.COLORTYPE_UIHILIGHTGLOW)
        self.backgroundSprite = SpriteThemeColored(bgParent=self, texturePath='res:/UI/Texture/classes/Achievements/hexBackIncomplete.png', colorType=uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.5)
        self.UpdateGroupState()

    def Close(self, *args, **kwds):
        if self.nameLabel and not self.nameLabel.destroyed:
            self.nameLabel.LoadTooltipPanel = None
            self.nameLabel.GetTooltipPosition = None
        return Container.Close(self, *args, **kwds)

    def GetTooltipPosition(self, *args, **kwds):
        return self.GetAbsolute()

    def UpdateGroupState(self):
        activeGroupID = sm.GetService('achievementSvc').GetActiveAchievementGroupID()
        groupData = GetAchievementGroup(self.achievementGroupID)
        totalNum = len(groupData.GetAchievementTasks())
        completed = len([ x for x in groupData.GetAchievementTasks() if x.completed ])
        if totalNum == completed:
            self.stateSprite.SetTexturePath('res:/UI/Texture/classes/Achievements/iconComplete.png')
            self.progressState = STATE_COMPLETED
            self.backgroundSprite.texturePath = 'res:/UI/Texture/classes/Achievements/hexBackComplete.png'
        elif completed:
            if activeGroupID == self.achievementGroupID:
                self.stateSprite.SetTexturePath('res:/UI/Texture/classes/Achievements/iconPartialActive.png')
            else:
                self.stateSprite.SetTexturePath('res:/UI/Texture/classes/Achievements/iconPartial.png')
            self.progressState = STATE_INPROGRESS
            self.backgroundSprite.texturePath = 'res:/UI/Texture/classes/Achievements/hexBackComplete.png'
        else:
            if activeGroupID == self.achievementGroupID:
                self.stateSprite.SetTexturePath('res:/UI/Texture/classes/Achievements/iconIncompleteActive.png')
            else:
                self.stateSprite.SetTexturePath('res:/UI/Texture/classes/Achievements/iconIncomplete.png')
            self.progressState = STATE_INCOMPLETE
            self.backgroundSprite.texturePath = 'res:/UI/Texture/classes/Achievements/hexBackIncomplete.png'
        self.nameLabel.text = groupData.groupName
        if activeGroupID == self.achievementGroupID:
            self.activeEffectSprite.display = True
            self.activeStateSprite.display = True
            uicore.animations.FadeTo(self.activeEffectSprite, startVal=0.7, endVal=0.2, duration=0.5)
            r, g, b, a = sm.GetService('uiColor').GetUIColor(uiconst.COLORTYPE_UIHILIGHT)
            uicore.animations.MorphVector2(self.activeEffectSprite, 'scale', startVal=(2.5, 2.5), endVal=(0.0, 0.0), duration=0.33)
            uicore.animations.SpColorMorphTo(self.activeStateSprite, startColor=(0, 0, 0, 0), endColor=(r,
             g,
             b,
             1.0), duration=0.3, curveType=uiconst.ANIM_OVERSHOT, callback=self.PulseActive)
        else:
            uicore.animations.FadeOut(self.activeStateSprite, duration=0.125)
            uicore.animations.FadeOut(self.activeEffectSprite, duration=0.125)
        if self.tooltipPanel:
            tooltipPanel = self.tooltipPanel()
            if tooltipPanel and not tooltipPanel.destroyed:
                tooltipPanel.Flush()
                self.LoadTooltipPanel(tooltipPanel)

    def PulseActive(self):
        r, g, b, a = sm.GetService('uiColor').GetUIColor(uiconst.COLORTYPE_UIHILIGHT)
        uicore.animations.SpColorMorphTo(self.activeStateSprite, startColor=(r,
         g,
         b,
         1.0), endColor=(r * 0.8,
         g * 0.8,
         b * 0.8,
         1.0), duration=1.5, curveType=uiconst.ANIM_WAVE, loops=uiconst.ANIM_REPEAT)

    def UpdateLabelPosition(self):
        if not self.nameLabel:
            return
        if self.localScale < 1.0:
            self.nameLabel.fontsize = fontConst.EVE_MEDIUM_FONTSIZE
        else:
            self.nameLabel.fontsize = fontConst.EVE_LARGE_FONTSIZE
        self.nameLabel.left = self.left + self.width / 2 + 14
        self.nameLabel.top = self.top + (self.height - self.nameLabel.textheight) / 2

    def SetLocalScale(self, localScale):
        self.localScale = localScale
        self.activeEffectSprite.width = self.activeEffectSprite.height = 300 * localScale
        self.activeStateSprite.width = self.activeStateSprite.height = 200 * localScale

    def OnClick(self, *args):
        sm.GetService('achievementSvc').SetActiveAchievementGroupID(self.achievementGroupID)

    def OnMouseEnter(self, *args):
        uicore.animations.FadeTo(self.backgroundSprite, startVal=self.backgroundSprite.opacity, endVal=1.0, duration=0.2, curveType=uiconst.ANIM_OVERSHOT)
        self.moTimer = AutoTimer(10, self.CheckMouseOver)
        if not SLOT_SHOW_MOUSEOVER_INFO:
            self.mouseEnterDelay = AutoTimer(100, self.CheckMouseEnter)

    def CheckMouseEnter(self, *args):
        self.mouseEnterDelay = None
        if uicore.uilib.mouseOver is self:
            sm.ScatterEvent('OnAchievementTreeMouseOver', self.achievementGroupID)

    def CheckMouseOver(self):
        if uicore.uilib.mouseOver is self:
            return
        if uicore.uilib.mouseOver.IsUnder(self):
            return
        if self.nameLabel and uicore.uilib.mouseOver is self.nameLabel:
            return
        self.moTimer = None
        uicore.animations.FadeTo(self.backgroundSprite, startVal=self.backgroundSprite.opacity, endVal=0.5, duration=0.1)

    def GetBounds(self):
        return (self.left,
         self.top,
         self.left + self.width,
         self.top + self.height)

    def LoadTooltipPanel(self, tooltipPanel, *args, **kwds):
        if not SLOT_SHOW_MOUSEOVER_INFO:
            return
        tooltipPanel.columns = 1
        tooltipPanel.margin = (10, 5, 10, 3)
        tooltipPanel.state = uiconst.UI_NORMAL
        groupData = GetAchievementGroup(self.achievementGroupID)
        if groupData:
            AchievementGroupEntry(parent=tooltipPanel, groupInfo=groupData, align=uiconst.TOPLEFT, width=240)

    def GetTooltipPosition(self, *args):
        return self.GetAbsolute()

    def GetTooltipPositionFallbacks(self, *args):
        return []

    def GetTooltipPointer(self, *args):
        return uiconst.POINT_TOP_2

    @apply
    def pos():
        fget = Container.pos.fget

        def fset(self, value):
            Container.pos.fset(self, value)
            self.UpdateLabelPosition()

        return property(**locals())

    @apply
    def left():
        fget = Container.left.fget

        def fset(self, value):
            Container.left.fset(self, value)
            self.UpdateLabelPosition()

        return property(**locals())

    @apply
    def top():
        fget = Container.top.fget

        def fset(self, value):
            Container.top.fset(self, value)
            self.UpdateLabelPosition()

        return property(**locals())


class AchievementTree(Transform):
    hexGridSize = 90.0
    localScale = 1.0
    gridBackground = None
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        Transform.ApplyAttributes(self, attributes)
        self.connections = {}
        self.slotsByID = {}
        self.ShowBackgroundGrid()

    def Close(self, *args):
        Transform.Close(self, *args)
        self.connections = None
        self.slotsByID = None

    def OnMouseWheel(self, dz):
        return
        if dz < 0:
            newScale = self.localScale * 2.0
        else:
            newScale = self.localScale / 2.0
        newScale = max(0.25, min(2.0, newScale))
        if newScale != self.localScale:
            uicore.animations.MorphScalar(self, 'mousewheelscale', self.localScale, newScale, duration=0.2)

    @apply
    def mousewheelscale():

        def fget(self):
            pass

        def fset(self, value):
            self.localScale = value
            self.UpdateTreePositions()

        return property(**locals())

    def ShowBackgroundGrid(self):
        self.gridBackground = Container(parent=self, align=uiconst.TOPLEFT, pos=(0, 0, 10000, 10000))
        for hexColumn in xrange(20):
            for hexRow in xrange(10):
                centerX, centerY = hex_slot_center_position(hexColumn, hexRow, self.hexGridSize * self.localScale * 0.5)
                slotSize = SLOT_SIZE * self.localScale
                hexSlot = Sprite(parent=self.gridBackground, left=centerX - slotSize / 2, top=centerY - slotSize / 2, width=slotSize, height=slotSize, texturePath='res:/UI/Texture/classes/Achievements/hexBack.png', opacity=0.05)
                hexSlot.hexGridPosition = (hexColumn, hexRow)

    def AddSlot(self, hexColumn, hexRow, achievementGroupID):
        centerX, centerY = hex_slot_center_position(hexColumn, hexRow, self.hexGridSize * self.localScale)
        slotSize = SLOT_SIZE * self.localScale
        hexSlot = AchievementTreeSlot(parent=self, left=centerX - slotSize / 2, top=centerY - slotSize / 2, width=slotSize, height=slotSize, achievementGroupID=achievementGroupID, hexGridPosition=(hexColumn, hexRow), idx=0)
        self.slotsByID[achievementGroupID] = hexSlot

    def AddConnection(self, fromAchievementGroupID, toAchievementGroupID):
        fromSlot = self.GetSlotByAchievementGroupID(fromAchievementGroupID)
        toSlot = self.GetSlotByAchievementGroupID(toAchievementGroupID)
        if not fromSlot or not toSlot:
            return
        connection = AchievementTreeConnection(parent=self, fromID=fromAchievementGroupID, toID=toAchievementGroupID)
        self.connections[fromAchievementGroupID, toAchievementGroupID] = connection

    def GetConnectionByIDs(self, fromOrToID1, fromOrToID2):
        if (fromOrToID1, fromOrToID2) in self.connections:
            return self.connections[fromOrToID1, fromOrToID2]
        if (fromOrToID2, fromOrToID1) in self.connections:
            return self.connections[fromOrToID2, fromOrToID1]

    def GetSlotByAchievementGroupID(self, achievementGroupID):
        return self.slotsByID.get(achievementGroupID, None)

    def GetSlots(self):
        return self.slotsByID.values()

    def UpdateTreeState(self):
        for each in self.GetSlots():
            each.UpdateGroupState()

        for connectionID, connection in self.connections.iteritems():
            fromID, toID = connectionID
            fromSlot = self.GetSlotByAchievementGroupID(fromID)
            toSlot = self.GetSlotByAchievementGroupID(toID)
            if not fromSlot or not toSlot:
                continue
            if fromSlot.progressState == STATE_COMPLETED and toSlot.progressState == STATE_COMPLETED:
                connection.SetLineType(LINE_SOLID)
            else:
                activeGroupID = sm.GetService('achievementSvc').GetActiveAchievementGroupID()
                if toID == activeGroupID:
                    connection.SetLineType(LINE_DASHED_ACTIVE)
                else:
                    connection.SetLineType(LINE_DASHED)

    def UpdateTreePositions(self):
        minX = sys.maxint
        maxX = -sys.maxint
        minY = sys.maxint
        maxY = -sys.maxint
        slots = self.GetSlots()
        if self.gridBackground:
            for each in self.gridBackground.children:
                hexColumn, hexRow = each.hexGridPosition
                centerX, centerY = hex_slot_center_position(hexColumn, hexRow, self.hexGridSize * self.localScale * 0.5)
                slotSize = SLOT_SIZE * self.localScale
                each.pos = (centerX - slotSize / 2,
                 centerY - slotSize / 2,
                 slotSize,
                 slotSize)

        for each in slots:
            hexColumn, hexRow = each.hexGridPosition
            centerX, centerY = hex_slot_center_position(hexColumn, hexRow, self.hexGridSize * self.localScale)
            slotSize = SLOT_SIZE * self.localScale
            each.pos = (centerX - slotSize / 2,
             centerY - slotSize / 2,
             slotSize,
             slotSize)
            left, top, right, bottom = each.GetBounds()
            minX = min(left, minX)
            maxX = max(right, maxX)
            minY = min(top, minY)
            maxY = max(bottom, maxY)
            each.SetLocalScale(self.localScale)

        for each in slots:
            each.left -= minX
            each.top -= minY

        if self.gridBackground:
            self.gridBackground.left = -minX
            self.gridBackground.top = -minY
        self.width = -minX + maxX
        self.height = -minY + maxY
        for connectionID, connection in self.connections.iteritems():
            fromID, toID = connectionID
            fromSlot = self.GetSlotByAchievementGroupID(fromID)
            toSlot = self.GetSlotByAchievementGroupID(toID)
            if not fromSlot or not toSlot:
                continue
            connection.UpdateFromToPosition(fromSlot, toSlot, self.localScale)

    def SetLocalScale(self, localScale):
        if localScale != self.localScale:
            self.localScale = localScale
            self.UpdateTreePositions()


class AchievementTreeWindowHeader(Container):
    default_align = uiconst.TOTOP

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        grid = LayoutGrid(parent=self, columns=2)
        self.auraSprite = Sprite(pos=(14, 0, 80, 80), texturePath='res:/UI/Texture/classes/achievements/auraAlpha.png')
        grid.AddCell(self.auraSprite, rowSpan=2)
        header = EveLabelLarge(parent=grid, text='Welcome!', top=16)
        message = EveLabelMedium(parent=grid, text='Welcome blurb', width=300)


class AchievementTreeWindow(Window):
    default_captionLabelPath = 'Achievements/UI/OpportunitiesTreeHeader'
    default_windowID = 'AchievementTreeWindow'
    default_width = 700
    default_height = 420
    default_minSize = (default_width, default_height)
    default_fixedWidth = default_width
    default_fixedHeight = default_height
    default_topParentHeight = 0
    achievementTree = None
    activeInfo = None
    __notifyevents__ = ['OnAchievementChanged',
     'OnAchievementActiveGroupChanged',
     'OnUIColorsChanged',
     'OnAchievementsDataInitialized']

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        mainArea = self.GetMainArea()
        mainArea.clipChildren = True
        infoContainer = Container(parent=mainArea, align=uiconst.TOLEFT_NOPUSH, width=260, padding=6)
        if not SLOT_SHOW_MOUSEOVER_INFO:
            self.activeInfo = ActiveAchievementInfo(parent=infoContainer, achievementGroupID=sm.GetService('achievementSvc').GetActiveAchievementGroupID())
        self.legendInfo = AchievementTreeLegend(parent=mainArea, align=uiconst.BOTTOMRIGHT, left=10, top=10)
        treeClipper = Container(parent=mainArea, padding=4, clipChildren=True)
        self.achievementTree = AchievementTree(parent=treeClipper, align=uiconst.CENTER, left=110, top=-10)
        connections = set()
        for i, achievementGroup in enumerate(achievementGroups):
            column, row = achievementGroup.treePosition
            self.achievementTree.AddSlot(column, row, achievementGroup.groupID)

        for groupID1, groupID2 in connections:
            self.achievementTree.AddConnection(groupID1, groupID2)

        self.achievementTree.UpdateTreePositions()
        self.achievementTree.UpdateTreeState()
        sm.RegisterNotify(self)

    def OnAchievementsDataInitialized(self, *args, **kwds):
        self.achievementTree.UpdateTreeState()
        if self.activeInfo:
            self.activeInfo.ReloadAchievementGroup()

    def OnAchievementActiveGroupChanged(self, *args, **kwds):
        self.achievementTree.UpdateTreeState()

    def OnAchievementChanged(self, *args, **kwds):
        self.achievementTree.UpdateTreeState()
        if self.activeInfo:
            self.activeInfo.ReloadAchievementGroup()

    def OnUIColorsChanged(self, *args, **kwds):
        self.achievementTree.UpdateTreeState()

    def OnResize_(self, *args, **kwds):
        if self.achievementTree:
            if self.width < 800:
                self.achievementTree.SetLocalScale(0.75)
            else:
                self.achievementTree.SetLocalScale(1.0)
