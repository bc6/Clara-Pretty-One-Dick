#Embedded file name: carbonui/primitives\bracket.py
from carbonui.primitives.frame import Frame
from .container import Container
from .base import Base, ScaleDpi
import carbonui.const as uiconst
import trinity

class Bracket(Container):
    """
    A UI container that has it's position dictated by the projection of the position of 
    an object in the 3d scene onto the camera plane
    """
    __guid__ = 'uiprimitives.Bracket'
    default_name = 'bracket'
    default_align = uiconst.NOALIGN
    projectBracket = None

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.renderObject.displayHeight = ScaleDpi(attributes.Get('width', self.default_width))
        self.renderObject.displayWidth = ScaleDpi(attributes.Get('height', self.default_height))
        self.projectBracket = trinity.EveProjectBracket()
        self.projectBracket.bracket = self.renderObject
        curveSet = attributes.get('curveSet', uicore.uilib.bracketCurveSet)
        curveSet.curves.append(self.projectBracket)

    def Close(self):
        Container.Close(self)
        uicore.uilib.bracketCurveSet.curves.fremove(self.projectBracket)
        self.projectBracket = None

    @apply
    def name():
        doc = 'Name of the bracket'
        fget = Container.name.fget

        def fset(self, name):
            Container.name.fset(self, name)
            if self.projectBracket:
                self.projectBracket.name = unicode(name)

        return property(**locals())

    @apply
    def trackTransform():
        doc = 'The trinity.Tr2Transform that is supposed to dictate position of the bracket'

        def fget(self):
            if self.projectBracket:
                return self.projectBracket.trackTransform

        def fset(self, value):
            self.projectBracket.trackTransform = value

        return property(**locals())

    @apply
    def trackBall():
        doc = 'The destiny.Ball that is supposed to dictate position of the bracket'

        def fget(self):
            if self.projectBracket:
                return self.projectBracket.trackBall

        def fset(self, value):
            self.projectBracket.trackBall = value

        return property(**locals())

    @apply
    def ballTrackingScaling():
        doc = 'Scaling factor applied when using trackBall.'

        def fget(self):
            return self.projectBracket.ballTrackingScaling

        def fset(self, value):
            self.projectBracket.ballTrackingScaling = value

        return property(**locals())

    @apply
    def dock():
        doc = "If True, the bracket will dock to the side of it's parent container when the \n        projection is out of scope. If False, the bracket will disappear."

        def fget(self):
            return self.projectBracket.dock

        def fset(self, value):
            if not self.destroyed:
                self.projectBracket.dock = value

        return property(**locals())

    @apply
    def left():
        doc = 'The x-coordinate of the bracket.'

        def fget(self):
            return uicore.ReverseScaleDpi(self.renderObject.displayX)

        def fset(self, value):
            if value != self._left:
                self._left = value
                self.renderObject.displayX = value

        return property(**locals())

    @apply
    def top():
        doc = 'The y-coordinate of the bracket.'

        def fget(self):
            return uicore.ReverseScaleDpi(self.renderObject.displayY)

        def fset(self, value):
            if value != self._top:
                self._top = value
                self.renderObject.displayY = value

        return property(**locals())

    @apply
    def minDispRange():
        doc = 'Bracket is hidden if the camera is closer to the object than this value'

        def fget(self):
            return self.projectBracket.minDispRange

        def fset(self, value):
            if self.destroyed:
                return
            self.projectBracket.minDispRange = value

        return property(**locals())

    @apply
    def maxDispRange():
        doc = 'Bracket is hidden if the camera is farther from the object than this value'

        def fget(self):
            return self.projectBracket.maxDispRange

        def fset(self, value):
            self.projectBracket.maxDispRange = value

        return property(**locals())
