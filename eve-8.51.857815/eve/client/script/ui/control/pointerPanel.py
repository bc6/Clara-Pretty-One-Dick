#Embedded file name: eve/client/script/ui/control\pointerPanel.py
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.primitives.frame import Frame
from carbonui.primitives.fill import Fill
from carbonui.primitives.transform import Transform
from carbonui.primitives.layoutGrid import LayoutGrid
from eve.client.script.ui.control.eveLabel import EveLabelMedium
import carbonui.const as uiconst
import base
import blue
import uiutil
import weakref
from eve.client.script.ui.control.eveWindowUnderlay import FrameUnderlay, SpriteUnderlay
import uthread
LEFTGROUP = [uiconst.POINT_LEFT_2, uiconst.POINT_LEFT_1, uiconst.POINT_LEFT_3]
RIGHTGROUP = [uiconst.POINT_RIGHT_2, uiconst.POINT_RIGHT_1, uiconst.POINT_RIGHT_3]
TOPGROUP = [uiconst.POINT_TOP_2, uiconst.POINT_TOP_1, uiconst.POINT_TOP_3]
BOTTOMGROUP = [uiconst.POINT_BOTTOM_2, uiconst.POINT_BOTTOM_1, uiconst.POINT_BOTTOM_3]
CORNERGROUP = [uiconst.POINT_TOPLEFT,
 uiconst.POINT_TOPRIGHT,
 uiconst.POINT_BOTTOMLEFT,
 uiconst.POINT_BOTTOMRIGHT]
POINT_CORRECTION = {uiconst.POINT_LEFT_1: LEFTGROUP + RIGHTGROUP + BOTTOMGROUP + TOPGROUP,
 uiconst.POINT_LEFT_2: LEFTGROUP + RIGHTGROUP + BOTTOMGROUP + TOPGROUP,
 uiconst.POINT_LEFT_3: LEFTGROUP + RIGHTGROUP + BOTTOMGROUP + TOPGROUP,
 uiconst.POINT_RIGHT_1: RIGHTGROUP + LEFTGROUP + BOTTOMGROUP + TOPGROUP,
 uiconst.POINT_RIGHT_2: RIGHTGROUP + LEFTGROUP + BOTTOMGROUP + TOPGROUP,
 uiconst.POINT_RIGHT_3: RIGHTGROUP + LEFTGROUP + BOTTOMGROUP + TOPGROUP,
 uiconst.POINT_BOTTOM_1: BOTTOMGROUP + LEFTGROUP + TOPGROUP + RIGHTGROUP,
 uiconst.POINT_BOTTOM_2: [uiconst.POINT_LEFT_2] + BOTTOMGROUP + LEFTGROUP + TOPGROUP + RIGHTGROUP,
 uiconst.POINT_BOTTOM_3: BOTTOMGROUP + LEFTGROUP + TOPGROUP + RIGHTGROUP,
 uiconst.POINT_TOP_1: TOPGROUP + LEFTGROUP + BOTTOMGROUP + RIGHTGROUP,
 uiconst.POINT_TOP_2: TOPGROUP + LEFTGROUP + BOTTOMGROUP + RIGHTGROUP,
 uiconst.POINT_TOP_3: TOPGROUP + LEFTGROUP + BOTTOMGROUP + RIGHTGROUP}
FRAME_WITH_POINTER_SKIN_GENERAL = 'general'
FRAME_WITH_POINTER_SKIN_BADGE = 'badgeStyle'

class GeneralFrameWithPointerSkin(object):

    def __init__(self):
        self.skinName = 'general'
        self.leftTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_left_02.png'
        self.rightTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_right_02.png'
        self.topRightTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_topright_02.png'
        self.topLeftTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_topleft_02.png'
        self.upTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_up_02.png'
        self.downTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_down_02.png'
        self.bottomLeftTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_bottomleft_02.png'
        self.bottomRightTexture = 'res:/UI/Texture/classes/FrameWithPointer/pointer_bottomright_02.png'
        self.backgroundTexture = 'res:/UI/Texture/classes/FrameWithPointer/background_04.png'
        self.backgroundOffset = -15
        self.backgroundCornerSize = 19


class BadgeStyleFrameWithPointerSkin(GeneralFrameWithPointerSkin):

    def __init__(self):
        super(BadgeStyleFrameWithPointerSkin, self).__init__()
        self.skinName = 'badgeStyle'
        self.leftTexture = 'res:/UI/Texture/classes/Notifications/pointer_left_02.png'
        self.rightTexture = 'res:/UI/Texture/classes/Notifications/pointer_right_02.png'
        self.backgroundTexture = 'res:/UI/Texture/classes/Notifications/newItemsBadgeBase.png'
        self.backgroundOffset = -6
        self.backgroundCornerSize = 10


SKIN_NAME_TO_CLASS = {FRAME_WITH_POINTER_SKIN_GENERAL: GeneralFrameWithPointerSkin,
 FRAME_WITH_POINTER_SKIN_BADGE: BadgeStyleFrameWithPointerSkin}

class PointerPanel(LayoutGrid):
    """
    Object base on layout grid to display various information,
    can contain any object based on carbonui.Base class.
    The positioning is based on anchoring where rect from the owner and
    point of this panel are aligned.
    """
    default_state = uiconst.UI_PICKCHILDREN
    default_align = uiconst.ABSOLUTE
    default_opacity = 0.0
    default_cellClipChildren = False
    beingDestroyed = False
    _owner = None
    pointerSize = 9
    scaleTransform = None
    defaultPointer = uiconst.POINT_BOTTOM_2

    def ApplyAttributes(self, attributes):
        attributes.align = uiconst.TOPLEFT
        LayoutGrid.ApplyAttributes(self, attributes)
        self.backgroundFrame = FrameWithPointer(bgParent=self, color=attributes.color)
        if attributes.owner:
            self.owner = attributes.owner
        else:
            self.opacity = 1.0

    def SetBackgroundColor(self, color):
        self.backgroundFrame.SetColor(color)

    def SetBackgroundAlpha(self, alphaValue):
        self.backgroundFrame.SetAlpha(alphaValue)

    @apply
    def owner():
        doc = "Weakref'd Owner of the panel"

        def fset(self, value):
            self._owner = weakref.ref(value)

        def fget(self):
            if self._owner:
                owner = self._owner()
                if owner and not owner.destroyed:
                    return owner
                self._owner = None

        return property(**locals())

    def Close(self, *args):
        LayoutGrid.Close(self, *args)
        if getattr(self, 'debugFrame', None):
            self.debugFrame.Close()
        if self.scaleTransform:
            self.scaleTransform.Close()
            self.scaleTransform = None

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
            adjustedLeft = int(round(left))
            adjustedTop = int(round(top))
            adjustedWidth = int(round(width))
            adjustedHeight = int(round(height))
            self._left = adjustedLeft
            self._top = adjustedTop
            self._width = adjustedWidth
            self._height = adjustedHeight
            self._displayX = uicore.ScaleDpi(adjustedLeft)
            self._displayY = uicore.ScaleDpi(adjustedTop)
            self._displayWidth = uicore.ScaleDpi(adjustedWidth)
            self._displayHeight = uicore.ScaleDpi(adjustedHeight)
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight
            self.UpdateBackgrounds()

        return property(**locals())

    @apply
    def left():
        doc = 'x-coordinate of UI element'

        def fget(self):
            return self._left

        def fset(self, value):
            adjustedValue = int(round(value))
            if adjustedValue != self._left:
                self._left = adjustedValue
                self._displayX = uicore.ScaleDpi(adjustedValue)
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
            adjustedValue = int(round(value))
            if adjustedValue != self._top:
                self._top = adjustedValue
                self._displayY = uicore.ScaleDpi(adjustedValue)
                ro = self.renderObject
                if ro:
                    ro.displayY = self._displayY

        return property(**locals())

    @apply
    def width():
        doc = 'Width of UI element'

        def fget(self):
            return self._width

        def fset(self, value):
            adjustedValue = int(round(value))
            if adjustedValue != self._width:
                self._width = adjustedValue
                self._displayWidth = uicore.ScaleDpi(adjustedValue)
                ro = self.renderObject
                if ro:
                    ro.displayWidth = self._displayWidth
                self.UpdateBackgrounds()
                owner = self.owner
                if owner is None:
                    return
                RefreshPanelPosition(self)

        return property(**locals())

    @apply
    def height():
        doc = 'Height of UI element'

        def fget(self):
            return self._height

        def fset(self, value):
            adjustedValue = int(round(value))
            if adjustedValue != self._height:
                self._height = adjustedValue
                self._displayHeight = uicore.ScaleDpi(adjustedValue)
                ro = self.renderObject
                if ro:
                    ro.displayHeight = self._displayHeight
                self.UpdateBackgrounds()
                owner = self.owner
                if owner is None:
                    return
                RefreshPanelPosition(self)

        return property(**locals())

    def GetPointerOffset(self):
        return self.backgroundFrame.pointerOffset

    def ShowPanel(self, owner):
        blue.synchro.Yield()
        if self.destroyed:
            return
        blue.synchro.SleepWallclock(2)
        if self.destroyed:
            return
        uicore.animations.FadeTo(self, startVal=self.opacity, endVal=1.0, duration=0.05, curveType=uiconst.ANIM_SMOOTH)


class FrameWithPointer(Container):
    pointerOffset = None
    skinCache = {}

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        skinName = attributes.get('skinName', 'general')
        actualSkinClass = SKIN_NAME_TO_CLASS.get(skinName)
        if not FrameWithPointer.skinCache.get(skinName):
            FrameWithPointer.skinCache[skinName] = actualSkinClass()
        self.skin = FrameWithPointer.skinCache[skinName]
        self._pointer = SpriteUnderlay(texturePath='res:/UI/Texture/classes/FrameWithPointer/pointer_down_02.png', parent=self, colorType=attributes.colorType or uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.95)
        self._background = FrameUnderlay(name='__underlay', bgParent=self, cornerSize=self.skin.backgroundCornerSize, offset=self.skin.backgroundOffset, texturePath=self.skin.backgroundTexture, colorType=attributes.colorType or uiconst.COLORTYPE_UIHILIGHTGLOW, opacity=0.95)

    def SetColor(self, color):
        self._background.color = color
        self._pointer.color = color

    def SetAlpha(self, alphaValue):
        self._background.SetAlpha(alphaValue)
        self._pointer.SetAlpha(alphaValue)

    def UpdatePointerPosition(self, positionFlag):
        if positionFlag == uiconst.POINTER_NONE:
            self._pointer.display = False
            return (0, 0)
        SIZE = 24
        BACKOFFSET = 8
        x, y = positionFlag
        self._pointer.displayX = [-SIZE + BACKOFFSET,
         0,
         (self.displayWidth - SIZE) / 2,
         self.displayWidth - SIZE,
         self.displayWidth - BACKOFFSET][x]
        self._pointer.displayY = [-SIZE + BACKOFFSET,
         0,
         (self.displayHeight - SIZE) / 2,
         self.displayHeight - SIZE,
         self.displayHeight - BACKOFFSET][y]
        self._pointer.displayWidth = SIZE
        self._pointer.displayHeight = SIZE
        if y == 0:
            if x == 0:
                self._pointer.displayX = -11
                self._pointer.displayY = -11
                resPath = self.skin.topLeftTexture
                self.pointerOffset = [self._pointer.displayX + 5, self._pointer.displayY + 5]
            elif x == 4:
                self._pointer.displayX = self.displayWidth - 13
                self._pointer.displayY = -11
                resPath = self.skin.topRightTexture
                self.pointerOffset = [self._pointer.displayX + 19, self._pointer.displayY + 5]
            else:
                resPath = self.skin.upTexture
                self.pointerOffset = [self._pointer.displayX + SIZE / 2, self._pointer.displayY + 10]
        elif y == 4:
            if x == 0:
                self._pointer.displayX = -11
                self._pointer.displayY = self.displayHeight - 13
                resPath = self.skin.bottomLeftTexture
                self.pointerOffset = [self._pointer.displayX + 5, self._pointer.displayY + 19]
            elif x == 4:
                self._pointer.displayX = self.displayWidth - 13
                self._pointer.displayY = self.displayHeight - 13
                resPath = self.skin.bottomRightTexture
                self.pointerOffset = [self._pointer.displayX + 19, self._pointer.displayY + 19]
            else:
                resPath = self.skin.downTexture
                self.pointerOffset = [self._pointer.displayX + SIZE / 2, self._pointer.displayY + 14]
        elif x == 0:
            resPath = self.skin.leftTexture
            self.pointerOffset = [self._pointer.displayX + 10, self._pointer.displayY + SIZE / 2]
        elif x == 4:
            resPath = self.skin.rightTexture
            self.pointerOffset = [self._pointer.displayX + 14, self._pointer.displayY + SIZE / 2]
        self._pointer.SetTexturePath(resPath)
        self._pointer.display = True
        return self.pointerOffset


def RefreshPanelPosition(pointerPanel):
    owner = pointerPanel.owner
    if owner is None:
        return
    panelPosition, isBlocked = GetPanelInterestFromObject(owner, checkIfBlockedByOther=getattr(pointerPanel, 'checkIfBlocked', True))
    if isBlocked:
        pointer = pointerPanel.defaultPointer
    else:
        pointer = GetPanelPointerFromOwner(owner)
        if pointer is None:
            pointer = pointerPanel.defaultPointer
    UpdatePanelPosition(pointerPanel, panelPosition, pointer)


def GetPanelInterestFromObject(uiObject, checkIfBlockedByOther = True):
    """By default we use the absolute position rect of the object to position
    the panel, but the object can override it by implementing GetTooltipPosition"""
    if hasattr(uiObject, 'GetTooltipPosition'):
        customInterestRect = uiObject.GetTooltipPosition()
        if customInterestRect:
            return (customInterestRect, False)
    if uicore.uilib.auxiliaryTooltip and uicore.uilib.auxiliaryTooltipPosition:
        absolutePosition = uicore.uilib.auxiliaryTooltipPosition
    else:
        absolutePosition = uiObject.GetAbsolute()
    retLeft, retTop, retWidth, retHeight = absolutePosition
    retRight = retLeft + retWidth
    retBottom = retTop + retHeight
    obj = uiObject.parent
    while obj:
        l, t, w, h = obj.GetAbsolute()
        retLeft = max(retLeft, l)
        retTop = max(retTop, t)
        retRight = min(retRight, l + w)
        retBottom = min(retBottom, t + h)
        obj = obj.parent

    if checkIfBlockedByOther:
        isBlocked = IsPartiallyBlockedByOther(uiObject, (retLeft,
         retTop,
         retRight,
         retBottom))
        if isBlocked:
            retLeft = max(retLeft, uicore.uilib.x - 8)
            retTop = max(retTop, uicore.uilib.y - 8)
            retRight = min(retRight, uicore.uilib.x + 8)
            retBottom = min(retBottom, uicore.uilib.y + 8)
    else:
        isBlocked = False
    return ((retLeft,
      retTop,
      retRight - retLeft,
      retBottom - retTop), isBlocked)


def IsPartiallyBlockedByOther(uiObject, rect):
    retLeft, retTop, retRight, retBottom = rect
    hierarchyTrace = GetObjectDesktopHierarchyPosition(uiObject)
    windows = uicore.registry.GetValidWindows()
    for window in windows:
        if not window.display or uiObject.IsUnder(window):
            continue
        windowHierarchyTrace = GetObjectDesktopHierarchyPosition(window)
        if hierarchyTrace < windowHierarchyTrace:
            continue
        l2, t2, w2, h2 = window.GetAbsolute()
        overlapx = not (retRight <= l2 or retLeft >= l2 + w2)
        overlapy = not (retBottom <= t2 or retTop >= t2 + h2)
        if overlapx and overlapy:
            return True

    return False


def SubtractBlockingUIElements(uiObject, rect):
    retLeft, retTop, retRight, retBottom = rect
    hierarchyTrace = GetObjectDesktopHierarchyPosition(uiObject)
    windows = uicore.registry.GetValidWindows()
    for window in windows:
        if not window.display or uiObject.IsUnder(window):
            continue
        windowHierarchyTrace = GetObjectDesktopHierarchyPosition(window)
        if hierarchyTrace < windowHierarchyTrace:
            continue
        l2, t2, w2, h2 = window.GetAbsolute()
        overlapx = not (retRight <= l2 or retLeft >= l2 + w2)
        overlapy = not (retBottom <= t2 or retTop >= t2 + h2)
        if not (overlapx and overlapy):
            continue
        skipVertical = False
        if retLeft < l2 < retRight:
            retRight = l2
            skipVertical = True
        if retLeft < l2 + w2 < retRight:
            retLeft = l2 + w2
            skipVertical = True
        if not skipVertical:
            if retTop < t2 < retBottom:
                retBottom = t2
            if retTop < t2 + h2 < retBottom:
                retTop = t2 + h2

    return (retLeft,
     retTop,
     retRight,
     retBottom)


def GetObjectDesktopHierarchyPosition(uiObject):
    trace = []
    obj = uiObject
    while obj.parent:
        idx = obj.parent.children.index(obj)
        trace.insert(0, idx)
        obj = obj.parent

    return trace


def GetPanelPointerFromOwner(uiObject):
    if hasattr(uiObject, 'GetTooltipPointer'):
        customPointer = uiObject.GetTooltipPointer()
        if customPointer is not None:
            return customPointer


def UpdatePanelPosition(panel, interestRect, menuPointFlag = None, fallbackPointFlags = None):
    if menuPointFlag is None:
        menuPointFlag = uiconst.POINT_BOTTOM_2
    if fallbackPointFlags is None:
        if hasattr(panel.owner, 'GetTooltipPositionFallbacks'):
            fallbackPointFlags = panel.owner.GetTooltipPositionFallbacks()
        else:
            fallbackPointFlags = POINT_CORRECTION.get(menuPointFlag, [])[:]
            fallbackPointFlags += CORNERGROUP
    AlignPointPanelToInterest(panel, menuPointFlag, interestRect)
    if fallbackPointFlags and panel.parent:
        if panel.left < 0 or panel.left + panel.width > uicore.desktop.width or panel.top < 0 or panel.top + panel.height > uicore.desktop.height:
            tryFlag = fallbackPointFlags.pop(0)
            UpdatePanelPosition(panel, interestRect, menuPointFlag=tryFlag, fallbackPointFlags=fallbackPointFlags)


def AlignPointPanelToInterest(panel, menuPointFlag, interestRect):
    al, at, aw, ah = interestRect
    if getattr(panel, 'debugShowInterest', False):
        if getattr(panel, 'debugFrame', None):
            panel.debugFrame.Close()
        panel.debugFrame = Frame(parent=uicore.layer.main, pos=interestRect, align=uiconst.TOPLEFT, idx=0)
    pointerOffset = panel.backgroundFrame.UpdatePointerPosition(menuPointFlag)
    px, py = pointerOffset
    px = uicore.ReverseScaleDpi(px)
    py = uicore.ReverseScaleDpi(py)
    fx, fy = menuPointFlag
    panel.menuPointFlag = menuPointFlag
    if fy == 4:
        panel.top = at - panel.height - panel.pointerSize
    elif fy == 0:
        panel.top = at + ah + panel.pointerSize
    else:
        panel.top = at + ah / 2 - py
    if fx == 4:
        panel.left = al - panel.width - panel.pointerSize
    elif fx == 0:
        panel.left = al + aw + panel.pointerSize
    else:
        panel.left = al + aw / 2 - px


def FadeOutPanelAndClose(panel, duration = 0.2):
    if panel.destroyed or panel.beingDestroyed:
        return
    panel.beingDestroyed = True
    duration *= panel.opacity
    if not duration:
        panel.Close()
        return
    pointerOffset = panel.backgroundFrame.pointerOffset
    if not pointerOffset:
        panel.Close()
        return
    x, y = uicore.ReverseScaleDpi(panel.displayX + pointerOffset[0]), uicore.ReverseScaleDpi(panel.displayY + pointerOffset[1])
    panel.scaleTransform = Transform(parent=panel.parent, state=uiconst.UI_DISABLED, align=uiconst.TOALL, scalingCenter=(x / float(uicore.desktop.width), y / float(uicore.desktop.height)))
    panel.parent.renderObject.children.remove(panel.renderObject)
    panel.scaleTransform.renderObject.children.append(panel.renderObject)
    uicore.animations.FadeTo(panel.scaleTransform, startVal=panel.opacity, endVal=0.0, duration=duration * 0.5, curveType=uiconst.ANIM_SMOOTH)
    uicore.animations.Tr2DScaleTo(panel.scaleTransform, panel.scaleTransform.scale, (0.0, 0.0), duration=duration, callback=panel.Close)
