#Embedded file name: eve/client/script/ui/inflight\overViewLabel.py
import blue
from eve.client.script.ui.control.eveWindowUnderlay import LineUnderlay, FillUnderlay
import uthread
import telemetry
import uicontrols
import uiprimitives
import carbonui.const as uiconst
from eve.client.script.ui.inflight.overviewConst import *
import trinity

class OverviewLabel(uiprimitives.VisibleBase):
    __guid__ = 'uicls.OverviewLabel'
    __renderObject__ = trinity.Tr2Sprite2dTextObject
    default_name = 'OverviewLabel'
    default_color = None
    _text = None
    _columnWidth = None
    _columnPosition = 0
    _globalMaxWidth = None
    _columnWidthDirty = False

    def ApplyAttributes(self, attributes):
        uiprimitives.VisibleBase.ApplyAttributes(self, attributes)
        self.fadeSize = self.ScaleDpi(COLUMNFADESIZE)
        self.rightAligned = False
        measurer = trinity.Tr2FontMeasurer()
        measurer.limit = 0
        measurer.fontSize = uicore.ScaleDpi(uicore.fontSizeFactor * attributes.fontSize)
        measurer.font = str(uicore.font.GetFontDefault())
        measurer.letterSpace = 0
        self.renderObject.fontMeasurer = measurer
        self.renderObject.shadowOffset = (0, 1)
        self.measurer = measurer

    def UpdateFade(self):
        measurer = self.measurer
        columnWidth = self.columnWidth
        if columnWidth:
            globalFade = False
            globalMaxWidth = self.globalMaxWidth
            if globalMaxWidth and globalMaxWidth - self.left < columnWidth:
                scaledMaxWidth = max(0, self.ScaleDpi(globalMaxWidth - self.left))
                globalFade = True
            elif self.rightAligned:
                scaledMaxWidth = measurer.cursorX
            else:
                scaledMaxWidth = self.ScaleDpi(columnWidth)
            if measurer.cursorX > scaledMaxWidth:
                maxFade = max(2, measurer.cursorX - scaledMaxWidth)
                if globalFade:
                    measurer.fadeRightStart = max(0, scaledMaxWidth - min(maxFade, self.fadeSize))
                    measurer.fadeRightEnd = scaledMaxWidth
                else:
                    measurer.fadeRightStart = measurer.cursorX + 1
                    measurer.fadeRightEnd = measurer.cursorX + 1
            else:
                measurer.fadeRightStart = measurer.cursorX + 1
                measurer.fadeRightEnd = measurer.cursorX + 1

    @apply
    def left():

        def fget(self):
            return self._left

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._left:
                self._left = adjustedValue
                self.FlagAlignmentDirty()
                self.UpdateFade()

        return property(**locals())

    @apply
    def width():

        def fget(self):
            return self._width

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._width:
                self._width = adjustedValue
                if self.rightAligned:
                    self.left = self.columnPosition + self.columnWidth - adjustedValue
                self.FlagAlignmentDirty()
                self.UpdateFade()

        return property(**locals())

    @apply
    def text():

        def fget(self):
            return self._text

        def fset(self, value):
            if self._text != value or self._columnWidthDirty:
                self._columnWidthDirty = False
                self._text = value
                if not value:
                    self.texture = None
                    self.spriteEffect = trinity.TR2_SFX_NONE
                    return
                measurer = self.measurer
                measurer.Reset()
                measurer.color = -1073741825
                if self.columnWidth:
                    measurer.limit = self.ScaleDpi(self.columnWidth)
                added = measurer.AddText(unicode(value))
                measurer.CommitText(0, measurer.ascender)
                if self.columnWidth:
                    self.width = min(self.columnWidth, self.ReverseScaleDpi(measurer.cursorX + 0.5))
                    self.renderObject.textWidth = min(self.ScaleDpi(self.columnWidth), measurer.cursorX)
                else:
                    self.width = self.ReverseScaleDpi(measurer.cursorX + 0.5)
                    self.renderObject.textWidth = measurer.cursorX
                self.height = self.ReverseScaleDpi(measurer.ascender - measurer.descender)
                self.renderObject.textHeight = measurer.ascender - measurer.descender

        return property(**locals())

    @apply
    def columnWidth():

        def fget(self):
            return self._columnWidth

        def fset(self, value):
            if self._columnWidth != value:
                self._columnWidth = value
                self._columnWidthDirty = True
                measurer = self.measurer
                self.width = min(value, self.ReverseScaleDpi(measurer.cursorX + 0.5))
                self.renderObject.textWidth = min(self.ScaleDpi(value), measurer.cursorX)
                if self.rightAligned:
                    self.left = self.columnPosition + value - self.width

        return property(**locals())

    @apply
    def columnPosition():

        def fget(self):
            return self._columnPosition

        def fset(self, value):
            if self._columnPosition != value:
                self._columnPosition = value
                if self.rightAligned:
                    self.left = value + self.columnWidth - self.width
                else:
                    self.left = value

        return property(**locals())

    @apply
    def globalMaxWidth():

        def fget(self):
            return self._globalMaxWidth

        def fset(self, value):
            if self._globalMaxWidth != value:
                self._globalMaxWidth = value
                self.UpdateFade()

        return property(**locals())

    @classmethod
    def MeasureTextSize(cls, text, **customAttributes):
        """ Util function to get the size of the label before its rendered"""
        customAttributes['parent'] = None
        customAttributes['align'] = uiconst.TOPLEFT
        label = cls(**customAttributes)
        label.text = text
        return (label.width, label.height)

    def GetMenu(self):
        parent = self.parent
        if parent and hasattr(parent, 'GetMenu'):
            return parent.GetMenu()

    def OnMouseEnter(self, *args, **kwds):
        parent = self.parent
        if parent and parent.OnMouseEnter.im_func != uiprimitives.Base.OnMouseEnter.im_func:
            return parent.OnMouseEnter(*args, **kwds)

    def OnMouseExit(self, *args, **kwds):
        parent = self.parent
        if parent and parent.OnMouseExit.im_func != uiprimitives.Base.OnMouseExit.im_func:
            return parent.OnMouseExit(*args, **kwds)

    def OnMouseDown(self, *args, **kwds):
        parent = self.parent
        if parent and parent.OnMouseDown.im_func != uiprimitives.Base.OnMouseDown.im_func:
            return parent.OnMouseDown(*args, **kwds)

    def OnMouseUp(self, *args, **kwds):
        parent = self.parent
        if parent and parent.OnMouseUp.im_func != uiprimitives.Base.OnMouseUp.im_func:
            return parent.OnMouseUp(*args, **kwds)

    def OnClick(self, *args, **kwds):
        parent = self.parent
        if parent and parent.OnClick.im_func != uiprimitives.Base.OnClick.im_func:
            return parent.OnClick(*args, **kwds)

    def OnDblClick(self, *args, **kwds):
        parent = self.parent
        if parent and hasattr(parent, 'OnDblClick'):
            return parent.OnDblClick(*args, **kwds)


class SortHeaders(uiprimitives.Container):
    __guid__ = 'uicls.SortHeaders'
    default_name = 'SortHeaders'
    default_align = uiconst.TOTOP
    default_height = 16
    default_state = uiconst.UI_PICKCHILDREN
    default_clipChildren = True
    default_padBottom = 0

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        LineUnderlay(parent=self, align=uiconst.TOBOTTOM, opacity=uiconst.OPACITY_FRAME)
        self.headerContainer = uiprimitives.Container(parent=self)
        self.settingsID = attributes.settingsID
        self.customSortIcon = None
        self.columnIDs = []
        self.fixedColumns = None
        self.defaultColumn = None

    def SetDefaultColumn(self, columnID, direction):
        self.defaultColumn = (columnID, direction)

    def CreateColumns(self, columns, fixedColumns = None):
        self.headerContainer.Flush()
        self.columnIDs = columns
        self.fixedColumns = fixedColumns
        if columns:
            sizes = self.GetCurrentSizes()
            for columnID in columns:
                header = uiprimitives.Container(parent=self.headerContainer, align=uiconst.TOLEFT, state=uiconst.UI_NORMAL)
                header.OnClick = (self.ClickHeader, header)
                header.OnDblClick = (self.DblClickHeader, header)
                header.columnID = columnID
                header.sortTriangle = None
                headerDivider = LineUnderlay(parent=header, align=uiconst.TORIGHT, opacity=uiconst.OPACITY_FRAME)
                if columnID not in fixedColumns:
                    scaler = uiprimitives.Container(parent=header, align=uiconst.TOPRIGHT, width=4, height=self.height - 1, state=uiconst.UI_NORMAL)
                    scaler.OnMouseDown = (self.StartHeaderScale, header)
                    scaler.OnMouseEnter = (self.OnHeaderMouseEnter, header)
                    scaler.OnMouseExit = (self.OnHeaderMouseExit, header)
                    header.OnMouseEnter = (self.OnHeaderMouseEnter, header)
                    header.OnMouseExit = (self.OnHeaderMouseExit, header)
                    scaler.cursor = 16
                label = uicontrols.EveLabelSmall(parent=header, text=sm.GetService('tactical').GetColumnLabel(columnID, addFormatUnit=True), align=uiconst.CENTERLEFT, left=6, state=uiconst.UI_DISABLED, maxLines=1)
                header.label = label
                if fixedColumns and columnID in fixedColumns:
                    header.width = fixedColumns[columnID]
                    if header.width <= 32:
                        label.Hide()
                elif columnID in sizes:
                    header.width = max(COLUMNMINSIZE, sizes[columnID])
                else:
                    header.width = max(COLUMNMINSIZE, max(COLUMNMINDEFAULTSIZE, label.textwidth + 24))
                header.fill = FillUnderlay(parent=header, colorType=uiconst.COLORTYPE_UIHILIGHT, padLeft=-1, padRight=-1, opacity=0.75)

            self.UpdateActiveState()

    def SetSortIcon(self, texturePath):
        if self.customSortIcon != texturePath:
            self.customSortIcon = texturePath
            self.UpdateActiveState()

    def UpdateActiveState(self):
        currentActive, currentDirection = self.GetCurrentActive()
        for each in self.headerContainer.children:
            if hasattr(each, 'columnID'):
                if each.columnID == currentActive:
                    if not each.sortTriangle:
                        each.sortTriangle = uicontrols.Icon(align=uiconst.CENTERRIGHT, pos=(3, -1, 16, 16), parent=each, name='directionIcon', idx=0)
                    if self.customSortIcon:
                        each.sortTriangle.LoadTexture(self.customSortIcon)
                    elif currentDirection:
                        each.sortTriangle.LoadIcon('ui_1_16_16')
                    else:
                        each.sortTriangle.LoadIcon('ui_1_16_15')
                    each.sortTriangle.state = uiconst.UI_DISABLED
                    each.fill.Show()
                    rightMargin = 20
                else:
                    each.fill.Hide()
                    if each.sortTriangle:
                        each.sortTriangle.Hide()
                    rightMargin = 6
                each.label.width = each.width - each.label.left - 4
                if each.sortTriangle and each.sortTriangle.display:
                    each.label.SetRightAlphaFade(each.width - rightMargin - each.label.left, uiconst.SCROLL_COLUMN_FADEWIDTH)
                else:
                    each.label.SetRightAlphaFade()
                if each.width <= 32 or each.width - each.label.left - rightMargin - 6 < each.label.textwidth:
                    each.hint = each.label.text
                else:
                    each.hint = None

    def GetCurrentColumns(self):
        return self.columnIDs

    @telemetry.ZONE_METHOD
    def GetCurrentActive(self):
        all = settings.char.ui.Get('SortHeadersSettings', {})
        currentActive, currentDirection = None, True
        if self.settingsID in all:
            currentActive, currentDirection = all[self.settingsID]
            if currentActive not in self.columnIDs:
                if self.columnIDs:
                    currentActive, currentDirection = self.columnIDs[0], True
                return (None, True)
            return (currentActive, currentDirection)
        if self.defaultColumn is not None:
            columnID, direction = self.defaultColumn
            if columnID in self.columnIDs:
                return self.defaultColumn
        if self.columnIDs:
            currentActive, currentDirection = self.columnIDs[0], True
        return (currentActive, currentDirection)

    def SetCurrentActive(self, columnID, doCallback = True):
        currentActive, currentDirection = self.GetCurrentActive()
        if currentActive == columnID:
            sortDirection = not currentDirection
        else:
            sortDirection = currentDirection
        all = settings.char.ui.Get('SortHeadersSettings', {})
        all[self.settingsID] = (columnID, sortDirection)
        settings.char.ui.Set('SortHeadersSettings', all)
        self.UpdateActiveState()
        if doCallback:
            self.OnSortingChange(currentActive, columnID, currentDirection, sortDirection)

    def DblClickHeader(self, header):
        if not self.ColumnIsFixed(header.columnID):
            self.SetCurrentActive(header.columnID, doCallback=False)
            self.OnColumnSizeReset(header.columnID)

    def ClickHeader(self, header):
        self.SetCurrentActive(header.columnID)

    def StartHeaderScale(self, header, mouseButton, *args):
        if mouseButton == uiconst.MOUSELEFT:
            self.startScaleX = uicore.uilib.x
            self.startScaleWidth = header.width
            uthread.new(self.ScaleHeader, header)

    def OnHeaderMouseEnter(self, header):
        pass

    def OnHeaderMouseExit(self, header):
        pass

    def ScaleHeader(self, header):
        while not self.destroyed and uicore.uilib.leftbtn:
            diff = self.startScaleX - uicore.uilib.x
            header.width = max(COLUMNMINSIZE, self.startScaleWidth - diff)
            self.UpdateActiveState()
            blue.pyos.synchro.Yield()

        currentSizes = self.RegisterCurrentSizes()
        self.UpdateActiveState()
        self.OnColumnSizeChange(header.columnID, header.width, currentSizes)

    def GetCurrentSizes(self):
        current = settings.char.ui.Get('SortHeadersSizes', {}).get(self.settingsID, {})
        if self.fixedColumns:
            current.update(self.fixedColumns)
        for each in self.headerContainer.children:
            if hasattr(each, 'columnID') and each.columnID not in current:
                current[each.columnID] = each.width

        return current

    def ColumnIsFixed(self, columnID):
        return columnID in self.fixedColumns

    def SetColumnSize(self, columnID, size):
        if columnID in self.fixedColumns:
            return
        for each in self.headerContainer.children:
            if hasattr(each, 'columnID') and each.columnID == columnID:
                each.width = max(COLUMNMINSIZE, size)
                break

        self.UpdateActiveState()
        currentSizes = self.RegisterCurrentSizes()
        self.OnColumnSizeChange(columnID, max(COLUMNMINSIZE, size), currentSizes)

    def RegisterCurrentSizes(self):
        sizes = {}
        for each in self.headerContainer.children:
            if hasattr(each, 'columnID'):
                sizes[each.columnID] = each.width

        all = settings.char.ui.Get('SortHeadersSizes', {})
        all[self.settingsID] = sizes
        settings.char.ui.Set('SortHeadersSizes', all)
        return sizes

    def OnSortingChange(self, oldColumnID, columnID, oldSortDirection, sortDirection):
        pass

    def OnColumnSizeChange(self, columnID, newSize, currentSizes):
        pass

    def OnColumnSizeReset(self, columnID):
        pass
