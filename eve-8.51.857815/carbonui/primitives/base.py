#Embedded file name: carbonui/primitives\base.py
import carbonui.const as uiconst
import types
import log
import trinity
import telemetry
import blue
from .dragdrop import DragDropObject
from ..util.bunch import Bunch
import carbonui.const
from carbonui.const import PUSHALIGNMENTS, AFFECTEDBYPUSHALIGNMENTS
DELEGATE_EVENTNAMES = ('OnMouseUp',
 'OnMouseDown',
 'OnMouseEnter',
 'OnMouseExit',
 'OnMouseHover',
 'OnMouseMove',
 'OnMouseWheel',
 'OnClick',
 'OnDblClick',
 'GetMenu',
 'OnMouseMoveDrag',
 'OnMouseDownDrag')

def ScaleDpi(value):
    """
    Applies dpi scaling to the given value.
    """
    return int(value * uicore.dpiScaling + 0.5)


def ScaleDpiF(value):
    """
    Applies dpi scaling to the given value with no rounding.
    """
    return value * uicore.dpiScaling


def ReverseScaleDpi(value):
    """
    Applies reverse dpi scaling to the given value.
    """
    if uicore.dpiScaling != 1.0:
        try:
            return int(value / uicore.dpiScaling + 0.5)
        except (ValueError, OverflowError):
            return 0

    else:
        return int(value)


class Base(DragDropObject):
    """
    The base class that all other UI objects inherit from. Deals with alignment, pick
    states, visibility and other basics.
    """
    __guid__ = 'uiprimitives.Base'
    __renderObject__ = None
    __members__ = ['name',
     'left',
     'top',
     'width',
     'height',
     'padLeft',
     'padTop',
     'padRight',
     'padBottom',
     'display',
     'align',
     'pickState',
     'parent',
     'renderObject']
    default_name = ''
    default_parent = None
    default_idx = -1
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_hint = None
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0
    default_padLeft = 0
    default_padTop = 0
    default_padRight = 0
    default_padBottom = 0
    default_cursor = None
    _left = 0
    _top = 0
    _width = 0
    _height = 0
    _align = None
    _display = True
    _sr = None
    _name = default_name
    _cursor = default_cursor
    _parentRef = None
    _alignmentDirty = False
    _displayDirty = False
    _displayX = 0
    _displayY = 0
    _displayWidth = 0
    _displayHeight = 0
    _padLeft = 0
    _padTop = 0
    _padRight = 0
    _padBottom = 0
    _pickState = uiconst.TR2_SPS_ON
    _hint = None
    _tooltipPanelClassInfo = None
    _delegatingEvents = False
    _constructingBase = True
    destroyed = False
    renderObject = None
    auxiliaryHint = None
    isPushAligned = False
    isAffectedByPushAlignment = False
    isTransformed = False
    isAnimated = False

    @telemetry.ZONE_METHOD
    def __init__(self, **kw):
        if self.__renderObject__:
            self.renderObject = RO = self.__renderObject__()
            uicore.uilib.RegisterObject(self, RO)
            RO.display = True
            RO.name = self.name
        attributesBunch = Bunch(**kw)
        self.ApplyAttributes(attributesBunch)

    def __repr__(self):
        if self.name:
            name = self.name.encode('utf8')
        else:
            name = 'None'
        return '%s object at %s, name=%s, destroyed=%s>' % (self.__guid__,
         hex(id(self)),
         name,
         self.destroyed)

    @telemetry.ZONE_METHOD
    def ApplyAttributes(self, attributes):
        self._cursor = attributes.get('cursor', self.default_cursor)
        self._hint = attributes.get('hint', self.default_hint)
        if 'name' in attributes:
            self.name = attributes.name
        self.SetAlign(attributes.get('align', self.default_align))
        pos = attributes.pos
        if pos is not None:
            self.pos = pos
        else:
            left = attributes.get('left', self.default_left)
            top = attributes.get('top', self.default_top)
            width = attributes.get('width', self.default_width)
            height = attributes.get('height', self.default_height)
            self.pos = (left,
             top,
             width,
             height)
        padding = attributes.padding
        if padding is not None:
            self.padding = padding
        else:
            padLeft = attributes.get('padLeft', self.default_padLeft)
            padTop = attributes.get('padTop', self.default_padTop)
            padRight = attributes.get('padRight', self.default_padRight)
            padBottom = attributes.get('padBottom', self.default_padBottom)
            self.padding = (padLeft,
             padTop,
             padRight,
             padBottom)
        self.SetState(attributes.get('state', self.default_state))
        if attributes.get('bgParent', None):
            idx = attributes.get('idx', self.default_idx)
            if idx is None:
                idx = -1
            attributes.bgParent.background.insert(idx, self)
        else:
            parent = attributes.get('parent', self.default_parent)
            if parent and not parent.destroyed:
                self.SetParent(parent, attributes.get('idx', self.default_idx))
        self._constructingBase = False
        self.FlagAlignmentDirty()

    def Close(self):
        if getattr(self, 'destroyed', False):
            return
        self.destroyed = True
        uicore.uilib.ReleaseObject(self)
        notifyevents = getattr(self, '__notifyevents__', None)
        if notifyevents:
            sm.UnregisterNotify(self)
        self._OnClose()
        parent = self.parent
        if parent and not parent._containerClosing:
            parent.children.remove(self)
            parent.background.remove(self)
        if self.isAnimated:
            self.StopAnimations()
        self.renderObject = None
        self._alignFunc = None
        if self._delegatingEvents:
            for eventName in DELEGATE_EVENTNAMES:
                setattr(self, eventName, None)

    def _GetLegacyDeadAttr(self):
        log.LogTraceback('UIObject.dead attribute is deprecated, use UIObject.destroyed')
        return self.destroyed

    dead = property(_GetLegacyDeadAttr)

    def _GetSR(self):
        if self._sr is None:
            self._sr = Bunch()
        return self._sr

    sr = property(_GetSR)

    def HasEventHandler(self, handlerName):
        """Returns True if this object is handling 'handlerName'
        type of input event. This ignores the uiprimitives.Base functions
        since its only for fallback purposes."""
        handlerArgs, handler = self.FindEventHandler(handlerName)
        if not handler:
            return False
        baseHandler = getattr(Base, handlerName, None)
        if baseHandler and getattr(handler, 'im_func', None) is baseHandler.im_func:
            return False
        return bool(handler)

    def FindEventHandler(self, handlerName):
        """ Returns optionalArguments, handler for handlerName if found"""
        handler = getattr(self, handlerName, None)
        if not handler:
            return (None, None)
        if type(handler) == types.TupleType:
            handlerArgs = handler[1:]
            handler = handler[0]
        else:
            handlerArgs = ()
        return (handlerArgs, handler)

    def StopAnimations(self):
        """
        Stop all animation curveSets associated with object
        """
        uicore.animations.StopAllAnimations(self)

    def HasAnimation(self, attrName):
        curveSet = uicore.animations.GetAnimationCurveSet(self, attrName)
        return curveSet is not None

    def ProcessEvent(self, eventID):
        uicore.uilib._TryExecuteHandler(eventID, self)

    def GetRenderObject(self):
        """
        Get trinity render object associated with this instance
        """
        return self.renderObject

    def SetParent(self, parent, idx = None):
        currentParent = self.parent
        if currentParent:
            currentParent.children.remove(self)
        if parent is not None:
            self.isTransformed = parent.isTransformed or self.isTransformed
            parent.children.insert(idx, self)

    def GetParent(self):
        if self._parentRef:
            return self._parentRef()

    parent = property(GetParent)

    def SetOrder(self, idx):
        """
        Set the order of this object amongst siblings (0: at top, -1: at bottom)
        """
        parent = self.parent
        if parent:
            currentIndex = parent.children.index(self)
            if currentIndex != idx:
                self.SetParent(parent, idx)

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
            if left < 1.0:
                adjustedLeft = left
            else:
                adjustedLeft = int(round(left))
            if top < 1.0:
                adjustedTop = top
            else:
                adjustedTop = int(round(top))
            if width < 1.0:
                adjustedWidth = width
            else:
                adjustedWidth = int(round(width))
            if height < 1.0:
                adjustedHeight = height
            else:
                adjustedHeight = int(round(height))
            if self._left != adjustedLeft or self._top != adjustedTop or self._width != adjustedWidth or self._height != adjustedHeight:
                self._left = adjustedLeft
                self._top = adjustedTop
                self._width = adjustedWidth
                self._height = adjustedHeight
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def left():
        doc = 'x-coordinate of UI element'

        def fget(self):
            return self._left

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._left:
                self._left = adjustedValue
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def top():
        doc = 'y-coordinate of UI element'

        def fget(self):
            return self._top

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._top:
                self._top = adjustedValue
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def width():
        doc = 'Width of UI element'

        def fget(self):
            return self._width

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._width:
                self._width = adjustedValue
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def height():
        doc = 'Height of UI element'

        def fget(self):
            return self._height

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._height:
                self._height = adjustedValue
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padding():
        doc = '\n        Padding as a tuple of four values (left, top, right, bottom).\n        It can also be assigned an integer value - all four items will\n        then receive the same value.\n        '

        def fget(self):
            return (self._padLeft,
             self._padTop,
             self._padRight,
             self._padBottom)

        def fset(self, value):
            if isinstance(value, (tuple, list)):
                padLeft, padTop, padRight, padBottom = value
            else:
                padLeft = padTop = padRight = padBottom = value
            if self._padLeft != padLeft or self._padTop != padTop or self._padRight != padRight or self._padBottom != padBottom:
                self._padLeft = padLeft
                self._padTop = padTop
                self._padRight = padRight
                self._padBottom = padBottom
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padLeft():
        doc = 'Left padding'

        def fget(self):
            return self._padLeft

        def fset(self, value):
            if value != self._padLeft:
                self._padLeft = value
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padRight():
        doc = 'Right padding'

        def fget(self):
            return self._padRight

        def fset(self, value):
            if value != self._padRight:
                self._padRight = value
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padTop():
        doc = 'Top padding'

        def fget(self):
            return self._padTop

        def fset(self, value):
            if value != self._padTop:
                self._padTop = value
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padBottom():
        doc = 'Bottom padding'

        def fget(self):
            return self._padBottom

        def fset(self, value):
            if value != self._padBottom:
                self._padBottom = value
                if not self._constructingBase:
                    self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def display():
        doc = 'Is UI element displayed?'

        def fget(self):
            return self._display

        def fset(self, value):
            if value != self._display:
                RO = self.renderObject
                if RO:
                    RO.display = value
                if value:
                    self._display = value
                self._alignmentDirty = False
                if not self._constructingBase:
                    self.FlagAlignmentDirty()
                self._display = value
                self._displayDirty = True

        return property(**locals())

    def SetAlign(self, align):
        """
        Sets alignment of this item in relation to its parent
        
        non-push alignments:
        -----------------------------------------------------------------------------------
        TOPLEFT      Relative from top/left
        TOPRIGHT     Relative from top/right, left attr moves the child from the right side of the parent
        BOTTOMLEFT   Relative from bottom/left, top attr moves the child from the bottom side of the parent
        BOTTOMRIGHT  Relative from bottom/right
        CENTERLEFT   Relative from left, centers the child vertically
        CENTERRIGHT  Relative from right, centers the child vertically
        CENTERTOP    Relative from top, centers the child horizontally
        CENTERBOTTOM Relative from bottom, centers the child horizontally
        CENTER       Centers the child inside the parent
        ABSOLUTE     Relative from 0,0 of the desktop
        
        push alignemnts:
        -----------------------------------------------------------------------------------
        TOLEFT       Item seeks to left and affects other items lower in parent hierarchy
        TOTOP        Item seeks to top and affects other items lower in parent hierarchy
        TOBOTTOM     Item seeks to bottom and affects other items lower in parent hierarchy
        TORIGHT      Item seeks to right and affects other items lower in parent hierarchy
        TOALL        Item fills empty space in the parent
        """
        if align == self._align:
            return
        if hasattr(self.renderObject, 'absoluteCoordinates'):
            if align == uiconst.ABSOLUTE:
                self.renderObject.absoluteCoordinates = True
            else:
                self.renderObject.absoluteCoordinates = False
        self._alignFunc, self.isPushAligned, self.isAffectedByPushAlignment = ALIGN_AND_CONSUME_FUNCTIONS[align]
        self._align = align
        if not self._constructingBase:
            self.FlagAlignmentDirty()

    def GetAlign(self):
        return self._align

    align = property(GetAlign, SetAlign)

    @apply
    def name():
        doc = 'Name of this UI element'

        def fget(self):
            return self._name or self.default_name or self.__class__.__name__

        def fset(self, value):
            self._name = value
            ro = self.renderObject
            if ro:
                ro.name = value

        return property(**locals())

    @apply
    def translation():
        doc = '\n            Translation is a tuple of (displayX,displayY). Prefer this over setting\n            x and y separately.\n            '

        def fget(self):
            return (self._displayX, self._displayY)

        def fset(self, value):
            self._displayX = value[0]
            self._displayY = value[1]
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY

        return property(**locals())

    @apply
    def displayRect():
        doc = '\n            displayRect is a tuple of (displayX,displayY,displayWidth,displayHeight).\n            Prefer this over setting x, y, width and height separately if all are\n            being set.\n            '

        def fget(self):
            return (self._displayX,
             self._displayY,
             self._displayWidth,
             self._displayHeight)

        def fset(self, value):
            displayX, displayY, displayWidth, displayHeight = value
            self._displayX = int(round(displayX))
            self._displayY = int(round(displayY))
            self._displayWidth = int(round(displayX + displayWidth)) - self._displayX
            self._displayHeight = int(round(displayY + displayHeight)) - self._displayY
            if self._displayWidth == 0 and round(displayWidth) > 0:
                self._displayWidth = 1
            if self._displayHeight == 0 and round(displayHeight) > 0:
                self._displayHeight = 1
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight

        return property(**locals())

    @apply
    def displayX():
        doc = 'x-coordinate of render object'

        def fget(self):
            return self._displayX

        def fset(self, value):
            self._displayX = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX

        return property(**locals())

    @apply
    def displayY():
        doc = 'y-coordinate of render object'

        def fget(self):
            return self._displayY

        def fset(self, value):
            self._displayY = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayY = self._displayY

        return property(**locals())

    @apply
    def displayWidth():
        doc = 'Width of render object'

        def fget(self):
            return self._displayWidth

        def fset(self, value):
            self._displayWidth = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayWidth = self._displayWidth

        return property(**locals())

    @apply
    def displayHeight():
        doc = 'Height of render object'

        def fget(self):
            return self._displayHeight

        def fset(self, value):
            self._displayHeight = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayHeight = self._displayHeight

        return property(**locals())

    @apply
    def pickState():
        doc = 'Pick state of render object'

        def fget(self):
            return self._pickState

        def fset(self, value):
            self._pickState = value
            ro = self.renderObject
            if ro:
                ro.pickState = value

        return property(**locals())

    def Disable(self, *args):
        """Disable picking"""
        self.pickState = uiconst.TR2_SPS_OFF

    def Enable(self, *args):
        """Enable picking"""
        self.pickState = uiconst.TR2_SPS_ON

    def SetFocus(self, *args):
        pass

    def SendMessage(self, *args, **kwds):
        pass

    def SetHint(self, hint):
        """Sets (MouseOver) hint on this object"""
        self.hint = hint

    def GetHint(self):
        """Returns current hint on this object"""
        return self.hint

    @apply
    def hint():
        doc = 'Tooltip hint of an ui object'

        def fget(self):
            return self._hint

        def fset(self, value):
            if value != self._hint:
                self._hint = value
                if self is uicore.uilib.mouseOver:
                    uicore.uilib.UpdateTooltip(instant=True)

        return property(**locals())

    @apply
    def tooltipPanelClassInfo():
        doc = 'Tooltip hint of an ui object'

        def fget(self):
            return self._tooltipPanelClassInfo

        def fset(self, value):
            if value != self._tooltipPanelClassInfo:
                self._tooltipPanelClassInfo = value
                if self is uicore.uilib.mouseOver:
                    uicore.uilib.RefreshTooltipForOwner(owner=self)

        return property(**locals())

    def SetDisplayRect(self, displayRect):
        """Sets displayRect of this object. This function is intented for
        objects which have alignment as NOALIGN and are therefor ignored by the
        alignment update. (Used by Bracket fe)"""
        align = self.GetAlign()
        if align != uiconst.NOALIGN:
            return
        self.displayRect = displayRect

    def SetPadding(self, *padding):
        log.LogTraceback('UIObject.SetPadding is deprecated, use UIObject.padding instead')
        try:
            self.padding = padding
        except:
            pass

    def SetPosition(self, left, top):
        """Set position of this item"""
        self.left = left
        self.top = top

    def GetPosition(self):
        """Returns set (local) left and top value of this item. Use *.GetAbsolutePosition() ==> (absLeft, absTop)
        if you have item which is in auto-alignment mode and need screen position of this item."""
        return (self.left, self.top)

    def IsClickable(self):
        """
        Returns True if wnd is clickable.
        Note: this does only check the state of items from wnd
        to desktop, does not check if another item is blocking it
        """
        if self.destroyed or not hasattr(self, 'state') or not hasattr(self, 'parent'):
            return False
        if self.state not in (uiconst.UI_NORMAL, uiconst.UI_PICKCHILDREN):
            return False
        dad = self.parent
        if dad is uicore.desktop:
            return True
        return dad.IsClickable()

    def IsUnder(self, ancestor_maybe, retfailed = False):
        """
        Returns True if ancestor_maybe is anchestor of child.
        Works recursively.
        """
        dad = self.parent
        if not dad:
            if retfailed:
                return self
            return False
        if dad is ancestor_maybe:
            return True
        return dad.IsUnder(ancestor_maybe, retfailed)

    def IsVisible(self):
        if self.destroyed or not hasattr(self, 'state') or not hasattr(self, 'parent'):
            return False
        if self.state == uiconst.UI_HIDDEN:
            return False
        dad = self.parent
        if not dad:
            return False
        if dad.state == uiconst.UI_HIDDEN:
            return False
        if dad is uicore.desktop:
            return True
        return dad.IsVisible()

    def IsClippedBy(self, clipper = None):
        """
        Returns true if clipped (and thus not visible) by the clipping object passed in
        
        This method should be used with care as GetAbsolute calls can introduce performance issues
        """
        if self.GetAbsoluteTop() > clipper.GetAbsoluteBottom():
            return True
        if self.GetAbsoluteBottom() < clipper.GetAbsoluteTop():
            return True
        if self.GetAbsoluteRight() < clipper.GetAbsoluteLeft():
            return True
        if self.GetAbsoluteLeft() > clipper.GetAbsoluteRight():
            return True
        return False

    def SetSize(self, width, height):
        """Set size of this item"""
        self.width = width
        self.height = height

    def GetSize(self):
        """Returns set width and height. Use *.GetAbsoluteSize() ==> (absWidth, absHeight)
        if you have item which is in auto-alignment mode"""
        return (self.width, self.height)

    def GetAbsoluteViewport(self, doPrint = False):
        """Returns absolute screen position and size of this item.
        
        Please do not use this method unless it's absolutely necessary since it adds
        considerable alignment overhead in many cases"""
        if not self.display:
            return (0, 0, 0, 0)
        w, h = self.GetAbsoluteSize()
        l, t = self.GetAbsolutePosition()
        return (l,
         t,
         w,
         h)

    def GetAbsolute(self, doPrint = False):
        """Returns absolute screen position and size of this item.
        
        Please do not use this method unless it's absolutely necessary since it adds
        considerable alignment overhead in many cases"""
        if not self.display:
            return (0, 0, 0, 0)
        w, h = self.GetAbsoluteSize()
        l, t = self.GetAbsolutePosition()
        return (l,
         t,
         w,
         h)

    @telemetry.ZONE_METHOD
    def GetAbsoluteSize(self):
        """Returns the displayWidth and displayHeight of the object. If said values are
        yet to be determined, we force an alignment update and return correct values
        
        Please do not use this method unless it's absolutely necessary since it adds
        considerable alignment overhead in many cases"""
        if self.destroyed or not self.display:
            return (0, 0)
        else:
            if self.isTransformed:
                scaleX, scaleY = self._GetAbsoluteScale()
            else:
                scaleX, scaleY = (1.0, 1.0)
            if self.isAffectedByPushAlignment:
                self._AssureAlignmentUpdated()
                return (ReverseScaleDpi(scaleX * self.displayWidth), ReverseScaleDpi(scaleY * self.displayHeight))
            return (int(scaleX * self.width), int(scaleY * self.height))

    def _GetAbsoluteScale(self):
        """ Returns absolute x and y scale values for this object, taking into accounts transforms above in the hierarchy """
        if hasattr(self, '_GetScale'):
            scaleX, scaleY = self._GetScale()
        else:
            scaleX, scaleY = (1.0, 1.0)
        parent = self.parent
        if parent:
            parScaleX, parScaleY = parent._GetAbsoluteScale()
            scaleX *= parScaleX
            scaleY *= parScaleY
        return (scaleX, scaleY)

    def _GetScale(self):
        """ Returns x and y scale values for this object """
        return (1.0, 1.0)

    def GetCurrentAbsoluteSize(self):
        """Returns the displayWidth and displayHeight of the object. No alignment
        is done, even if the object is flagged dirty."""
        if self.destroyed or not self.display:
            return (0, 0)
        elif self.isAffectedByPushAlignment:
            return (ReverseScaleDpi(self.displayWidth), ReverseScaleDpi(self.displayHeight))
        else:
            return (self.width, self.height)

    def _AssureAlignmentUpdated(self):
        if self._alignmentDirty or self._displayDirty:
            parent = self.parent
            if parent:
                prevParent = None
                while parent:
                    if not parent.isAffectedByPushAlignment and not parent._alignmentDirty:
                        break
                    if not parent._childrenAlignmentDirty and not parent._displayDirty:
                        break
                    if not parent.display:
                        break
                    prevParent = parent
                    parent = parent.parent

                parent = parent or prevParent
                if not parent.isAffectedByPushAlignment:
                    oldDisplayWidth = parent.displayWidth
                    oldDisplayHeight = parent.displayHeight
                    parent.displayWidth = ScaleDpiF(parent.width)
                    parent.displayHeight = ScaleDpiF(parent.height)
                    sizeChanged = oldDisplayWidth != parent.displayWidth or oldDisplayHeight != parent.displayHeight
                    if sizeChanged:
                        for each in parent.children:
                            each.FlagAlignmentDirty()

                parent.UpdateAlignment(updateChildrenOnly=True)

    @telemetry.ZONE_METHOD
    def GetAbsolutePosition(self):
        """
        Returns absolute screen position of this item.
        
        Please do not use this method unless it's absolutely necessary since it adds
        considerable alignment overhead in many cases"""
        if self.destroyed or not self.display:
            return (0, 0)
        self._AssureAlignmentUpdated()
        l, t = self._GetAbsolutePosition(0, 0)
        return (ReverseScaleDpi(l), ReverseScaleDpi(t))

    def _GetAbsolutePosition(self, childLeft, childTop):
        parent = self.GetParent()
        left, top = self._GetRelativePosition()
        left += childLeft
        top += childTop
        if parent and self.align != uiconst.ABSOLUTE:
            left, top = parent._GetAbsolutePosition(left, top)
        return (left, top)

    def _GetRelativePosition(self):
        """ Returns position relative to parent """
        if self.renderObject:
            return (self.renderObject.displayX, self.renderObject.displayY)
        else:
            return (self.displayX, self.displayY)

    def GetAbsoluteLeft(self):
        l, t = self.GetAbsolutePosition()
        return l

    absoluteLeft = property(GetAbsoluteLeft)

    def GetAbsoluteTop(self):
        l, t = self.GetAbsolutePosition()
        return t

    absoluteTop = property(GetAbsoluteTop)

    def GetAbsoluteBottom(self):
        l, t = self.GetAbsolutePosition()
        w, h = self.GetAbsoluteSize()
        return t + h

    absoluteBottom = property(GetAbsoluteBottom)

    def GetAbsoluteRight(self):
        l, t = self.GetAbsolutePosition()
        w, h = self.GetAbsoluteSize()
        return l + w

    absoluteRight = property(GetAbsoluteRight)

    def SetState(self, state):
        """Sets oldstyle state of this object. State can be one of:
            uiconst.UI_NORMAL       --> Object visible and pickable
            uiconst.UI_DISABLED     --> Object visible and not pickable
            uiconst.UI_HIDDEN       --> Object not visible
            uiconst.UI_PICKCHILDREN --> Object visible, only childrens pickable
        """
        if state == uiconst.UI_NORMAL:
            self.display = True
            self.pickState = uiconst.TR2_SPS_ON
        elif state == uiconst.UI_DISABLED:
            self.display = True
            self.pickState = uiconst.TR2_SPS_OFF
        elif state == uiconst.UI_HIDDEN:
            self.display = False
        elif state == uiconst.UI_PICKCHILDREN:
            self.display = True
            self.pickState = uiconst.TR2_SPS_CHILDREN

    def GetState(self):
        """
        Returns oldstyle state of this object. State can be one of:
            uiconst.UI_NORMAL       --> Object visible and pickable
            uiconst.UI_DISABLED     --> Object visible and not pickable
            uiconst.UI_HIDDEN       --> Object not visible
            uiconst.UI_PICKCHILDREN --> Object visible, only childrens pickable
        """
        if not self.display:
            return uiconst.UI_HIDDEN
        if self.pickState == uiconst.TR2_SPS_CHILDREN:
            return uiconst.UI_PICKCHILDREN
        if self.pickState == uiconst.TR2_SPS_ON:
            return uiconst.UI_NORMAL
        if self.pickState == uiconst.TR2_SPS_OFF:
            return uiconst.UI_DISABLED

    state = property(GetState, SetState)

    def FlagAlignmentDirty(self, hint = None):
        if not self.display or self._constructingBase:
            return
        self._alignmentDirty = True
        flagObj = self.parent
        if flagObj and (flagObj._childrenAlignmentDirty or not flagObj._display):
            return
        while flagObj:
            flagObj._childrenAlignmentDirty = True
            if flagObj.align == uiconst.NOALIGN:
                uicore.uilib.alignIslands.append(flagObj)
                return
            flagObj = flagObj.parent
            if flagObj and (flagObj._childrenAlignmentDirty or not flagObj._display):
                return

    @telemetry.ZONE_METHOD
    def UpdateToLeftAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom)
            displayWidth = ScaleDpiF(width)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        widthUsed = ScaleDpiF(padLeft + width + left + padRight)
        budgetLeft += widthUsed
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToLeftAlignmentNoPush(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom)
            displayWidth = ScaleDpiF(width)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToRightAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + budgetWidth - ScaleDpiF(width + padRight + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom)
            displayWidth = ScaleDpiF(width)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        widthUsed = ScaleDpiF(padLeft + width + padRight + left)
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToRightAlignmentNoPush(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + budgetWidth - ScaleDpiF(width + padRight + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom)
            displayWidth = ScaleDpiF(width)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToBottomAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + budgetHeight - ScaleDpiF(height + padBottom + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight)
            displayHeight = ScaleDpiF(height)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        heightUsed = ScaleDpiF(padTop + height + top + padBottom)
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToBottomAlignmentNoPush(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + budgetHeight - ScaleDpiF(height + padBottom + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight)
            displayHeight = ScaleDpiF(height)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToTopAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight)
            displayHeight = ScaleDpiF(height)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        heightUsed = ScaleDpiF(padTop + height + top + padBottom)
        budgetTop += heightUsed
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToTopAlignmentNoPush(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight)
            displayHeight = ScaleDpiF(height)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToAllAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight + left + width)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom + top + height)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateAbsoluteAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        if not budgetOnly:
            left, top, width, height = self.pos
            displayX = ScaleDpiF(left)
            displayY = ScaleDpiF(top)
            displayWidth = ScaleDpiF(width)
            displayHeight = ScaleDpiF(height)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateTopLeftAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            displayX = ScaleDpiF(left + padLeft)
            displayY = ScaleDpiF(top + padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateTopRightAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = budgetWidth + ScaleDpiF(padLeft - width - left)
            displayY = ScaleDpiF(top + padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateBottomRightAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = budgetWidth + ScaleDpiF(padLeft - width - left)
            displayY = budgetHeight + ScaleDpiF(padTop - height - top)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateBottomLeftAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = ScaleDpiF(left + padLeft)
            displayY = budgetHeight + ScaleDpiF(padTop - height - top)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = (budgetWidth - ScaleDpiF(width)) / 2 + ScaleDpiF(left + padLeft)
            displayY = (budgetHeight - ScaleDpiF(height)) / 2 + ScaleDpiF(top + padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterBottomAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = (budgetWidth - ScaleDpiF(width)) / 2 + ScaleDpiF(left + padLeft)
            displayY = budgetHeight - ScaleDpiF(height + top - padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterTopAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = (budgetWidth - ScaleDpiF(width)) / 2 + ScaleDpiF(left + padLeft)
            displayY = ScaleDpiF(top + padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterLeftAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = ScaleDpiF(left + padLeft)
            displayY = (budgetHeight - ScaleDpiF(height)) / 2 + ScaleDpiF(top + padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterRightAlignment(self, budgetOnly, *budget):
        if not budgetOnly:
            padLeft, padTop, padRight, padBottom = self.padding
            left, top, width, height = self.pos
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            displayX = budgetWidth - ScaleDpiF(width + left - padLeft)
            displayY = (budgetHeight - ScaleDpiF(height)) / 2 + ScaleDpiF(top + padTop)
            displayWidth = ScaleDpiF(width - padLeft - padRight)
            displayHeight = ScaleDpiF(height - padTop - padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateNoAlignment(self, budgetOnly, *budget):
        left, top, width, height = self.pos
        displayWidth = ScaleDpi(width)
        displayHeight = ScaleDpi(height)
        self.displayWidth = displayWidth
        self.displayHeight = displayHeight
        return budget

    @telemetry.ZONE_METHOD
    def UpdateToLeftProportionalAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            width = int(float(self.parent.displayWidth) * width)
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom)
            displayWidth = width - ScaleDpiF(padLeft + padRight)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        widthUsed = ScaleDpiF(padLeft + left + padRight) + self.displayWidth
        budgetLeft += widthUsed
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToRightProportionalAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            width = int(float(self.parent.displayWidth) * self._width)
            displayX = budgetLeft + budgetWidth - width - ScaleDpiF(padRight + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayHeight = budgetHeight - ScaleDpiF(padTop + padBottom)
            displayWidth = width - ScaleDpiF(padLeft + padRight)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        widthUsed = ScaleDpiF(padLeft + padRight + left) + self.displayWidth
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToTopProportionalAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            height = int(float(self.parent.displayHeight) * height)
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + ScaleDpiF(padTop + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight)
            displayHeight = height - ScaleDpiF(padTop + padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        heightUsed = ScaleDpiF(padTop + top + padBottom) + self.displayHeight
        budgetTop += heightUsed
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToBottomProportionalAlignment(self, budgetOnly, budgetLeft, budgetTop, budgetWidth, budgetHeight):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            height = int(float(self.parent.displayHeight) * height)
            displayX = budgetLeft + ScaleDpiF(padLeft + left)
            displayY = budgetTop + budgetHeight - height - ScaleDpiF(padBottom + top)
            displayWidth = budgetWidth - ScaleDpiF(padLeft + padRight)
            displayHeight = height - ScaleDpiF(padTop + padBottom)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        heightUsed = ScaleDpiF(padTop + top + padBottom) + self.displayHeight
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateTopLeftProportionalAlignment(self, budgetOnly, *budget):
        padLeft, padTop, padRight, padBottom = self.padding
        left, top, width, height = self.pos
        if not budgetOnly:
            parent = self.parent
            budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
            if self._width < 1.0:
                displayWidth = width * budgetWidth - ScaleDpiF(padLeft + padRight)
            else:
                displayWidth = ScaleDpiF(width - padLeft - padRight)
            if self._height < 1.0:
                displayHeight = height * budgetHeight - ScaleDpiF(padTop + padBottom)
            else:
                displayHeight = ScaleDpiF(height - padTop - padBottom)
            if self._left < 1.0:
                displayX = (budgetWidth - displayWidth) * (left + padLeft)
            else:
                displayX = ScaleDpiF(left + padLeft)
            if self._top < 1.0:
                displayY = (budgetHeight - displayHeight) * (top + padTop)
            else:
                displayY = ScaleDpiF(top + padTop)
            self.displayRect = (displayX,
             displayY,
             displayWidth,
             displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateAlignmentAsRoot(self, caller = None):
        if self.destroyed or not self.display:
            return
        if self.align == uiconst.NOALIGN:
            self.UpdateAlignment(0, 0, ScaleDpi(self.width), ScaleDpi(self.height))
        else:
            self.UpdateAlignment(0, 0, self.displayWidth, self.displayHeight)

    def UpdateAlignment(self, budgetLeft = 0, budgetTop = 0, budgetWidth = 0, budgetHeight = 0, updateChildrenOnly = False):
        if self.destroyed:
            return (budgetLeft,
             budgetTop,
             budgetWidth,
             budgetHeight,
             False)
        displayDirty = self._displayDirty
        alignmentDirty = self._alignmentDirty
        self._alignmentDirty = False
        self._displayDirty = False
        fullUpdate = alignmentDirty or displayDirty
        sizeChange = False
        preDX, preDY, preDWidth, preDHeight = self.displayRect
        budgetLeft, budgetTop, budgetWidth, budgetHeight = self._alignFunc(self, not fullUpdate, budgetLeft, budgetTop, budgetWidth, budgetHeight)
        if fullUpdate:
            newDX, newDY, newDWidth, newDHeight = self.displayRect
            sizeChange = preDWidth != newDWidth or preDHeight != newDHeight
            posChange = preDX != newDX or preDY != newDY
            if sizeChange or posChange:
                if self._OnResize.im_func != Base._OnResize.im_func:
                    self._OnResize()
            if sizeChange:
                self._OnSizeChange_NoBlock(ReverseScaleDpi(newDWidth), ReverseScaleDpi(newDHeight))
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight,
         sizeChange)

    def ScaleDpi(self, value):
        """
        Applies dpi scaling to the given value.
        """
        return ScaleDpi(value)

    def ReverseScaleDpi(self, value):
        """
        Applies reverse dpi scaling to the given value.
        """
        return ReverseScaleDpi(value)

    def Toggle(self, *args):
        """ Toggles visible state off this item """
        if self.IsHidden():
            self.Show()
        else:
            self.Hide()

    def Hide(self, *args):
        self.display = False

    def Show(self, *args):
        self.display = True

    def IsHidden(self):
        """Returns True if this object is hidden"""
        return not self.display

    def FindParentByName(self, parentName):
        parent = self.GetParent()
        while parent:
            if parent.name == parentName:
                return parent
            parent = parent.GetParent()

    @apply
    def cursor():
        doc = 'Cursor value of this object. Triggers cursor update when set'

        def fget(self):
            return self._cursor

        def fset(self, value):
            self._cursor = value
            uicore.CheckCursor()

        return property(**locals())

    def _OnClose(self, *args, **kw):
        pass

    def _OnResize(self, *args):
        pass

    def _OnSizeChange_NoBlock(self, *args):
        pass

    def OnMouseUp(self, *args):
        pass

    def OnMouseDown(self, *args):
        pass

    def OnMouseEnter(self, *args):
        pass

    def OnMouseExit(self, *args):
        pass

    def OnMouseHover(self, *args):
        pass

    def OnClick(self, *args):
        pass

    def OnMouseMove(self, *args):
        pass

    def DelegateEvents(self, delegateTo):
        self._delegatingEvents = True
        for eventName in DELEGATE_EVENTNAMES:
            toHandler = getattr(delegateTo, eventName, None)
            if toHandler:
                setattr(self, eventName, toHandler)

    def DelegateEventsNotImplemented(self, delegateTo):
        """Same as DelegateEvents except it leaves out functions
        which have been implemented in self"""
        self._delegatingEvents = True
        for eventName in DELEGATE_EVENTNAMES:
            haveLocal = self.HasEventHandler(eventName)
            if not haveLocal:
                toHandler = getattr(delegateTo, eventName, None)
                if toHandler:
                    setattr(self, eventName, toHandler)

    @apply
    def __bluetype__():
        doc = 'legacy trinity name of object'

        def fget(self):
            if self.__renderObject__:
                return self.__renderObject__().__bluetype__

        return property(**locals())

    @apply
    def __typename__():
        doc = 'legacy type name of object'

        def fget(self):
            if self.__renderObject__:
                return self.__renderObject__().__typename__

        return property(**locals())


ALIGN_AND_CONSUME_FUNCTIONS = {uiconst.TOPLEFT: (Base.UpdateTopLeftAlignment, uiconst.TOPLEFT in PUSHALIGNMENTS, uiconst.TOPLEFT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOALL: (Base.UpdateToAllAlignment, uiconst.TOALL in PUSHALIGNMENTS, uiconst.TOALL in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.NOALIGN: (Base.UpdateNoAlignment, uiconst.NOALIGN in PUSHALIGNMENTS, uiconst.NOALIGN in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOLEFT: (Base.UpdateToLeftAlignment, uiconst.TOLEFT in PUSHALIGNMENTS, uiconst.TOLEFT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TORIGHT: (Base.UpdateToRightAlignment, uiconst.TORIGHT in PUSHALIGNMENTS, uiconst.TORIGHT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOTOP: (Base.UpdateToTopAlignment, uiconst.TOTOP in PUSHALIGNMENTS, uiconst.TOTOP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOBOTTOM: (Base.UpdateToBottomAlignment, uiconst.TOBOTTOM in PUSHALIGNMENTS, uiconst.TOBOTTOM in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOLEFT_NOPUSH: (Base.UpdateToLeftAlignmentNoPush, uiconst.TOLEFT_NOPUSH in PUSHALIGNMENTS, uiconst.TOLEFT_NOPUSH in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TORIGHT_NOPUSH: (Base.UpdateToRightAlignmentNoPush, uiconst.TORIGHT_NOPUSH in PUSHALIGNMENTS, uiconst.TORIGHT_NOPUSH in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOTOP_NOPUSH: (Base.UpdateToTopAlignmentNoPush, uiconst.TOTOP_NOPUSH in PUSHALIGNMENTS, uiconst.TOTOP_NOPUSH in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOBOTTOM_NOPUSH: (Base.UpdateToBottomAlignmentNoPush, uiconst.TOBOTTOM_NOPUSH in PUSHALIGNMENTS, uiconst.TOBOTTOM_NOPUSH in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOLEFT_PROP: (Base.UpdateToLeftProportionalAlignment, uiconst.TOLEFT_PROP in PUSHALIGNMENTS, uiconst.TOLEFT_PROP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TORIGHT_PROP: (Base.UpdateToRightProportionalAlignment, uiconst.TORIGHT_PROP in PUSHALIGNMENTS, uiconst.TORIGHT_PROP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOTOP_PROP: (Base.UpdateToTopProportionalAlignment, uiconst.TOTOP_PROP in PUSHALIGNMENTS, uiconst.TOTOP_PROP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOBOTTOM_PROP: (Base.UpdateToBottomProportionalAlignment, uiconst.TOBOTTOM_PROP in PUSHALIGNMENTS, uiconst.TOBOTTOM_PROP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.ABSOLUTE: (Base.UpdateAbsoluteAlignment, uiconst.ABSOLUTE in PUSHALIGNMENTS, uiconst.ABSOLUTE in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOPLEFT_PROP: (Base.UpdateTopLeftProportionalAlignment, uiconst.TOPLEFT_PROP in PUSHALIGNMENTS, uiconst.TOPLEFT_PROP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.TOPRIGHT: (Base.UpdateTopRightAlignment, uiconst.TOPRIGHT in PUSHALIGNMENTS, uiconst.TOPRIGHT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.BOTTOMRIGHT: (Base.UpdateBottomRightAlignment, uiconst.BOTTOMRIGHT in PUSHALIGNMENTS, uiconst.BOTTOMRIGHT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.BOTTOMLEFT: (Base.UpdateBottomLeftAlignment, uiconst.BOTTOMLEFT in PUSHALIGNMENTS, uiconst.BOTTOMLEFT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.CENTER: (Base.UpdateCenterAlignment, uiconst.CENTER in PUSHALIGNMENTS, uiconst.CENTER in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.CENTERBOTTOM: (Base.UpdateCenterBottomAlignment, uiconst.CENTERBOTTOM in PUSHALIGNMENTS, uiconst.CENTERBOTTOM in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.CENTERTOP: (Base.UpdateCenterTopAlignment, uiconst.CENTERTOP in PUSHALIGNMENTS, uiconst.CENTERTOP in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.CENTERLEFT: (Base.UpdateCenterLeftAlignment, uiconst.CENTERLEFT in PUSHALIGNMENTS, uiconst.CENTERLEFT in AFFECTEDBYPUSHALIGNMENTS),
 uiconst.CENTERRIGHT: (Base.UpdateCenterRightAlignment, uiconst.CENTERRIGHT in PUSHALIGNMENTS, uiconst.CENTERRIGHT in AFFECTEDBYPUSHALIGNMENTS)}
