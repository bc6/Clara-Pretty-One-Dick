#Embedded file name: eve/client/script/ui/shared/infoPanels\infoPanelControls.py
from carbonui.fontconst import STYLE_DEFAULT
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from carbonui.primitives.frame import Frame
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.eveFontConst import EVE_SMALL_FONTSIZE
from eve.client.script.ui.login.charcreation.ccConst import FRAME_SOFTSHADE
import carbonui.const as uiconst
import trinity

class InfoPanelHeaderBackground(Container):
    BGCOLOR = (1, 1, 1, 0.15)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.colorFill = Fill(bgParent=self, color=attributes.color or self.BGCOLOR)
        self.shadow = Frame(bgParent=self, frameConst=FRAME_SOFTSHADE, color=(0, 0, 0, 0.25), padding=(-10, -10, -10, -10))

    def SetBackgroundColor(self, *color):
        self.colorFill.SetRGBA(*color)


class InfoPanelLabel(Container):
    displayText = None
    default_fontsize = EVE_SMALL_FONTSIZE
    default_fontStyle = STYLE_DEFAULT
    default_color = (1.0, 1.0, 1.0, 0.8)

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.mainLabel = Label(parent=self, state=uiconst.UI_DISABLED, color=attributes.color or self.default_color, fontsize=attributes.fontsize or self.default_fontsize, fontStyle=attributes.fontStyle or self.default_fontStyle, bold=attributes.bold or False)
        self.mainShadowLabel = Label(parent=self, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, color=(0, 0, 0, 0.75), fontsize=attributes.fontsize or self.default_fontsize, fontStyle=attributes.fontStyle or self.default_fontStyle, bold=attributes.bold or False)
        self.mainShadowLabel.renderObject.spriteEffect = trinity.TR2_SFX_BLUR
        self.text = attributes.text

    @apply
    def text():

        def fset(self, value):
            self.mainLabel.text = value
            self.mainShadowLabel.text = value
            self.width = self.mainLabel.width
            self.height = self.mainLabel.height

        def fget(self):
            return self.mainLabel.text

        return property(**locals())

    @apply
    def textwidth():

        def fset(self, value):
            pass

        def fget(self):
            return self.mainLabel.textwidth

        return property(**locals())

    @apply
    def textheight():

        def fset(self, value):
            pass

        def fget(self):
            return self.mainLabel.textheight

        return property(**locals())

    @apply
    def fontsize():

        def fset(self, value):
            self.mainLabel.fontsize = value
            self.mainShadowLabel.fontsize = value

        def fget(self):
            return self.mainLabel.fontsize

        return property(**locals())

    def SetAlpha(self, alpha):
        self.mainLabel.SetAlpha(alpha)
        self.mainShadowLabel.SetAlpha(alpha)
