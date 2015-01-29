#Embedded file name: eve/client/script/ui/inflight/bracketsAndTargets\inSpaceBracketTooltip.py
from itertools import chain
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbon.common.script.util.format import FmtDist
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.primitives.frame import Frame
from carbonui.primitives.sprite import Sprite
from carbonui.uianimations import animations
from carbonui.util.mouseTargetObject import MouseTargetObject
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.tooltips import TooltipPersistentPanel
import carbonui.const as uiconst
from eve.client.script.ui.inflight.bracketsAndTargets.bracketVarious import MAXOVERLAP_TOOLTIP_ENTRIES
from eve.client.script.ui.inflight.overview import SpaceObjectIcon
import state
import blue
import uthread
import trinity
import fleetbr
from carbonui.primitives.layoutGrid import LayoutGridRow, LayoutGrid
TOOLTIPLABELCUTOFF = 150
TOOLTIPLABELCUTOFFFADELENGTH = 20
TOOLTIPPANEL_HEIGHTCAP = 200
TOOLTIPPANEL_ENTRIESCAP = 10
TOOLTIP_OPACITY = 0.8
MINENTRYHEIGHT = 26

class PersistentInSpaceBracketTooltip(TooltipPersistentPanel):
    __notifyevents__ = ['OnStateChange']
    isCompact = False
    sideContainer = None
    scroll = None
    scrollEnabled = False
    loaded = False
    overlaps = None
    overlapSites = None
    debugShowInterest = False

    def ApplyAttributes(self, attributes):
        TooltipPersistentPanel.ApplyAttributes(self, attributes)
        self.align = uiconst.ABSOLUTE
        self.rowsByItemIDs = {}
        sm.RegisterNotify(self)
        uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEDOWN, self.OnGlobalMouseDown)
        MouseTargetObject(self)

    def Close(self, *args):
        TooltipPersistentPanel.Close(self, *args)
        if self.overlaps or self.overlapSites:
            for each in chain(self.overlaps, self.overlapSites):
                each.opacity = 1.0
                each.pickState = uiconst.TR2_SPS_ON

        for layer in (uicore.layer.inflight, uicore.layer.sensorSuite):
            animations.FadeTo(layer, startVal=layer.opacity, endVal=1.0, duration=0.05)

        if self.sideContainer:
            self.sideContainer.Close()

    def IsOverlapBracket(self, bracket):
        return bracket in self.overlaps or bracket in self.overlapSites

    def GetNumberOfBrackets(self):
        return len(self.overlaps) + len(self.overlapSites)

    def CloseWithFade(self, *args):
        self.Close()

    def OnGlobalMouseDown(self, uiObject, *args, **kwds):
        if self.destroyed:
            return False
        if uiObject.IsUnder(self) or uiObject.IsUnder(uicore.layer.menu):
            return True
        if self.sideContainer and uiObject.IsUnder(self.sideContainer):
            return True
        self.CloseWithFade()
        return False

    def OnStateChange(self, itemID, flag, status, *args):
        entry = self.GetBracketEntryByID(itemID)
        if entry:
            if flag in (state.targeted, state.targeting, state.activeTarget):
                entry.UpdateIcon()
            elif flag == state.selected:
                entry.SetSelected(status)
            elif flag == state.mouseOver:
                entry.SetHilited(status)

    def GetBracketEntryByID(self, itemID):
        return self.rowsByItemIDs.get(itemID, None)

    def OnMouseEnter(self, *args):
        self.LoadEntries()

    def LoadTooltip(self, bracket, overlaps, boundingBox, overlapSites, *args, **kwds):
        self.overlaps = overlaps
        self.overlapSites = overlapSites
        self.scrollEnabled = False if self.GetNumberOfBrackets() <= 15 else True
        bracket.SetOrder(0)
        self.SetBackgroundAlpha(TOOLTIP_OPACITY)
        isFloating = bracket.IsFloating()
        if isFloating:
            self.isCompact = settings.user.ui.Get('bracketmenu_floating', True)
        else:
            self.isCompact = settings.user.ui.Get('bracketmenu_docked', False)
        self.LoadGeneric1ColumnTemplate()
        scroll = ScrollContainer(align=uiconst.TOPLEFT, parent=self)
        scroll.isTabStop = False
        scroll.verticalScrollBar.align = uiconst.TORIGHT_NOPUSH
        scroll.verticalScrollBar.width = 3
        self.scroll = scroll
        subGrid = LayoutGrid(parent=scroll, align=uiconst.TOPLEFT, columns=1 if self.isCompact else 3, name='bracketTooltipSubGrid')
        self.subGrid = subGrid
        if self.isCompact:
            self.sideContainer = BracketTooltipSidePanel(align=uiconst.TOPLEFT, parent=self.parent, idx=self.parent.children.index(self))
            self.sideContainer.display = False
            uthread.new(self.UpdateSideContainer)
        self.LoadEntries()
        self.state = uiconst.UI_NORMAL

    def LoadEntries(self):
        if self.loaded:
            return
        self.loaded = True
        self.subGrid.Flush()
        overlaps = self.overlaps
        self.margin = 3
        rowOrder = []
        for bracket in overlaps:
            row = self.subGrid.AddRow(rowClass=BracketTooltipRow, bracket=bracket, isCompact=self.isCompact, sideContainer=self.sideContainer)
            self.rowsByItemIDs[bracket.itemID] = row
            rowOrder.append(row)

        for bracket in self.overlapSites:
            row = self.subGrid.AddRow(rowClass=SensorOverlaySiteTooltipRow, bracket=bracket, isCompact=self.isCompact, sideContainer=self.sideContainer)
            data = bracket.data
            self.rowsByItemIDs[data.GetSiteType(), data.siteID] = row
            rowOrder.append(row)

        self.subGrid.RefreshGridLayout()
        MAXVISIBLE = MAXOVERLAP_TOOLTIP_ENTRIES
        totalHeight = 0
        for row in rowOrder[:MAXVISIBLE]:
            totalHeight += row.height

        self.scroll.width = self.subGrid.width + (5 if len(rowOrder) > MAXVISIBLE else 0)
        self.scroll.height = totalHeight
        self.state = uiconst.UI_NORMAL

    def IsOwnerPickable(self):
        owner = self.owner
        if not owner:
            return False
        for row in self.rowsByItemIDs.values():
            if row.GetBracket():
                break
        else:
            return False

        prestate = owner.state
        owner.state = uiconst.UI_NORMAL
        try:
            ol, ot, ow, oh = owner.GetTooltipPosition()
            ol = uicore.ScaleDpiF(ol)
            ot = uicore.ScaleDpiF(ot)
            ow = uicore.ScaleDpiF(ow)
            oh = uicore.ScaleDpiF(oh)
            renderObject, pyObject = uicore.uilib.PickScreenPosition(int(ol + ow / 2), int(ot + oh / 2))
            if pyObject and (pyObject.IsUnder(uicore.layer.menu) or pyObject.IsUnder(uicore.layer.bracket) or pyObject.IsUnder(uicore.layer.sensorSuite)):
                return True
            if pyObject is not owner:
                tryPick = ((ol + 1, ot + oh / 2),
                 (ol + ow - 1, ot + oh / 2),
                 (ol + ow / 2, ot + 1),
                 (ol + ow / 2, ot + oh - 1))
                hits = 0
                for x, y in tryPick:
                    renderObject, pyObject = uicore.uilib.PickScreenPosition(int(x), int(y))
                    if pyObject is owner:
                        hits += 1
                        if hits == 2:
                            return True
                    if pyObject and pyObject.IsUnder(uicore.layer.menu):
                        return True

        finally:
            owner.state = prestate

        return pyObject is owner

    def UpdateSideContainer(self):
        rightAligned = (uiconst.POINT_RIGHT_1, uiconst.POINT_RIGHT_2, uiconst.POINT_RIGHT_3)
        while not self.destroyed:
            if not hasattr(self, 'menuPointFlag'):
                blue.pyos.synchro.SleepWallclock(1)
                continue
            if self.menuPointFlag in rightAligned or self.left + self.width + self.sideContainer.width > uicore.desktop.width:
                self.sideContainer.SetContentAlign(uiconst.TORIGHT)
                self.sideContainer.left = self.left - self.sideContainer.width
                for row in self.rowsByItemIDs.values():
                    row.UpdateDynamicValues()

            else:
                self.sideContainer.SetContentAlign(uiconst.TOLEFT)
                self.sideContainer.left = self.left + self.width
            self.sideContainer.top = self.top
            self.sideContainer.height = self.height
            self.sideContainer.grid.top = self.scroll.mainCont.top
            self.sideContainer.opacity = self.opacity
            if self.beingDestroyed:
                self.sideContainer.display = False
            else:
                self.sideContainer.display = True
            blue.pyos.synchro.SleepWallclock(1)


class BracketShadowLabel(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    mainLabel = None
    mainShadowLabel = None
    sideMargins = (0, 0)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        mainLabel = EveLabelSmall(parent=self, state=uiconst.UI_DISABLED, color=(1, 1, 1, 1), width=attributes.width or 0, autoFitToText=attributes.autoFitToText or False)
        mainShadowLabel = EveLabelSmall(parent=self, state=uiconst.UI_DISABLED, color=(0, 0, 0, 1), width=attributes.width or 0, autoFitToText=attributes.autoFitToText or False)
        mainShadowLabel.renderObject.spriteEffect = trinity.TR2_SFX_BLUR
        self.mainLabel = mainLabel
        self.mainShadowLabel = mainShadowLabel
        self.text = attributes.text

    def SetSideMargins(self, leftMargin = 0, rightMargin = 0):
        self.sideMargins = (leftMargin, rightMargin)

    @apply
    def text():

        def fset(self, value):
            self.mainLabel.text = value
            self.mainShadowLabel.text = value
            leftMargin, rightMargin = self.sideMargins
            self.mainLabel.left = -self.mainLabel.mincommitcursor + leftMargin
            self.mainShadowLabel.left = -self.mainLabel.mincommitcursor + leftMargin
            self.width = self.mainLabel.textwidth + leftMargin + rightMargin - self.mainLabel.mincommitcursor
            self.height = self.mainLabel.height

        def fget(self):
            return self.mainLabel.text

        return property(**locals())


class BracketTooltipSidePanel(Container):
    default_state = uiconst.UI_PICKCHILDREN
    default_align = uiconst.TOPLEFT
    default_clipChildren = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.textLabels = []
        self.grid = LayoutGrid(parent=self, columns=3, margin=3, OnGridSizeChanged=self.OnGridSizeChanged)

    def OnGridSizeChanged(self, width, height):
        self.width = width

    def CreateBracketEntry(self):
        self.grid.AddCell(cellObject=Container(align=uiconst.TOPLEFT, pos=(0,
         0,
         2,
         MINENTRYHEIGHT)))
        label = BracketShadowLabel(align=uiconst.CENTERLEFT)
        self.grid.AddCell(cellObject=label)
        self.textLabels.append(label)
        self.grid.AddCell(cellObject=Container(align=uiconst.TOPLEFT, pos=(0,
         0,
         2,
         MINENTRYHEIGHT)))
        return label

    def SetContentAlign(self, contentAlign):
        for textlabel in self.textLabels:
            if contentAlign == uiconst.TOLEFT:
                textlabel.align = uiconst.CENTERLEFT
            else:
                textlabel.align = uiconst.CENTERRIGHT

    def Close(self, *args):
        Container.Close(self, *args)
        self.textLabels = None


class BracketTooltipRowBase(LayoutGridRow):
    selectedSprite = None
    radialMenuSprite = None
    mainShadowLabel = None
    mainLabel = None
    sideEntry = None
    isCompact = False
    default_state = uiconst.UI_NORMAL

    def ApplyAttributes(self, attributes):
        LayoutGridRow.ApplyAttributes(self, attributes)
        self.isCompact = attributes.isCompact or False
        bracket = attributes.bracket
        self.bracket = bracket
        if not self.IsBracketStillValid():
            return
        self.hilite = Fill(bgParent=self, color=(1, 1, 1, 0.0))
        self.iconParent = Container(align=uiconst.CENTER, pos=(0,
         0,
         26,
         MINENTRYHEIGHT), parent=self)
        self.iconObj = self.CreateIcon()
        self.radialMenuSprite = None
        if self.isCompact:
            self.mainLabel = attributes.sideContainer.CreateBracketEntry()
            self.mainLabel.DelegateEvents(self)
        else:
            self.mainLabel = BracketShadowLabel(text='', align=uiconst.CENTERLEFT, width=TOOLTIPLABELCUTOFF, autoFitToText=True, state=uiconst.UI_DISABLED)
            self.AddCell(cellObject=self.mainLabel, cellPadding=(2, 2, 6, 2))
            self.distanceLabel = EveLabelSmall(parent=self, align=uiconst.CENTERRIGHT, left=4)
        self.dynamicsUpdateTimer = None

    def UpdateDynamicValues(self):
        pass

    def StartDynamicUpdates(self):
        self.UpdateDynamicValues()
        self.dynamicsUpdateTimer = AutoTimer(500, self.UpdateDynamicValues)

    def CreateIcon(self):
        return None

    def IsBracketStillValid(self):
        return True

    def Close(self, *args):
        LayoutGridRow.Close(self, *args)
        self.bracket = None
        self.mainLabel = None
        self.dynamicsUpdateTimer = None

    def ShowRadialMenuIndicator(self, slimItem = None, *args):
        if not self.radialMenuSprite:
            self.radialMenuSprite = Sprite(name='radialMenuSprite', parent=self.iconParent, texturePath='res:/UI/Texture/classes/RadialMenu/bracketHilite.png', pos=(0, 0, 20, 20), color=(0.5, 0.5, 0.5, 0.5), align=uiconst.CENTER, state=uiconst.UI_DISABLED)
        self.radialMenuSprite.display = True

    def HideRadialMenuIndicator(self, slimItem = None, *args):
        if self.radialMenuSprite:
            self.radialMenuSprite.display = False

    def GetBracket(self):
        bracket = self.bracket
        if bracket and not bracket.destroyed:
            return bracket
        if self.destroyed:
            return
        self.state = uiconst.UI_DISABLED
        self.opacity = 0.2
        self.bracket = None
        if self.isCompact and not self.mainLabel.destroyed:
            self.mainLabel.state = uiconst.UI_DISABLED
            self.mainLabel.opacity = 0.2

    def SetHilited(self, hiliteState):
        bracket = self.GetBracket()
        if not bracket:
            return
        if hiliteState:
            self.hilite.opacity = 0.2
            if self.mainLabel:
                self.mainLabel.opacity = 1.5
        else:
            self.hilite.opacity = 0.0
            if self.mainLabel:
                self.mainLabel.opacity = 0.8

    def OnClick(self, *args):
        bracket = self.GetBracket()
        if bracket:
            return bracket.OnClick()

    def OnMouseDown(self, *args):
        bracket = self.GetBracket()
        if bracket:
            return bracket.OnMouseDown()

    def OnMouseEnter(self, *args):
        self.SetHilited(True)
        uthread.new(self.WhileMouseOver)
        bracket = self.GetBracket()
        if bracket:
            bracket.OnMouseEnter()

    def WhileMouseOver(self):
        while uicore.uilib.mouseOver is self or uicore.uilib.mouseOver is self.mainLabel:
            blue.pyos.synchro.SleepWallclock(10)
            if self.destroyed:
                break

        self.SetHilited(False)

    def OnMouseExit(self, *args):
        bracket = self.GetBracket()
        if bracket:
            bracket.OnMouseExit()

    def AlignContent(self, align = uiconst.TOLEFT):
        if not self.isCompact:
            return
        if align == uiconst.TOLEFT:
            self.mainLabel.align = uiconst.CENTERLEFT
        else:
            self.mainLabel.align = uiconst.CENTERRIGHT
        if self.mainShadowLabel:
            self.mainShadowLabel.align = self.mainLabel.align

    def GetMenu(self, *args):
        bracket = self.GetBracket()
        if bracket:
            return bracket.GetMenu()


class BracketTooltipRow(BracketTooltipRowBase):
    subLabel = None
    fleetBroadcastSprite = None
    fleetBroadcastType = None

    def ApplyAttributes(self, attributes):
        BracketTooltipRowBase.ApplyAttributes(self, attributes)
        self.selectedSprite = None
        if self.bracket.slimItem:
            selected, hilited = sm.GetService('state').GetStates(self.bracket.slimItem, [state.selected, state.mouseOver])
            self.SetSelected(selected)
            self.SetHilited(hilited)
        self.StartDynamicUpdates()

    def CreateIcon(self):
        self.iconObj = SpaceObjectIcon(state=uiconst.UI_DISABLED, pos=(0, 0, 16, 16), align=uiconst.CENTER, parent=self.iconParent)
        self.UpdateIcon()
        return self.iconObj

    def IsBracketStillValid(self):
        ball = self.bracket.ball
        slimItem = self.bracket.slimItem
        return ball or slimItem

    def UpdateIcon(self):
        if not self.bracket or self.bracket.destroyed:
            return
        ball = self.bracket.ball
        slimItem = self.bracket.slimItem
        if not (ball or slimItem):
            iconNo = getattr(self.bracket, 'iconNo', None)
            if iconNo:
                self.iconObj.iconSprite.LoadIcon(iconNo)
            return
        self.iconObj.UpdateSpaceObjectIcon(slimItem, ball)
        self.iconObj.UpdateSpaceObjectIconColor(slimItem, ball)
        self.iconObj.UpdateSpaceObjectState(slimItem, ball)
        self.iconObj.UpdateSpaceObjectFlagAndBackgroundColor(slimItem, ball)

    def SetSelected(self, selectedState):
        if selectedState:
            if not self.selectedSprite:
                self.selectedSprite = Sprite(parent=self.iconObj, pos=(0, 0, 30, 30), name='selection', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/selectionCircle.png', align=uiconst.CENTER, color=(1, 1, 1, 0.5))
            self.selectedSprite.display = True
        elif self.selectedSprite:
            self.selectedSprite.display = False

    def UpdateDynamicValues(self):
        if self.destroyed:
            return
        bracket = self.GetBracket()
        if not bracket or bracket.destroyed:
            self.dynamicsUpdateTimer = None
            return
        distance = None
        if getattr(bracket, 'showDistance', 1):
            distance = bracket.GetDistance()
            if distance:
                if not self.isCompact:
                    self.distanceLabel.text = FmtDist(distance)
        rightAligned = self.mainLabel.align != uiconst.CENTERLEFT
        fleetBroadcastType = getattr(bracket, 'fleetBroadcastType', None)
        if fleetBroadcastType:
            if fleetBroadcastType != self.fleetBroadcastType:
                self.fleetBroadcastType = fleetBroadcastType
                icon = fleetbr.types[fleetBroadcastType]['smallIcon']
                if not self.fleetBroadcastSprite:
                    self.fleetBroadcastSprite = Sprite(parent=self.mainLabel, pos=(0, 0, 16, 16), state=uiconst.UI_NORMAL, align=uiconst.CENTERLEFT, idx=0)
                    self.fleetBroadcastSprite.DelegateEvents(self)
                self.fleetBroadcastSprite.LoadIcon(icon)
            if rightAligned:
                self.mainLabel.SetSideMargins(0, 18)
                self.fleetBroadcastSprite.align = uiconst.CENTERRIGHT
            else:
                self.mainLabel.SetSideMargins(18, 0)
        elif self.fleetBroadcastSprite:
            self.fleetBroadcastSprite.Close()
            self.fleetBroadcastSprite = None
            self.fleetBroadcastType = None
            self.mainLabel.SetSideMargins()
        tagAndTargetStr = getattr(bracket, 'tagAndTargetStr', None)
        subinfoString = None
        if hasattr(bracket, 'GetSubLabelCallback'):
            subinfoCallback = bracket.GetSubLabelCallback()
            if subinfoCallback:
                subinfoString = subinfoCallback()
        combinedString = ''
        if rightAligned:
            combinedString = '<right>'
        combinedString += bracket.displayName
        if self.isCompact and distance:
            combinedString += ' ' + FmtDist(distance)
        if subinfoString or tagAndTargetStr:
            combinedString += '<br>'
            if tagAndTargetStr:
                combinedString += '<b>' + tagAndTargetStr + '</b>'
            if subinfoString:
                if tagAndTargetStr:
                    combinedString += '  '
                combinedString += '[' + subinfoString + ']'
        self.mainLabel.text = combinedString
        self.iconParent.height = max(MINENTRYHEIGHT, self.mainLabel.height)


class SensorOverlaySiteTooltipRow(BracketTooltipRowBase):

    def ApplyAttributes(self, attributes):
        BracketTooltipRowBase.ApplyAttributes(self, attributes)
        Fill(bgParent=self, color=self.bracket.outerColor, opacity=0.25)
        self.displayName = self.bracket.GetBracketLabelText()
        self.SetHilited(False)
        self.StartDynamicUpdates()

    def CreateIcon(self):
        return Sprite(state=uiconst.UI_DISABLED, pos=(0, 0, 16, 16), align=uiconst.CENTER, parent=self.iconParent, texturePath=self.bracket.innerIconResPath)

    def IsBracketStillValid(self):
        return True

    def AlignContent(self, align = uiconst.TOLEFT):
        if not self.isCompact:
            return
        if align == uiconst.TOLEFT:
            self.mainLabel.align = uiconst.CENTERLEFT
        else:
            self.mainLabel.align = uiconst.CENTERRIGHT
        if self.mainShadowLabel:
            self.mainShadowLabel.align = self.mainLabel.align

    def UpdateDynamicValues(self):
        if self.destroyed:
            return
        bracket = self.GetBracket()
        if not bracket or bracket.destroyed:
            self.dynamicsUpdateTimer = None
            return
        distance = None
        if getattr(bracket, 'showDistance', 1):
            distance = bracket.GetDistance()
            if distance:
                if not self.isCompact:
                    self.distanceLabel.text = FmtDist(distance)
        rightAligned = self.mainLabel.align != uiconst.CENTERLEFT
        combinedString = ''
        if rightAligned:
            combinedString = '<right>'
        combinedString += self.GetDisplayName()
        if self.isCompact and distance:
            combinedString += ' ' + FmtDist(distance)
        self.mainLabel.text = combinedString
        self.iconParent.height = max(MINENTRYHEIGHT, self.mainLabel.height)

    def GetMenu(self, *args):
        bracket = self.GetBracket()
        if bracket:
            return bracket.GetMenu()

    def OnClick(self, *args):
        bracket = self.GetBracket()
        if bracket:
            return bracket.OnClick()

    def OnMouseDown(self, *args):
        bracket = self.GetBracket()
        if bracket:
            sm.GetService('menu').TryExpandActionMenu(None, self, siteData=bracket.data)

    def GetDisplayName(self):
        return self.displayName
