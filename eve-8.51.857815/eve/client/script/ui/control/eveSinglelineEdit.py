#Embedded file name: eve/client/script/ui/control\eveSinglelineEdit.py
from carbon.common.script.util.timerstuff import AutoTimer
from carbonui.control.singlelineedit import SinglelineEditCore
from eve.client.script.ui.control.eveLabel import EveLabelSmall
from eve.client.script.ui.control.eveLabel import Label
from eve.client.script.ui.control.eveWindowUnderlay import BumpedUnderlay
from eve.client.script.ui.control.eveBaseLink import GetCharIDFromTextLink
import carbonui.const as uiconst
from eve.client.script.ui.control.tooltips import TooltipGeneric
import localization
import util
import uiutil
import trinity

class SinglelineEdit(SinglelineEditCore):
    """ Standard single-line text edit """
    __guid__ = 'uicontrols.SinglelineEdit'
    default_left = 0
    default_top = 2
    default_width = 80
    default_height = 18
    default_align = uiconst.TOPLEFT
    capsWarning = None
    capsLockUpdateThread = None

    def ApplyAttributes(self, attributes):
        SinglelineEditCore.ApplyAttributes(self, attributes)
        self.displayHistory = True
        if self.GetAlign() == uiconst.TOALL:
            self.height = 0
        else:
            self.height = self.default_height
        self.isTypeField = attributes.isTypeField
        self.isCharacterField = attributes.isCharacterField

    def Close(self):
        if self.capsWarning:
            self.capsWarning.Close()
        self.capsLockUpdateThread = None
        SinglelineEditCore.Close(self)

    def SetPasswordChar(self, char):
        SinglelineEditCore.SetPasswordChar(self, char)
        if self.passwordchar:
            self.capsWarning = TooltipGeneric(parent=uicore.layer.hint, idx=0, opacity=0.0)
            self.capsWarning.defaultPointer = uiconst.POINT_LEFT_2
            self.capsLockUpdateThread = AutoTimer(1, self.UpdateCapsState)
        else:
            self.capsLockUpdateThread = None

    def Prepare_(self):
        self.sr.text = Label(name='edittext', parent=self._textClipper, left=self.TEXTLEFTMARGIN, state=uiconst.UI_DISABLED, maxLines=1, align=uiconst.CENTERLEFT, fontsize=self.fontsize)
        self.sr.hinttext = Label(parent=self._textClipper, name='hinttext', align=uiconst.CENTERLEFT, state=uiconst.UI_DISABLED, maxLines=1, left=self.TEXTLEFTMARGIN, fontsize=self.fontsize)
        self.sr.background = BumpedUnderlay(bgParent=self, showFill=True)

    def SetLabel(self, text):
        self.sr.label = EveLabelSmall(parent=self, name='__caption', text=text, state=uiconst.UI_DISABLED, align=uiconst.TOPLEFT, idx=0)
        self.sr.label.top = -self.sr.label.textheight
        if self.adjustWidth:
            self.width = max(self.width, self.sr.label.textwidth)

    def OnDropData(self, dragObj, nodes):
        SinglelineEditCore.OnDropData(self, dragObj, nodes)
        if self.isTypeField:
            self.OnDropType(dragObj, nodes)
        if self.isCharacterField:
            self.OnDropCharacter(dragObj, nodes)

    def OnDropType(self, dragObj, nodes):
        node = nodes[0]
        guid = node.Get('__guid__', None)
        typeID = None
        if guid in ('xtriui.ShipUIModule', 'xtriui.InvItem', 'listentry.InvItem', 'listentry.InvAssetItem'):
            typeID = getattr(node.item, 'typeID', None)
        elif guid in ('listentry.GenericMarketItem', 'listentry.QuickbarItem'):
            typeID = getattr(node, 'typeID', None)
        if typeID:
            typeName = cfg.invtypes.Get(typeID).name
            self.SetValue(typeName)

    def OnDropCharacter(self, dragObj, nodes):
        node = nodes[0]
        if node.Get('__guid__', None) not in uiutil.AllUserEntries() + ['TextLink']:
            return
        charID = GetCharIDFromTextLink(node)
        if charID is None:
            charID = node.charID
        if util.IsCharacter(charID):
            charName = cfg.eveowners.Get(charID).name
            self.SetValue(charName)

    def UpdateCapsState(self):
        """
        Checks caps lock and updates the caps warning
        """
        if not self.capsWarning or self.capsWarning.destroyed or self.destroyed:
            self.capsLockUpdateThread = None
            return
        if self.passwordchar is not None:
            if trinity.app.GetKeyState(uiconst.VK_CAPITAL) == True and self is uicore.registry.GetFocus():
                if self.capsWarning:
                    if self.capsWarning.opacity == 0.0:
                        self.capsWarning.opacity = 1.0
                    self.capsWarning.display = True
                    self.capsWarning.SetTooltipString(localization.GetByLabel('/Carbon/UI/Common/CapsLockWarning'), self)
            else:
                self.capsWarning.display = False


from carbonui.control.singlelineedit import SinglelineEditCoreOverride
SinglelineEditCoreOverride.__bases__ = (SinglelineEdit,)
