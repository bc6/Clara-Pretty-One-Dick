#Embedded file name: eve/client/script/ui/crimewatch\duelInviteWindow.py
from eve.client.script.ui.shared.stateFlag import FlagIconWithState
import uicls
import carbonui.const as uiconst
import uiprimitives
import uicontrols
import uiutil
import localization
import util
import uthread
import blue
from crimewatchConst import Colors

class DuelInviteWindow(uicontrols.Window):
    __guid__ = 'uicls.DuelInviteWindow'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        self.charID = attributes.charID
        self.corpID = attributes.corpID
        self.allianceID = attributes.allianceID
        self.info = cfg.eveowners.Get(self.charID)
        self.result = set()
        self.SetCaption(localization.GetByLabel('UI/Crimewatch/Duel/InvitationWindowCaption'))
        self.SetMinSize([400, 222])
        self.MakeUnResizeable()
        self.MakeUnKillable()
        self.MakeUnpinable()
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.ConstructLayout()

    def ConstructLayout(self):
        invitorCont = uiprimitives.Container(name='invitorCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 70), padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         0), state=uiconst.UI_PICKCHILDREN)
        challangerImgCont = uiprimitives.Container(name='challangerImgCont', parent=invitorCont, align=uiconst.TOLEFT, pos=(0, 0, 64, 0), padding=(0,
         0,
         const.defaultPadding,
         0), state=uiconst.UI_PICKCHILDREN)
        challangerCont = uiprimitives.Container(name='challangerCont', parent=invitorCont, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         0,
         0,
         0))
        uiutil.GetOwnerLogo(challangerImgCont, self.charID, size=64, noServerCall=True)
        stateFlag = FlagIconWithState(parent=challangerImgCont, align=uiconst.BOTTOMRIGHT, left=4, top=10)
        labels = [uicontrols.EveLabelMedium(name='charNameLabel', text=localization.GetByLabel('UI/Common/Name'), parent=challangerCont, left=0, top=0, align=uiconst.TOPLEFT, width=60, state=uiconst.UI_NORMAL, idx=0), uicontrols.EveLabelMedium(name='corpNameLabel', text=localization.GetByLabel('UI/Common/Corporation'), parent=challangerCont, left=0, top=21, align=uiconst.TOPLEFT, width=270, state=uiconst.UI_NORMAL, idx=0)]
        if self.allianceID is not None:
            labels.append(uicontrols.EveLabelMedium(name='allianceNameLabel', text=localization.GetByLabel('UI/Common/Alliance'), parent=challangerCont, left=0, top=42, align=uiconst.TOPLEFT, width=270, state=uiconst.UI_NORMAL, idx=0))
        labelLength = max((l.textwidth for l in labels)) + 2 * const.defaultPadding
        uicontrols.EveLabelMedium(name='charName', text=util.FmtOwnerLink(self.charID), parent=challangerCont, left=labelLength, top=0, align=uiconst.TOPLEFT, width=270, state=uiconst.UI_NORMAL, idx=0)
        uicontrols.EveLabelMedium(name='corpName', text=util.FmtOwnerLink(self.corpID), parent=challangerCont, left=labelLength, top=21, align=uiconst.TOPLEFT, width=270, state=uiconst.UI_NORMAL, idx=0)
        if self.allianceID is not None:
            uicontrols.EveLabelMedium(name='allianceName', text=util.FmtOwnerLink(self.allianceID) if self.allianceID else '', parent=challangerCont, left=labelLength, top=42, align=uiconst.TOPLEFT, width=270, state=uiconst.UI_NORMAL, idx=0)
        uiprimitives.Sprite(name='logo', parent=invitorCont, texturePath='res:/UI/Texture/Crimewatch/Crimewatch_LimitedEngagement_64.png', width=64, height=64, align=uiconst.TOPRIGHT, padding=(0,
         0,
         const.defaultPadding,
         0))
        bodyTextCont = uiprimitives.Container(name='bodyTextCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 30), padding=(const.defaultPadding,
         const.defaultPadding * 2,
         const.defaultPadding,
         0), state=uiconst.UI_PICKCHILDREN)
        box = uiprimitives.Container(parent=bodyTextCont, name='frame', align=uiconst.TOLEFT, width=64, height=64, padding=(const.defaultPadding,
         const.defaultPadding * 3,
         const.defaultPadding,
         const.defaultPadding * 3))
        self.time = uicontrols.Label(parent=box, name='counter', text='60', fontsize=32, bold=False, align=uiconst.CENTERRIGHT, color=Colors.Engagement.GetRGBA(), left=15)
        captionCont = uiprimitives.Container(name='captionCont', parent=bodyTextCont, align=uiconst.TOALL, pos=(0, 0, 0, 0))
        l = uicontrols.EveLabelSmall(name='charName', text=localization.GetByLabel('UI/Crimewatch/Duel/DuelDecleration'), parent=captionCont, left=0, top=0, align=uiconst.TOALL, state=uiconst.UI_NORMAL)
        bodyTextCont.height = max(64, l.textheight)
        controlsCont = uiprimitives.Container(name='controlsCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0,
         0,
         0,
         20 + const.defaultPadding), padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         0))
        self.blockOption = uicontrols.Checkbox(text=localization.GetByLabel('UI/Crimewatch/Duel/BlockCommunications'), parent=controlsCont, configName='block', retval=1, checked=0, groupname=None, pos=(const.defaultPadding,
         0,
         300,
         0), align=uiconst.TOPLEFT)
        self.btnGroup = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Crimewatch/Duel/Accept'),
          self.Confirm,
          (),
          81,
          1,
          0,
          0], [localization.GetByLabel('UI/Crimewatch/Duel/Decline'),
          self.Decline,
          (),
          81,
          1,
          1,
          0]], parent=self.sr.main, align=uiconst.TOTOP)
        self.SetHeight(sum((c.height for c in self.sr.main.children)) + 40)
        uicore.registry.SetFocus(self.btnGroup.children[0])
        icon = challangerImgCont.children[0]
        icon.isDragObject = True
        icon.GetDragData = self.CharGetDragData
        icon.OnClick = self.CharOnClick
        slimItem = sm.GetService('crimewatchSvc').GetSlimItemDataForCharID(self.charID)
        if slimItem is not None:
            stateSvc = sm.GetService('state')
            flagCode = stateSvc.CheckFilteredFlagState(slimItem)
            flagInfo = stateSvc.GetStatePropsColorAndBlink(flagCode)
            stateFlag.ModifyIcon(flagInfo=flagInfo)

    def StartTimeout(self, expiryTime):
        self.expiryThread = uthread.new(self._DoTimeout, expiryTime)

    def _DoTimeout(self, expiryTime):
        timeout = expiryTime - blue.os.GetWallclockTimeNow()
        while timeout > 0:
            blue.pyos.synchro.SleepWallclock(100)
            timeout = expiryTime - blue.os.GetWallclockTimeNow()
            self.time.text = str(max(0, int(timeout / float(const.SEC))))

        if not self or self.destroyed:
            return
        self.SetModalResult(uiconst.OK)
        self.time.SetTextColor(util.Color.RED)
        for btn in self.btnGroup.subpar.children:
            btn.Disable()

        blue.pyos.synchro.SleepWallclock(2000)
        self.Close()

    def CharGetDragData(self, *args):
        if self and not self.destroyed:
            fakeNode = util.KeyVal()
            fakeNode.charID = self.charID
            fakeNode.typeID = self.info.typeID
            fakeNode.info = self.info
            fakeNode.itemID = self.charID
            fakeNode.__guid__ = 'listentry.User'
            return [fakeNode]
        else:
            return []

    def CharOnClick(self, *args):
        sm.GetService('info').ShowInfo(typeID=self.info.typeID, itemID=self.charID)

    def Confirm(self, *args):
        self.result = {'accept'}
        if self.blockOption.checked:
            self.result.add('block')
        self.SetModalResult(uiconst.OK)

    def Decline(self, *args):
        self.result = {'decline'}
        if self.blockOption.checked:
            self.result.add('block')
        self.SetModalResult(uiconst.OK)
