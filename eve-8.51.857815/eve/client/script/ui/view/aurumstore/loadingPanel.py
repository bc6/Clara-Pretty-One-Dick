#Embedded file name: eve/client/script/ui/view/aurumstore\loadingPanel.py
from carbonui.primitives.container import Container
from carbonui.primitives.sprite import Sprite
from carbonui.util.color import Color
import carbonui.const as uiconst
from eve.client.script.ui.control.eveLoadingWheel import LoadingWheel
from eve.client.script.ui.view.aurumstore.vgsUiPrimitives import VgsLabelMedium, ExitButton
import localization

class LoadingPanel(Container):
    default_name = 'StoreLoadingPanel'
    default_state = uiconst.UI_NORMAL
    default_bgColor = Color.BLACK
    default_align = uiconst.TOALL

    def ApplyAttributes(self, attributes):
        super(LoadingPanel, self).ApplyAttributes(attributes)
        self.enableClickToClose = False
        self.logo = Sprite(parent=self, align=uiconst.CENTER, texturePath='res:/UI/Texture/vgs/huge-NES-logo.png', top=-108, width=521, height=216, state=uiconst.UI_DISABLED)
        bottomContainer = Container(parent=self, align=uiconst.TOBOTTOM_PROP, height=0.25)
        self.loadingWheel = LoadingWheel(parent=bottomContainer, align=uiconst.CENTERTOP, width=100, height=100)
        self.statusLabel = VgsLabelMedium(parent=bottomContainer, align=uiconst.CENTERTOP, text=localization.GetByLabel('UI/VirtualGoodsStore/LoadingStoreData'), top=80)
        ExitButton(parent=self, align=uiconst.TOPRIGHT, onClick=self.Shutdown, top=4, left=4, hint=localization.GetByLabel('UI/VirtualGoodsStore/ExitStore'))

    def Shutdown(self):
        uicore.cmd.ToggleAurumStore()
        self.Close()

    def OnClick(self):
        if self.enableClickToClose:
            self.Shutdown()

    def ShowStoreUnavailable(self, message = None):
        self.enableClickToClose = True
        uicore.animations.FadeTo(self.logo, startVal=self.logo.opacity, endVal=0.25, duration=1, timeOffset=0.5)
        uicore.animations.FadeOut(self.loadingWheel, duration=1)
        if message:
            self.statusLabel.text = message
        else:
            self.statusLabel.text = localization.GetByLabel('UI/VirtualGoodsStore/StoreUnavailable')
