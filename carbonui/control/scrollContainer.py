#Embedded file name: carbonui/control\scrollContainer.py
import carbonui.const as uiconst
from eve.client.script.ui.control.eveWindowUnderlay import BumpedUnderlay, RaisedUnderlay
from eve.client.script.ui.control.themeColored import FillThemeColored
import uthread
import blue
import math
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.control.label import LabelOverride as Label
from carbonui.primitives.container import Container

class ScrollContainer(Container):
    """ 
        A container with vertical and horizontal scrolling functionality. Children must
        all use the same alignment mode, which must be either TOPLEFT, TOLEFT or TOTOP.
        
        Note that all children appended to this container will actually end up in 
        self.mainCont, which is necessary for scrolling to work without the need for
        users to know about the existance of self.mainCont.
    """
    __guid__ = 'uicls.ScrollContainer'
    default_name = 'scrollContainer'
    default_state = uiconst.UI_NORMAL
    dragHoverScrollAreaSize = 30
    dragHoverScrollSpeed = 60.0
    default_showUnderlay = False
    isTabStop = True
    pushContent = True

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        pushContent = attributes.pushContent or self.pushContent
        showUnderlay = attributes.Get('showUnderlay', self.default_showUnderlay)
        self.scrollbarsDisabled = False
        self.scrollToVerticalPending = None
        self.scrollToHorizontalPending = None
        self.noContentHint = None
        self.verticalScrollBar = ScrollBar(parent=self, align=uiconst.TORIGHT if pushContent else uiconst.TORIGHT_NOPUSH)
        self.verticalScrollBar.OnScrolled = self._OnVerticalScrollBar
        self.horizontalScrollBar = ScrollBar(parent=self, align=uiconst.TOBOTTOM if pushContent else uiconst.TOBOTTOM_NOPUSH)
        self.horizontalScrollBar.OnScrolled = self._OnHorizontalScrollBar
        self.clipCont = Container(name='clipCont', parent=self, clipChildren=True)
        self.mainCont = ContainerAutoSize(name='mainCont', parent=self.clipCont, state=uiconst.UI_NORMAL)
        self.mainCont._OnSizeChange_NoBlock = self._OnMainContSizeChange
        self.children.insert = self._InsertChild
        self.children.append = self._AppendChild
        self.children.remove = self._RemoveChild
        self._mouseHoverCookie = uicore.uilib.RegisterForTriuiEvents(uiconst.UI_MOUSEHOVER, self.OnGlobalMouseHover)
        if showUnderlay:
            self.underlay = BumpedUnderlay(bgParent=self)
        else:
            self.underlay = None

    def Close(self, *args):
        uicore.uilib.UnregisterForTriuiEvents(self._mouseHoverCookie)
        Container.Close(self, *args)

    def _InsertChild(self, idx, obj):
        self.mainCont.children.insert(idx, obj)
        self.mainCont.align = obj.align

    def _AppendChild(self, obj):
        self.mainCont.children.append(obj)
        self.mainCont.align = obj.align

    def _RemoveChild(self, obj):
        self.mainCont.children.remove(obj)

    def OnGlobalMouseHover(self, obj, *args):
        """ Scroll when drag-hovering over top or bottom parts of scroll """
        if uicore.IsDragging() and (obj == self or obj.IsUnder(self.mainCont)):
            l, t, w, h = self.GetAbsolute()
            if self.verticalScrollBar.display and h > 0:
                fraction = self.dragHoverScrollSpeed / float(h)
                y = uicore.uilib.y - t
                if y <= self.dragHoverScrollAreaSize:
                    self.ScrollMoveVertical(-fraction)
                    self.verticalScrollBar.AnimFade()
                elif y > h - self.dragHoverScrollAreaSize:
                    self.ScrollMoveVertical(fraction)
                    self.verticalScrollBar.AnimFade()
            if self.horizontalScrollBar.display and w > 0:
                fraction = self.dragHoverScrollSpeed / float(w)
                x = uicore.uilib.x - l
                if x <= self.dragHoverScrollAreaSize:
                    self.ScrollMoveHorizontal(-fraction)
                    self.horizontalScrollBar.AnimFade()
                elif x > w - self.dragHoverScrollAreaSize:
                    self.ScrollMoveHorizontal(fraction)
                    self.horizontalScrollBar.AnimFade()
        return True

    def _OnSizeChange_NoBlock(self, width, height):
        self._UpdateHandleSizesAndPosition(width, height, updatePos=False)

    def _OnMainContSizeChange(self, width, height):
        self._UpdateScrollbars()

    def Flush(self):
        self.mainCont.Flush()

    def DisableScrollbars(self):
        self.scrollbarsDisabled = True
        self._UpdateScrollbars()

    def EnableScrollbars(self):
        self.scrollbarsDisabled = False
        self._UpdateScrollbars()

    def _UpdateScrollbars(self):
        w, h = self.GetAbsoluteSize()
        self._UpdateHandleSizesAndPosition(w, h)

    def _UpdateHandleSizesAndPosition(self, width, height, updatePos = True):
        if self.mainCont.height > 0 and not self.scrollbarsDisabled:
            size = float(height) / self.mainCont.height
        else:
            size = 1.0
        self.verticalScrollBar.SetScrollHandleSize(size)
        if updatePos:
            denum = self.mainCont.height - height
            if denum <= 0.0:
                pos = 0.0
            else:
                pos = float(-self.mainCont.top) / denum
            self.verticalScrollBar.ScrollTo(pos)
        else:
            pos = self.verticalScrollBar.handlePos
        self._OnVerticalScrollBar(pos)
        if self.mainCont.width != 0 and not self.scrollbarsDisabled:
            size = float(width) / self.mainCont.width
        else:
            size = 1.0
        self.horizontalScrollBar.SetScrollHandleSize(size)
        if updatePos:
            denum = self.mainCont.width - width
            if denum <= 0.0:
                pos = 0.0
            else:
                pos = float(-self.mainCont.left) / denum
            self.horizontalScrollBar.ScrollTo(pos)
        else:
            pos = self.horizontalScrollBar.handlePos
        self._OnHorizontalScrollBar(pos)
        if self.horizontalScrollBar.display and self.verticalScrollBar.display:
            self.verticalScrollBar.padBottom = self.horizontalScrollBar.height
        else:
            self.verticalScrollBar.padBottom = 0

    def _OnVerticalScrollBar(self, posFraction):
        w, h = self.clipCont.GetAbsoluteSize()
        posFraction = max(0.0, min(posFraction, 1.0))
        self.mainCont.top = -posFraction * (self.mainCont.height - h)
        self.OnScrolledVertical(posFraction)

    def _OnHorizontalScrollBar(self, posFraction):
        w, h = self.clipCont.GetAbsoluteSize()
        posFraction = max(0.0, min(posFraction, 1.0))
        self.mainCont.left = -posFraction * (self.mainCont.width - w)
        self.OnScrolledHorizontal(posFraction)

    def OnScrolledHorizontal(self, posFraction):
        """ Overwriteable"""
        pass

    def OnScrolledVertical(self, posFraction):
        """ Overwriteable"""
        pass

    def ScrollToVertical(self, posFraction):
        """ Call this method to scroll the vertical scrollbar to a given position [0.0 - 1.0] """
        if self._alignmentDirty:
            self.scrollToVerticalPending = posFraction
        elif self.verticalScrollBar.display:
            self.verticalScrollBar.ScrollTo(posFraction)
            self._OnVerticalScrollBar(self.verticalScrollBar.handlePos)

    def ScrollToHorizontal(self, posFraction):
        """ Call this method to scroll the horizontal scrollbar to a given position [0.0 - 1.0] """
        if self._alignmentDirty:
            self.scrollToHorizontalPending = posFraction
        elif self.horizontalScrollBar.display:
            self.horizontalScrollBar.ScrollTo(posFraction)
            self._OnHorizontalScrollBar(self.horizontalScrollBar.handlePos)

    def GetPositionVertical(self):
        return self.verticalScrollBar.handlePos

    def GetPositionHorizontal(self):
        return self.horizontalScrollBar.handlePos

    def UpdateAlignment(self, *args, **kwds):
        ret = Container.UpdateAlignment(self, *args, **kwds)
        if self.scrollToVerticalPending:
            self.verticalScrollBar.ScrollTo(self.scrollToVerticalPending)
            self._OnVerticalScrollBar(self.verticalScrollBar.handlePos)
        self.scrollToVerticalPending = None
        if self.scrollToHorizontalPending:
            self.horizontalScrollBar.ScrollTo(self.scrollToHorizontalPending)
            self._OnHorizontalScrollBar(self.horizontalScrollBar.handlePos)
        self.scrollToHorizontalPending = None
        return ret

    def ScrollMoveVertical(self, moveFraction):
        """ Move the vertical scrollbar by an arbitrary negative or positive float value """
        self.verticalScrollBar.ScrollMove(moveFraction)
        self._OnVerticalScrollBar(self.verticalScrollBar.handlePos)

    def ScrollMoveHorizontal(self, moveFraction):
        """ Move the horizontal scrollbar by a given arbitrary negative or positive float value """
        self.horizontalScrollBar.ScrollMove(moveFraction)
        self._OnHorizontalScrollBar(self.horizontalScrollBar.handlePos)

    def OnMouseWheel(self, dz):
        if self.verticalScrollBar.display:
            prop = -dz / float(self.mainCont.height)
            if math.fabs(prop) < 0.1:
                prop = math.copysign(0.1, prop)
            self.ScrollMoveVertical(prop)
            self.verticalScrollBar.AnimFade()
        elif self.horizontalScrollBar.display:
            prop = -dz / float(self.mainCont.width)
            if math.fabs(prop) < 0.1:
                prop = math.copysign(0.1, prop)
            self.ScrollMoveHorizontal(prop)
            self.horizontalScrollBar.AnimFade()

    def OnKeyDown(self, key, flag):
        if key == uiconst.VK_PRIOR:
            self.ScrollByPage(up=True)
        elif key == uiconst.VK_NEXT:
            self.ScrollByPage(up=False)

    def ScrollByPage(self, up = True):
        if not self.verticalScrollBar.display:
            return
        w, h = self.clipCont.GetAbsoluteSize()
        if up:
            mainContTopNewTop = self.mainCont.top + h
            mainContTopNewTop = min(0, mainContTopNewTop)
        else:
            mainContTopNewTop = self.mainCont.top - h
            mainContTopNewTop = max(h - self.mainCont.height, mainContTopNewTop)
        self.mainCont.top = mainContTopNewTop
        self._UpdateScrollbars()
        self.verticalScrollBar.AnimFade()

    def ShowNoContentHint(self, text):
        """ Show a hint that explains why the scroll container is empty """
        self.noContentHint = Label(parent=self, align=uiconst.TOTOP, padding=(16, 32, 16, 0), text=text, fontsize=20, uppercase=True, letterspace=1)

    def HideNoContentHint(self):
        if self.noContentHint:
            self.noContentHint.Close()
            self.noContentHint = None

    def OnSetFocus(self, *args):
        if self.underlay:
            self.underlay.AnimEntry()

    def OnKillFocus(self, *args):
        if self.underlay:
            self.underlay.AnimExit()


class ScrollBar(Container):
    """ 
        A scrollbar class that can be hooked up to other control through the OnScrolled
        method. The scrollbar automatically adjusts it's layout to it's alignment, which 
        must be one of TOLEFT, TORIGHT, TOTOP or TOBOTTOM.
    """
    __guid__ = 'uicls.ScrollBar'
    default_name = 'scrollBar'
    default_align = uiconst.TORIGHT
    default_state = uiconst.UI_HIDDEN
    default_width = 7
    default_height = 6
    VERTICAL = 1
    HORIZONTAL = 2
    default_scrollSpeed = 0.05

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.scrollSpeed = attributes.get('scrollSpeed', self.default_scrollSpeed)
        self.handleSize = 0.5
        self.handlePos = 0.0
        self.mouseDownThread = None
        self.animFadeThread = None
        self.isDragging = False
        self.PrepareUnderlay_()
        if self.align in (uiconst.TORIGHT,
         uiconst.TOLEFT,
         uiconst.TORIGHT_NOPUSH,
         uiconst.TOLEFT_NOPUSH):
            self.PrepareVertical_()
            self.orientation = self.VERTICAL
        elif self.align in (uiconst.TOTOP,
         uiconst.TOBOTTOM,
         uiconst.TOTOP_NOPUSH,
         uiconst.TOBOTTOM_NOPUSH):
            self.PrepareHorizontal_()
            self.orientation = self.HORIZONTAL
        else:
            raise ValueError('Scrollbars must have TOBOTTOM, TOTOP, TOLEFT, TORIGHT or equivalent _NOPUSH alignments.')
        self.scrollHandle.OnMouseDown = self._OnScrollHandleMouseDown
        self.scrollHandle.OnMouseUp = self._OnScrollHandleMouseUp

    def PrepareUnderlay_(self):
        """ Overwritten by game specific layout """
        self.underlay = FillThemeColored(name='underlay', bgParent=self)

    def PrepareVertical_(self):
        """ Overwritten by game specific layout """
        self.handleCont = Container(name='handleCont', parent=self, align=uiconst.TOALL)
        self.scrollHandle = ScrollHandle(name='scrollhandle', parent=self.handleCont, align=uiconst.TOTOP_PROP, state=uiconst.UI_NORMAL, height=self.handleSize)

    def PrepareHorizontal_(self):
        """ Overwritten by game specific layout """
        self.handleCont = Container(name='handleCont', parent=self, align=uiconst.TOALL)
        self.scrollHandle = ScrollHandle(name='scrollhandle', parent=self.handleCont, align=uiconst.TOLEFT_PROP, state=uiconst.UI_NORMAL, width=self.handleSize)

    def _OnScrollHandleMouseDown(self, *args):
        self.isDragging = True
        ScrollHandle.OnMouseDown(self.scrollHandle, *args)
        uthread.new(self._DragScrollHandleThread)

    def _OnScrollHandleMouseUp(self, *args):
        self.isDragging = False
        ScrollHandle.OnMouseUp(self.scrollHandle, *args)

    def _DragScrollHandleThread(self):
        left, top = self.handleCont.GetAbsolutePosition()
        handleLeft, handleTop = self.scrollHandle.GetAbsolutePosition()
        maxLeft, maxTop = self._GetHandleMaxPos()
        if self.orientation == self.HORIZONTAL:
            xOffset = uicore.uilib.x - handleLeft
            while uicore.uilib.leftbtn:
                x = uicore.uilib.x - left - xOffset
                self.ScrollTo(float(x) / maxLeft)
                self.OnScrolled(self.handlePos)
                blue.synchro.Yield()

        else:
            yOffset = uicore.uilib.y - handleTop
            while uicore.uilib.leftbtn:
                y = uicore.uilib.y - top - yOffset
                self.ScrollTo(float(y) / maxTop)
                self.OnScrolled(self.handlePos)
                blue.synchro.Yield()

    def OnMouseDown(self, *args):
        """ Empty space behind scrollHandle clicked, scroll to that position """
        left, top, width, height = self.handleCont.GetAbsolute()
        if self.orientation == self.VERTICAL:
            posFraction = (uicore.uilib.y - top) / float(height)
            self.ScrollTo(posFraction)
            self.OnScrolled(posFraction)
        else:
            posFraction = (uicore.uilib.x - left) / float(width)
            self.ScrollTo(posFraction)
            self.OnScrolled(posFraction)

    def SetScrollHandleSize(self, sizeFraction):
        """ Set the size of the scroll handle """
        sizeFraction = max(0.0, min(sizeFraction, 1.0))
        self.display = sizeFraction != 1.0
        if self.orientation == self.HORIZONTAL:
            self.scrollHandle.width = max(0.05, sizeFraction)
        else:
            self.scrollHandle.height = max(0.05, sizeFraction)
        self.handleSize = sizeFraction
        self.ScrollTo(self.handlePos)

    def _GetHandleMaxPos(self):
        """ Returns maxLeft and maxTop values for self.scrollHandle """
        width, height = self.handleCont.GetAbsoluteSize()
        handleWidth, handleHeight = self.scrollHandle.GetAbsoluteSize()
        maxLeft = width - handleWidth
        maxTop = height - handleHeight
        return (maxLeft, maxTop)

    def ScrollTo(self, posFraction):
        """ Set the position of the scroll handle as defined by posFraction [0.0 - 1.0] """
        posFraction = max(0.0, min(posFraction, 1.0))
        maxLeft, maxTop = self._GetHandleMaxPos()
        if self.orientation == self.HORIZONTAL:
            self.scrollHandle.left = posFraction * maxLeft
        else:
            self.scrollHandle.top = posFraction * maxTop
        self.handlePos = posFraction

    def ScrollMove(self, moveFraction):
        """ Move the scroll handle by amount defined by moveFraction """
        self.ScrollTo(self.handlePos + moveFraction * self.handleSize)

    def OnScrolled(self, posFraction):
        """ Overwriteable """
        pass

    def AnimFade(self):
        self.fadeEndTime = blue.os.GetTime() + 0.3 * const.SEC
        if not self.animFadeThread:
            self.scrollHandle.AnimEntry(duration=0.1)
            uthread.new(self._AnimFadeThread)

    def _AnimFadeThread(self):
        while blue.os.GetTime() < self.fadeEndTime:
            blue.synchro.Yield()

        if uicore.uilib.mouseOver != self.scrollHandle:
            self.scrollHandle.AnimExit(duration=0.5)
        self.animFadeThread = None


class ScrollHandle(Container):
    """
    The handle bar dragged around to control a scroll
    """
    __guid__ = 'uicls._ScrollHandle'
    default_name = 'scrollHandle'
    default_width = 50
    default_height = 50
    OPACITY_INACTIVE = 0.6
    OPACITY_ACTIVE = 1.0

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.sr.hilite = None
        self._dragging = False
        self.Prepare_()

    def Prepare_(self):
        self.hilite = RaisedUnderlay(bgParent=self, opacity=self.OPACITY_INACTIVE, hideFrame=True)

    def OnMouseDown(self, btn, *args):
        self.hilite.OnMouseDown()

    def OnMouseMove(self, *etc):
        pass

    def OnMouseUp(self, btn, *args):
        self.hilite.OnMouseUp()

    def AnimEntry(self, duration = 0.15):
        self.hilite.OnMouseEnter()
        uicore.animations.FadeTo(self.hilite, self.hilite.opacity, self.OPACITY_ACTIVE, duration=duration)

    def OnMouseEnter(self, *args):
        self.AnimEntry()

    def AnimExit(self, duration = 0.5):
        self.hilite.OnMouseExit()
        uicore.animations.FadeTo(self.hilite, self.hilite.opacity, self.OPACITY_INACTIVE, duration=duration)

    def OnMouseExit(self, *args):
        self.AnimExit()
