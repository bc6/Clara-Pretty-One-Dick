#Embedded file name: eve/client/script/ui/podGuide\megaMenuEntries.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from carbonui.primitives.fill import Fill
from eve.client.script.ui.control.eveLabel import EveLabelLarge, EveLabelSmall

class MegaMenuHeader(Container):
    default_align = uiconst.TOPLEFT
    default_height = 30
    sidePadding = 30

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        headerInfoDict = attributes.headerInfo
        text = headerInfoDict['groupName']
        textLabel = EveLabelLarge(parent=self, text=text, align=uiconst.CENTER)
        self.width = textLabel.textwidth + self.sidePadding


class MegaMenuEntry(Container):
    default_align = uiconst.TOPLEFT
    default_state = uiconst.UI_NORMAL
    default_height = 24
    sidePadding = 30

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.hiliteFill = Fill(bgParent=self, opacity=0.0)
        entryInfo = attributes.entryInfo
        self.callback = entryInfo['callback']
        self.callbackArgs = entryInfo['args']
        entryInfoDict = attributes.entryInfo
        text = entryInfoDict['text']
        self.textLabel = EveLabelSmall(parent=self, text=text, align=uiconst.CENTER)
        self.width = self.textLabel.textwidth + self.sidePadding
        self.height = max(self.default_height, self.textLabel.textheight + 4)

    def OnMouseEnter(self, *args):
        self.hiliteFill.opacity = 0.2
        self.textLabel.SetRGB(1, 0, 0, 1)

    def OnMouseExit(self, *args):
        self.hiliteFill.opacity = 0.0
        self.textLabel.SetRGB(1, 1, 1, 1)

    def OnClick(self, *args):
        if self.callback:
            self.callback(self.callbackArgs)
