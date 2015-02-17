#Embedded file name: eve/client/script/ui/control\tooltips.py
from carbonui.control.menu import ObjectHasMenu, GetContextMenuOwner
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.sprite import Sprite
import carbonui.const as uiconst
from .eveIcon import Icon, InfoIcon
from .eveLabel import *
from .pointerPanel import PointerPanel, FrameWithPointer, FadeOutPanelAndClose, RefreshPanelPosition
import base
import blue
import uthread
import log
import carbonui.const as uiconst
COLOR_NUMBERVALUE = (0.8,
 0.8,
 0.8,
 1.0)
COLOR_NUMBERVALUE_NEGATIVE = (1.0,
 0.1,
 0.1,
 1.0)
COLOR_NUMBERVALUE_POSITIVE = (1.0,
 0.1,
 0.1,
 1.0)
COLOR_FRAME_NORMAL = (0.75,
 0.9,
 0.98,
 1.0)
SLEEPTIME_EXTEND = 1000
SLEEPTIME_EXTENDFAST = 10
SLEEPTIME_TIMETOLIVE = 50
SLEEPTIME_TIMETOLIVE_EDITABLE = 300

class ShortcutHint(Container):
    default_align = uiconst.TOPRIGHT

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        bgColor = attributes.get('bgColor', (1, 1, 1, 0.1))
        Fill(bgParent=self, color=bgColor)
        textColor = attributes.get('textColor', (1, 1, 1, 0.3))
        self.textLabel = EveLabelMedium(align=uiconst.CENTER, parent=self, text=attributes.text, bold=True, color=textColor)
        self.AdjustSize()

    def AdjustSize(self):
        width = self.textLabel.width + 8
        self.width = width - width % 16 + 16
        self.height = self.textLabel.height


class TooltipGeneric(Container):
    """Tooltip object to replace the old mouseover hints and keeping it
    in sync (behaviour and appearance wise) with TooltipPanel
    """
    default_opacity = 0.0
    pointerSize = 9
    beingDestroyed = None
    scaleTransform = None
    defaultPointer = uiconst.POINT_BOTTOM_2

    def ApplyAttributes(self, attributes):
        attributes.align = uiconst.NOALIGN
        Container.ApplyAttributes(self, attributes)
        self.backgroundFrame = FrameWithPointer(bgParent=self)
        self.textLabel = EveLabelMedium(align=uiconst.TOPLEFT, width=200, autoFitToText=True, parent=self, left=10, top=3)

    def SetTooltipString(self, tooltipString, owner):
        if not tooltipString and self.opacity:
            self.display = False
            return
        self.textLabel.text = tooltipString
        self.owner = owner
        self.pos = (0,
         0,
         uicore.ReverseScaleDpi(self.textLabel.actualTextWidth) + 20,
         uicore.ReverseScaleDpi(self.textLabel.actualTextHeight) + 6)
        RefreshPanelPosition(self)
        uicore.animations.FadeTo(self, startVal=self.opacity, endVal=1.0, duration=0.2, curveType=uiconst.ANIM_SMOOTH)

    @apply
    def left():
        doc = 'x-coordinate of UI element'

        def fget(self):
            return self._left

        def fset(self, value):
            self._left = value
            self.displayX = uicore.ScaleDpiF(self._left)
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX

        return property(**locals())

    @apply
    def top():
        doc = 'y-coordinate of UI element'

        def fget(self):
            return self._top

        def fset(self, value):
            self._top = value
            self.displayY = uicore.ScaleDpiF(self._top)
            ro = self.renderObject
            if ro:
                ro.displayY = self._displayY

        return property(**locals())

    @apply
    def pos():
        doc = 'Position of UI element'

        def fget(self):
            return (self._left,
             self._top,
             self._width,
             self._height)

        def fset(self, value):
            left, top, width, height = value
            doFlag = self._width != width or self._height != height
            self._left = left
            self._top = top
            self._width = width
            self._height = height
            self.displayX = uicore.ScaleDpiF(self._left)
            self.displayY = uicore.ScaleDpiF(self._top)
            self.displayWidth = uicore.ScaleDpiF(self._width)
            self.displayHeight = uicore.ScaleDpiF(self._height)
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight
                if not self._constructingBase and doFlag:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def display():
        doc = 'Is UI element displayed?'

        def fget(self):
            return self._display

        def fset(self, value):
            if value != self._display:
                self._display = value
                ro = self.renderObject
                if ro:
                    ro.display = value

        return property(**locals())

    def Close(self, *args):
        if getattr(uicore.uilib, 'tooltipHandler', None):
            now = blue.os.GetWallclockTime()
            uicore.uilib.tooltipHandler.lastCloseTime = now
        Container.Close(self, *args)
        if getattr(self, 'debugFrame', None):
            self.debugFrame.Close()
        if self.scaleTransform:
            self.scaleTransform.Close()
            self.scaleTransform = None


class TooltipPanel(PointerPanel):
    default_state = uiconst.UI_PICKCHILDREN
    default_align = uiconst.TOPLEFT
    default_opacity = 0.0
    default_cellClipChildren = False

    def Close(self, *args):
        if getattr(uicore.uilib, 'tooltipHandler', None) and len(self.children):
            now = blue.os.GetWallclockTime()
            uicore.uilib.tooltipHandler.lastCloseTime = now
        PointerPanel.Close(self, *args)

    def CloseWithFade(self, *args):
        if getattr(uicore.uilib, 'tooltipHandler', None) and len(self.children):
            now = blue.os.GetWallclockTime()
            uicore.uilib.tooltipHandler.lastCloseTime = now
        FadeOutPanelAndClose(self)

    def ShowPanel(self, owner):
        PointerPanel.ShowPanel(self, owner)
        if hasattr(owner, 'LoadExtendedTooltipPanel'):
            alt = uicore.uilib.Key(uiconst.VK_MENU)
            if alt:
                expandSleeptime = SLEEPTIME_EXTENDFAST
            else:
                expandSleeptime = SLEEPTIME_EXTEND
            self.expandTimer = base.AutoTimer(expandSleeptime, self.ExpandTooltipPanel, owner)
        if self.pickState == uiconst.TR2_SPS_ON:
            timeToLive = SLEEPTIME_TIMETOLIVE_EDITABLE
        else:
            timeToLive = SLEEPTIME_TIMETOLIVE
        self.HoldTillMouseOutside(timeToLive)
        if self.destroyed or self.beingDestroyed:
            return
        if self.opacity:
            FadeOutPanelAndClose(self)
        else:
            self.Close()

    def ExpandTooltipPanel(self, owner):
        self.expandTimer = None
        if self.destroyed or self.beingDestroyed:
            return
        if owner.destroyed:
            return
        owner.LoadExtendedTooltipPanel(self)

    def HoldTillMouseOutside(self, graceTime):
        lastOnTime = blue.os.GetWallclockTime()
        radialMenuSvc = sm.GetService('radialmenu')
        while not self.destroyed:
            now = blue.os.GetWallclockTime()
            if self.pickState == uiconst.TR2_SPS_ON:
                contextMenuOwner = GetContextMenuOwner()
                if contextMenuOwner and contextMenuOwner.IsUnder(self):
                    lastOnTime = now
                    blue.synchro.SleepWallclock(5)
                    continue
                radialMenuOwner = radialMenuSvc.GetRadialMenuOwner()
                if radialMenuOwner and radialMenuOwner.IsUnder(self):
                    lastOnTime = now
                    blue.synchro.SleepWallclock(5)
                    continue
                ownerPickable = self.IsOwnerPickable()
                if not ownerPickable:
                    return False
            mouseInside = self.IsMouseInside()
            if mouseInside:
                lastOnTime = now
                blue.synchro.SleepWallclock(5)
                continue
            blue.synchro.SleepWallclock(1)
            if self.destroyed:
                return False
            if lastOnTime and blue.os.TimeDiffInMs(lastOnTime, now) > graceTime:
                return False

    def IsOwnerPickable(self):
        owner = self.owner
        if not owner:
            return False
        prestate = owner.state
        owner.state = uiconst.UI_NORMAL
        try:
            ol, ot, ow, oh = owner.GetAbsolute()
            ol = uicore.ScaleDpiF(ol)
            ot = uicore.ScaleDpiF(ot)
            ow = uicore.ScaleDpiF(ow)
            oh = uicore.ScaleDpiF(oh)
            renderObject, pyObject = uicore.uilib.PickScreenPosition(int(ol + ow / 2), int(ot + oh / 2))
            if pyObject and pyObject.IsUnder(uicore.layer.menu):
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

    def IsMouseInside(self):
        if self.destroyed:
            return False
        owner = self.owner
        if not owner:
            return False
        mouseOver = uicore.uilib.mouseOver
        if mouseOver is owner:
            return True
        if mouseOver is self or mouseOver.IsUnder(self):
            return True
        focus = uicore.registry.GetFocus()
        if focus and focus.IsUnder(self):
            return True
        return False

    def LoadTooltip(self, *args):
        """ overwritable """
        pass

    def ExpandTooltip(self, owner):
        self.expandTimer = None
        if self.destroyed or self.beingDestroyed:
            return
        if owner.destroyed:
            return
        if hasattr(owner, 'LoadExtendedTooltipPanel'):
            owner.LoadExtendedTooltipPanel(self)

    def AddCommandTooltip(self, command):
        """Accepts command from command service and wraps it up as
        label, shortcut
        description
        """
        label = command.GetName()
        shortcutStr = command.GetShortcutAsString()
        self.AddLabelShortcut(label, shortcutStr)
        detailedDescription = command.GetDetailedDescription()
        if detailedDescription:
            self.AddLabelMedium(text=detailedDescription, align=uiconst.TOPLEFT, wrapWidth=200, colSpan=self.columns, color=(0.6, 0.6, 0.6, 1))

    def AddLabelShortcut(self, label, shortcut):
        self.FillRow()
        labelObj = self.AddLabelMedium(text=label, bold=True, cellPadding=(0, 0, 7, 0), colSpan=self.columns - 1)
        if shortcut:
            ml, mt, mr, mb = self.margin
            shortcutObj = ShortcutHint(text=shortcut)
            self.AddCell(shortcutObj, cellPadding=(7,
             0,
             -mr + 6,
             0))
        else:
            self.AddCell()
            shortcutObj = None
        return (labelObj, shortcutObj)

    def AddLabelValue(self, label, value, valueColor = COLOR_NUMBERVALUE):
        self.FillRow()
        labelObj = self.AddLabelMedium(text=label, align=uiconst.CENTERLEFT, bold=True, cellPadding=(0, 0, 7, 0))
        valueObj = self.AddLabelMedium(text=value, align=uiconst.CENTERRIGHT, color=valueColor, top=1, colSpan=self.columns - 1, cellPadding=(7, 0, 0, 0))
        return (labelObj, valueObj)

    def AddIconLabel(self, icon, label, iconSize = 32):
        self.FillRow()
        iconObj = Sprite(pos=(0,
         0,
         iconSize,
         iconSize), align=uiconst.CENTERLEFT)
        iconObj.LoadIcon(icon, ignoreSize=True)
        self.AddCell(iconObj, cellPadding=(-3, 0, 3, 0))
        labelObj = self.AddLabelMedium(text=label, align=uiconst.CENTERLEFT, bold=True, cellPadding=(0, 0, 7, 0))
        return (iconObj, labelObj)

    def AddIconLabelValue(self, icon, label, value, valueColor = COLOR_NUMBERVALUE, iconSize = 32):
        self.FillRow()
        iconObj = Sprite(pos=(0,
         0,
         iconSize,
         iconSize), align=uiconst.CENTERLEFT)
        iconObj.LoadIcon(icon, ignoreSize=True)
        self.AddCell(iconObj, cellPadding=(-3, 0, 3, 0))
        labelObj = self.AddLabelMedium(text=label, align=uiconst.CENTERLEFT, bold=True, cellPadding=(0, 0, 7, 0))
        valueObj = self.AddLabelMedium(align=uiconst.CENTERRIGHT, bold=True, color=valueColor, top=1, colSpan=self.columns - 2, cellPadding=(7, 0, 0, 0))
        return (iconObj, labelObj, valueObj)

    def AddDivider(self, color = (1, 1, 1, 0.3), cellPadding = None):
        self.FillRow()
        divider = Fill(align=uiconst.TOTOP, state=uiconst.UI_DISABLED, color=color, height=1, padding=(0, 3, 0, 3))
        self.AddCell(divider, colSpan=self.columns, cellPadding=cellPadding)
        return divider

    def AddSpacer(self, width, height, colSpan = 1, rowSpan = 1):
        spacer = Fill(align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, width=width, height=height, color=(0, 0, 0, 0))
        self.AddCell(spacer, colSpan=colSpan, rowSpan=rowSpan)
        return spacer

    def AddLabelSmall(self, state = uiconst.UI_DISABLED, wrapWidth = None, **keywords):
        """Util to add small text to a tooltip"""
        if wrapWidth:
            keywords['width'] = wrapWidth
            keywords['autoFitToText'] = True
        label = EveLabelSmall(state=state, **keywords)
        self.AddCell(label, **keywords)
        return label

    def AddLabelMedium(self, state = uiconst.UI_DISABLED, wrapWidth = None, **keywords):
        """Util to add medium text to a tooltip"""
        if wrapWidth:
            keywords['width'] = wrapWidth
            keywords['autoFitToText'] = True
        label = EveLabelMedium(state=state, **keywords)
        self.AddCell(label, **keywords)
        return label

    def AddLabelLarge(self, state = uiconst.UI_DISABLED, wrapWidth = None, **keywords):
        """Util to add large text to a tooltip"""
        if wrapWidth:
            keywords['width'] = wrapWidth
            keywords['autoFitToText'] = True
        label = EveLabelLarge(state=state, **keywords)
        self.AddCell(label, **keywords)
        return label

    def AddInfoIcon(self, typeID = None, itemID = None, align = uiconst.TOPRIGHT, **keywords):
        infoIcon = InfoIcon(typeID=typeID, itemID=itemID, align=align, size=16, left=0, top=0)
        self.AddCell(infoIcon, **keywords)
        return infoIcon

    def LoadGeneric1ColumnTemplate(self):
        self.columns = 1
        self.margin = (12, 4, 12, 4)
        self.cellPadding = 0
        self.cellSpacing = 0

    def LoadGeneric2ColumnTemplate(self):
        self.columns = 2
        self.margin = (12, 4, 12, 4)
        self.cellPadding = 0
        self.cellSpacing = 0

    def LoadGeneric3ColumnTemplate(self):
        self.columns = 3
        self.margin = (12, 4, 12, 4)
        self.cellPadding = 0
        self.cellSpacing = 0


class TooltipPersistentPanel(TooltipPanel):
    picktestEnabled = True
    checkIfBlocked = False

    def ApplyAttributes(self, attributes):
        TooltipPanel.ApplyAttributes(self, attributes)

    def DisablePickTest(self):
        self.picktestEnabled = False

    def HoldTillMouseOutside(self, graceTime):
        while not self.destroyed and self.owner and not self.owner.destroyed:
            if self.picktestEnabled:
                ownerPickable = self.IsOwnerPickable()
                if not ownerPickable:
                    self.opacity = 0.0
                else:
                    self.opacity = 1.0
            blue.synchro.SleepWallclock(5)

    def IsMouseInside(self):
        return True

    def Close(self, *args):
        PointerPanel.Close(self, *args)
