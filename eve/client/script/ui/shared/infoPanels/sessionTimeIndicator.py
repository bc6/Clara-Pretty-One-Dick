#Embedded file name: eve/client/script/ui/shared/infoPanels\sessionTimeIndicator.py
import uicls
import carbonui.const as uiconst
import math
import blue
import uiprimitives
import uicontrols
import util
import localization

class SessionTimeIndicator(uiprimitives.Container):
    """ Circular control that displays the progress of the session change timer """
    __guid__ = 'uicls.SessionTimeIndicator'

    def ApplyAttributes(self, attributes):
        uiprimitives.Container.ApplyAttributes(self, attributes)
        size = 24
        self.ramps = uiprimitives.Container(parent=self, name='ramps', pos=(0,
         0,
         size,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        leftRampCont = uiprimitives.Container(parent=self.ramps, name='leftRampCont', pos=(0,
         0,
         size / 2,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.leftRamp = uiprimitives.Transform(parent=leftRampCont, name='leftRamp', pos=(0,
         0,
         size,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        uiprimitives.Sprite(parent=self.leftRamp, name='rampSprite', pos=(0,
         0,
         size / 2,
         size), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/TiDiIndicator/left.png', color=(0, 0, 0, 0.5))
        rightRampCont = uiprimitives.Container(parent=self.ramps, name='rightRampCont', pos=(0,
         0,
         size / 2,
         size), align=uiconst.TOPRIGHT, state=uiconst.UI_DISABLED, clipChildren=True)
        self.rightRamp = uiprimitives.Transform(parent=rightRampCont, name='rightRamp', pos=(-size / 2,
         0,
         size,
         size), align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
        uiprimitives.Sprite(parent=self.rightRamp, name='rampSprite', pos=(size / 2,
         0,
         size / 2,
         size), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/TiDiIndicator/right.png', color=(0, 0, 0, 0.5))
        self.coloredPie = uiprimitives.Sprite(parent=self, name='tidiColoredPie', pos=(0,
         0,
         size,
         size), texturePath='res:/UI/Texture/classes/TiDiIndicator/circle.png', state=uiconst.UI_DISABLED, color=(1, 1, 1, 0.5))

    def AnimSessionChange(self):
        duration = session.nextSessionChange - blue.os.GetSimTime()
        while blue.os.GetSimTime() < session.nextSessionChange:
            timeDiff = session.nextSessionChange - blue.os.GetSimTime()
            progress = timeDiff / float(duration)
            self.SetProgress(1.0 - progress)
            timeLeft = util.FmtTimeInterval(timeDiff, breakAt='sec')
            self.hint = localization.GetByLabel('UI/Neocom/SessionChangeHint', timeLeft=timeLeft)
            self.state = uiconst.UI_NORMAL
            blue.pyos.synchro.Yield()

        self.SetProgress(1.0)
        self.state = uiconst.UI_HIDDEN

    def SetProgress(self, progress):
        progress = max(0.0, min(1.0, progress))
        leftRamp = min(1.0, max(0.0, progress * 2))
        rightRamp = min(1.0, max(0.0, progress * 2 - 1.0))
        self.leftRamp.SetRotation(math.pi + math.pi * leftRamp)
        self.rightRamp.SetRotation(math.pi + math.pi * rightRamp)
