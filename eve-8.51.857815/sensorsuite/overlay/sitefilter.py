#Embedded file name: sensorsuite/overlay\sitefilter.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.uianimations import animations
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from audioConst import BTNCLICK_DEFAULT
from eve.client.script.ui.util.uiComponents import HoverEffect, Component
from eve.common.lib.appConst import defaultPadding
import localization
import logging
logger = logging.getLogger(__name__)

@Component(HoverEffect(color=(1.0, 1.0, 1.0, 0.15)))

class SiteButton(Container):
    default_height = 20
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    opacityIdleIcon = 0.0
    opacityMouseDownIcon = 1.0
    opacityIdleLabel = 0.4
    opacityMouseDownLabel = 1.0
    exitDuration = 0.3

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.sensorSuite = sm.GetService('sensorSuite')
        config = attributes.filterConfig
        iconCont = Container(parent=self, width=24, height=24, align=uiconst.TOLEFT, padding=(2, 2, 0, 2), state=uiconst.UI_DISABLED)
        self.icon = Sprite(parent=iconCont, width=16, height=16, texturePath=config.iconPath, color=config.color)
        Sprite(parent=iconCont, width=16, height=16, texturePath=config.iconPath, opacity=0.5)
        textCont = Container(parent=self, align=uiconst.TOALL)
        self.label = EveLabelMedium(parent=textCont, align=uiconst.CENTERLEFT, text=localization.GetByLabel(config.label))
        self.width = iconCont.width + iconCont.padLeft + iconCont.padRight + self.label.textwidth + defaultPadding
        self.config = config
        self.isActive = attributes.isActive
        if self.isActive:
            self.icon.opacity = self.opacityMouseDownIcon
            self.label.opacity = self.opacityMouseDownLabel
        else:
            self.icon.opacity = self.opacityIdleIcon
            self.label.opacity = self.opacityIdleLabel

    def OnClick(self, *args):
        self.Toggle()
        sm.GetService('audio').SendUIEvent(BTNCLICK_DEFAULT)

    def SetActive(self, isActive):
        self.isActive = isActive
        if self.isActive:
            animations.FadeTo(self.icon, self.icon.opacity, self.opacityMouseDownIcon, duration=0.1)
            animations.FadeTo(self.label, self.label.opacity, self.opacityMouseDownLabel, duration=0.1)
        else:
            animations.FadeTo(self.icon, self.icon.opacity, self.opacityIdleIcon, duration=self.exitDuration)
            animations.FadeTo(self.label, self.label.opacity, self.opacityIdleLabel, duration=self.exitDuration)
        self.sensorSuite.SetSiteFilter(self.config.siteType, self.isActive)

    def Toggle(self):
        self.SetActive(not self.isActive)
