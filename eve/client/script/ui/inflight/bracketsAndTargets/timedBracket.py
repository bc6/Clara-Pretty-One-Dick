#Embedded file name: eve/client/script/ui/inflight/bracketsAndTargets\timedBracket.py
from eve.client.script.ui.inflight.bracketsAndTargets.inSpaceBracket import InSpaceBracket
import blue
from uiprimitives import Container, Fill
from uicontrols import Frame
import carbonui.const as uiconst

class TimedBracket(InSpaceBracket):

    def ApplyAttributes(self, attributes):
        InSpaceBracket.ApplyAttributes(self, attributes)
        self.width = self.height = 32
        container = Container(parent=self, align=uiconst.CENTER, top=12, height=30, width=64)
        self.timer = Timer(parent=container, align=uiconst.TOTOP, height=12, state=uiconst.UI_HIDDEN)

    def Startup(self, slimItem, ball = None, transform = None):
        InSpaceBracket.Startup(self, slimItem, ball=ball, transform=transform)
        self.SetUnlocking(slimItem)

    def Animate(self, startProportion, duration):
        self.timer.state = uiconst.UI_NORMAL
        self.timer.Animate(startProportion, float(duration))

    def OnSlimItemChange(self, oldSlim, newSlim):
        self.SetUnlocking(newSlim)

    def SetUnlocking(self, slimItem):
        if slimItem.timerInfo is not None:
            startProportion, duration = self.GetAnimationInfo(*slimItem.timerInfo)
            self.Animate(startProportion, duration)

    def GetAnimationInfo(self, startTime, duration):
        durationInBlueTime = duration * const.SEC
        endTime = startTime + durationInBlueTime
        currentTime = blue.os.GetSimTime()
        if endTime < currentTime:
            return (1.0, duration)
        startProportion = (currentTime - startTime) / durationInBlueTime
        return (startProportion, duration)


class Timer(Container):

    def ApplyAttributes(self, attributes):
        super(Timer, self).ApplyAttributes(attributes)
        self.frame = Frame(parent=self)
        self.fill = Fill(parent=self, align=uiconst.TOLEFT_PROP, width=0, padding=(2, 2, 2, 2))

    def Animate(self, startProportion, duration):
        self.fill.width = startProportion
        uicore.animations.MorphScalar(self.fill, 'width', startVal=float(startProportion), endVal=1.0, duration=duration, loops=1, curveType=uiconst.ANIM_LINEAR)
