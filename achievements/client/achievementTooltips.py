#Embedded file name: achievements/client\achievementTooltips.py
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveLabel import EveLabelSmall, EveLabelMediumBold, EveLabelMedium, Label
import carbonui.const as uiconst

class SectionHeader(Container):
    default_height = 20

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.isOpen = True
        headerText = attributes.headerText
        self.toggleFunc = attributes.toggleFunc
        self.arrowSprite = Sprite(name='arrow', parent=self, pos=(0, 0, 16, 16), texturePath='res:/UI/Texture/Icons/38_16_229.png', state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT)
        self.tipsHeader = EveLabelMediumBold(name='tipsHeader', text=headerText, parent=self, left=16, align=uiconst.CENTERLEFT)

    def OnClick(self, *args):
        if self.isOpen:
            self.arrowSprite.SetTexturePath('res:/UI/Texture/Icons/38_16_228.png')
        else:
            self.arrowSprite.SetTexturePath('res:/UI/Texture/Icons/38_16_229.png')
        self.isOpen = not self.isOpen
        self.toggleFunc(self)


class ExtraInfoEntry(Container):
    default_padLeft = 30
    default_padRight = 30
    default_padTop = 6

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        info = attributes.info
        self.icon = Sprite(name='arrow', parent=self, pos=(0,
         0,
         info['size'],
         info['size']), texturePath=info['path'], state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT)
        self.text = EveLabelSmall(name='tipsHeader', text=info['text'], parent=self, left=info['size'] + 2, top=1, align=uiconst.TOPLEFT)
        iconColor = info.get('color', None)
        if iconColor:
            self.icon.SetRGB(*iconColor)

    def UpdateAlignment(self, *args, **kwds):
        retVal = Container.UpdateAlignment(self, *args, **kwds)
        if getattr(self, 'icon', None) and getattr(self, 'text', None):
            newHeight = max(self.icon.height + 2 * self.icon.top, self.text.textheight + 2 * self.text.padTop)
            self.height = newHeight
        return retVal
