#Embedded file name: notifications/client/controls\badgeContainer.py
import blue
import uthread
import carbonui.const as uiconst
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.pointerPanel import FRAME_WITH_POINTER_SKIN_BADGE
from eve.client.script.ui.control.pointerPanel import FrameWithPointer
from carbonui.primitives.container import Container

class BadgeContainer(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes=attributes)
        self.badgeLabel = EveLabelMedium(name='myLabel', parent=self, align=uiconst.CENTER, bold=True, text='1')
        self.width = self.badgeLabel.width + 10
        self.left = -self.badgeLabel.width - 20
        self.top = self.parent.height / 2 - self.parent.height / 2
        self.pointFromLeft = attributes.Get('pointfromleft', True)
        self.pointerframe = FrameWithPointer(bgParent=self, skinName=FRAME_WITH_POINTER_SKIN_BADGE)

    def updateBadgePointerPosition(self):
        if self.pointFromLeft:
            positionFlag = uiconst.POINT_RIGHT_2
        else:
            positionFlag = uiconst.POINT_LEFT_2
        self.pointerframe.UpdatePointerPosition(positionFlag=positionFlag)

    def ShowBadge(self):
        if self.opacity < 1:
            uicore.animations.FadeIn(self, duration=0.25, callback=None)

    def UpdateAlignment(self, *args, **kwds):
        retval = Container.UpdateAlignment(self, *args, **kwds)
        self.updateBadgePointerPosition()
        return retval

    def SetBadgeValue(self, value):
        self.badgeLabel.SetText(str(value))
        self.width = self.badgeLabel.width + 10
        self.left = -self.badgeLabel.width - 20
        uthread.new(self.updateBadgePointerPosition)

    def HideBadge(self):
        uicore.animations.FadeOut(self, duration=0.25, callback=None)
