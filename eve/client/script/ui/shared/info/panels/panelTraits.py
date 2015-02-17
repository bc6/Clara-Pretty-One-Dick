#Embedded file name: eve/client/script/ui/shared/info/panels\panelTraits.py
from carbonui.control.scrollContainer import ScrollContainer
from eve.client.script.ui.shared.traits import HasTraits, TraitsContainer

class PanelTraits(ScrollContainer):
    default_name = 'PanelTraits'
    default_padLeft = 4
    default_padTop = 4
    default_padRight = 4
    default_padBottom = 4
    default_showUnderlay = True

    def ApplyAttributes(self, attributes):
        ScrollContainer.ApplyAttributes(self, attributes)
        self.initialized = False
        self.typeID = attributes.typeID

    def Load(self):
        if self.initialized:
            return
        self.initialized = True
        TraitsContainer(parent=self, typeID=self.typeID, padding=7, traitAttributeIcons=True)

    @classmethod
    def TraitsVisible(cls, typeID):
        return HasTraits(typeID)
