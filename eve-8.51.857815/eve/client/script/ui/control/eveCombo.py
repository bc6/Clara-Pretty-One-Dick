#Embedded file name: eve/client/script/ui/control\eveCombo.py
from carbonui.control.basicDynamicScroll import Scroll
from carbonui.control.combo import ComboCore
from carbonui.control.menu import ClearMenuLayer
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveLabel import EveLabelMedium
from eve.client.script.ui.control.eveWindowUnderlay import RaisedUnderlay, LabelUnderlay, FillUnderlay, BumpedUnderlay
import carbonui.const as uiconst
import uiprimitives
from eve.client.script.ui import eveFontConst
import trinity

class Combo(ComboCore):
    __guid__ = 'uicontrols.Combo'
    default_fontsize = eveFontConst.EVE_MEDIUM_FONTSIZE
    default_labelleft = None
    default_align = uiconst.TOPLEFT
    default_width = 86
    default_height = 18

    def ApplyAttributes(self, attributes):
        self.labelleft = attributes.get('labelleft', self.default_labelleft)
        ComboCore.ApplyAttributes(self, attributes)
        self.sr.expander.LoadIcon('ui_38_16_229')
        self.sr.expander.opacity = 0.8
        self.sr.expander.top = 0
        self.sr.expander.left = -1

    def SetLabel_(self, label):
        if self.labelleft is not None:
            self.padLeft = self.labelleft
            self.sr.label.left = -self.labelleft
            self.sr.label.width = self.labelleft - 6
        if label:
            self.sr.label.text = label
            self.glowLabel.text = label
            if self.labelleft is not None:
                self.sr.label.top = 0
                self.sr.label.SetAlign(uiconst.CENTERLEFT)
            else:
                self.sr.label.top = -self.sr.label.textheight
            self.sr.label.state = uiconst.UI_DISABLED
        else:
            self.sr.label.state = uiconst.UI_HIDDEN

    def Prepare_SelectedText_(self):
        self.sr.selected = LabelUnderlay(text='', parent=self.sr.textclipper, name='value', align=uiconst.CENTERLEFT, left=3, state=uiconst.UI_DISABLED)
        self.glowLabel = LabelUnderlay(parent=self.sr.textclipper, state=uiconst.UI_DISABLED, align=uiconst.CENTERLEFT, left=3, opacity=0.0)
        self.glowLabel.renderObject.spriteEffect = trinity.TR2_SFX_BLUR

    def Prepare_Underlay_(self):
        self.sr.backgroundFrame = RaisedUnderlay(parent=self)

    def Prepare_Label_(self):
        self.sr.label = EveLabelSmall(text='', parent=self, name='label', top=-13, left=1, state=uiconst.UI_HIDDEN, idx=1)

    def Prepare_OptionMenu_(self):
        ClearMenuLayer()
        menu = uiprimitives.Container(parent=uicore.layer.menu, pos=(0, 0, 200, 200), align=uiconst.RELATIVE)
        menu.sr.scroll = Scroll(parent=menu)
        menu.sr.scroll.OnKillFocus = self.OnScrollFocusLost
        menu.sr.scroll.OnSelectionChange = self.OnScrollSelectionChange
        menu.sr.scroll.Confirm = self.Confirm
        menu.sr.scroll.OnUp = self.OnUp
        menu.sr.scroll.OnDown = self.OnDown
        menu.sr.scroll.OnRight = self.Confirm
        menu.sr.scroll.OnLeft = self.Confirm
        menu.sr.scroll.sr.underlay.opacity = 0.0
        BumpedUnderlay(bgParent=menu, opacity=1.0, isInFocus=True, isWindowActive=True)
        FillUnderlay(bgParent=menu, colorType=uiconst.COLORTYPE_UIBASECONTRAST, opacity=1.0)
        return (menu, menu.sr.scroll)

    def GetEntryClass(self):
        from eve.client.script.ui.control.entries import ComboEntry
        return ComboEntry

    def Startup(self, *args):
        pass


from carbonui.control.combo import ComboCoreOverride
ComboCoreOverride.__bases__ = (Combo,)
