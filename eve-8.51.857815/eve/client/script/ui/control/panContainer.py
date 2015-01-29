#Embedded file name: eve/client/script/ui/control\panContainer.py
from carbonui.primitives.container import Container
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.const import UI_PICKCHILDREN, TOPLEFT, UICURSOR_DRAGGABLE, UI_NORMAL, CENTER
import geo2
import uthread
import blue
from carbonui.primitives.transform import Transform

class PanContainer(Container):
    """ A control that provides basic panning and scaling of it's children """
    default_name = 'PanContainer'
    default_panSpeed = 8.0
    default_panAmount = 2.0
    default_callback = None
    default_state = UI_NORMAL
    default_clipChildren = True
    default_panLeft = 0.0
    default_panTop = 0.0
    default_border = (10, 10, 10, 10)
    default_axisLockMargin = 50
    cursor = UICURSOR_DRAGGABLE

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.panSpeed = attributes.Get('panSpeed', self.default_panSpeed)
        self.panAmount = attributes.Get('panAmount', self.default_panAmount)
        self.callback = attributes.Get('callback', self.default_callback)
        self._border = None
        self.border = attributes.Get('border', self.default_border)
        self._panLeft = attributes.Get('panLeft', self.default_panLeft)
        self._panTop = attributes.Get('panTop', self.default_panTop)
        self.axisLockMargin = attributes.Get('axisLockMargin', self.default_axisLockMargin)
        self._scale = 1.0
        self.panUpdateThread = None
        self.panTarget = None
        self.transform = Transform(parent=self, align=TOPLEFT, state=UI_PICKCHILDREN, scalingCenter=(0.5, 0.5))
        self.mainCont = ContainerAutoSize(name='mainCont', parent=self.transform, align=CENTER, state=UI_PICKCHILDREN)

    def OnMouseMove(self, *args):
        if uicore.uilib.leftbtn and not uicore.uilib.rightbtn:
            k = self.panAmount / self.scale
            self.Pan(k * uicore.uilib.dx, k * uicore.uilib.dy)

    def Pan(self, dx = 0, dy = 0):
        """ Pan along current camera xyz coordinates """
        if self.panTarget is None:
            self.panTarget = geo2.Vector(0, 0)
        if self.IsClampedHorizontally():
            dx = 0
        if self.IsClampedVertically():
            dy = 0
        self.panTarget += geo2.Vector(dx, dy)
        if not self.panUpdateThread:
            self.panUpdateThread = uthread.new(self._PanUpdateThread)

    def IsClampedHorizontally(self, includeMargin = True):
        width = self.transform.width
        parWidth, _ = self.GetAbsoluteSize()
        bLeft, _, bRight, _ = self.border
        margin = self.axisLockMargin if includeMargin else 0
        if width < parWidth - bLeft - bRight + margin:
            return True
        return False

    def IsClampedVertically(self, includeMargin = True):
        height = self.transform.height
        _, parHeight = self.GetAbsoluteSize()
        _, bTop, _, bBottom = self.border
        margin = self.axisLockMargin if includeMargin else 0
        if height < parHeight - bTop - bBottom + margin:
            return True
        return False

    def PanTo(self, panLeft, panTop, animate = True, duration = None, timeOffset = 0.0, sleep = False):
        """ Pan to panLeft, panTop (0.0 - 1.0) """
        if animate:
            if not duration:
                length = geo2.Vec3Distance((panLeft, panTop, 0), (self.panLeft, self.panTop, 0))
                duration = max(0.1, length * self.scale)
            uicore.animations.MorphScalar(self, 'panLeft', self.panLeft, panLeft, duration=duration, timeOffset=timeOffset)
            uicore.animations.MorphScalar(self, 'panTop', self.panTop, panTop, duration=duration, timeOffset=timeOffset, sleep=sleep)
        else:
            self.panLeft = panLeft
            self.panTop = panTop

    def PanToMouseOver(self, duration = None, timeOffset = 0.0, sleep = False):
        """ Pan to location currently being hovered over """
        panLeft, panTop = self.GetMousePositionProportional()
        if not duration:
            length = geo2.Vec2Length((panLeft - self.panLeft, panTop - self.panTop))
            if length < 0.2:
                return 0.0
            duration = max(0.3, length * 0.4)
        self.PanTo(panLeft, panTop, duration=duration, timeOffset=timeOffset, sleep=sleep)
        return duration

    def GetMousePositionProportional(self):
        x = uicore.uilib.x
        y = uicore.uilib.y
        left, top, width, height = self.transform.GetAbsolute()
        x = (x - left) / float(width)
        y = (y - top) / float(height)
        x = max(0.0, min(x, 1.0))
        y = max(0.0, min(y, 1.0))
        return (x, y)

    def GetScale(self):
        return self._scale

    def SetScale(self, value):
        self._scale = value
        self.transform.scale = (value, value)
        self.FlagAlignmentDirty()

    scale = property(GetScale, SetScale)

    def _PanUpdateThread(self):
        while True:
            if self.panTarget is None or not self.mainCont.children:
                break
            distLeft = geo2.Vec2Length(self.panTarget)
            if distLeft == 0:
                break
            dist = self.panSpeed / blue.os.fps
            if distLeft < 1.0:
                dist *= 1.0 / distLeft
            dist = min(dist, 1.0)
            toMove = geo2.Vec2Scale(self.panTarget, dist)
            self.panTarget -= toMove
            dx, dy = toMove
            self.panLeft -= dx / self.mainCont.width
            self.panTop -= dy / self.mainCont.height
            blue.synchro.Yield()

        self.panUpdateThread = None
        self.panTarget = None

    def GetPanLeft(self):
        return self._panLeft

    def SetPanLeft(self, value):
        self._panLeft = max(0.0, min(value, 1.0))
        self.FlagAlignmentDirty()

    panLeft = property(GetPanLeft, SetPanLeft)

    def GetPanTop(self):
        return self._panTop

    def SetPanTop(self, value):
        self._panTop = max(0.0, min(value, 1.0))
        self.FlagAlignmentDirty()

    panTop = property(GetPanTop, SetPanTop)

    def UpdateAlignment(self, *args, **kwds):
        budget = super(PanContainer, self).UpdateAlignment(*args, **kwds)
        self._UpdateTransformPos()
        return budget

    def _UpdateTransformPos(self):
        self.transform.width = self.mainCont.width * self.scale
        self.transform.height = self.mainCont.height * self.scale
        minLeft, maxLeft, minTop, maxTop = self._GetPanningConstraints()
        diff = minTop - maxTop
        self.transform.top = maxTop + diff * self._panTop
        diff = minLeft - maxLeft
        self.transform.left = maxLeft + diff * self._panLeft
        if self.callback:
            self.callback()

    def _GetPanningConstraints(self):
        width, height = self.transform.width, self.transform.height
        parWidth, parHeight = self.GetAbsoluteSize()
        bLeft, bTop, bRight, bBottom = self.border
        if self.IsClampedHorizontally(includeMargin=False):
            minLeft = maxLeft = (bRight - bLeft + parWidth - width) / 2
        else:
            minLeft = parWidth - width - bLeft
            maxLeft = bRight
        if self.IsClampedVertically(includeMargin=False):
            minTop = maxTop = (bBottom - bTop + parHeight - height) / 2
        else:
            minTop = parHeight - height - bTop
            maxTop = bBottom
        return (minLeft,
         maxLeft,
         minTop,
         maxTop)

    def SetBorder(self, border):
        if isinstance(border, int):
            self._border = (border,
             border,
             border,
             border)
        else:
            self._border = border
        self.FlagAlignmentDirty()

    def GetBorder(self):
        return self._border

    border = property(GetBorder, SetBorder)
