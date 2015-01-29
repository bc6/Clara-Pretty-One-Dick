#Embedded file name: eve/client/script/ui/shared/fleet\storeFleetSetupWnd.py
"""
The UI code for the window that allows you to store your fleet settings
"""
import localization
import carbonui.const as uiconst
from eve.client.script.ui.control.eveWindow import Window
from eve.client.script.ui.control.eveSinglelineEdit import SinglelineEdit
from carbonui.primitives.container import Container
import uicontrols
import uiprimitives
import uicls
import uiutil

class StoreFleetSetupWnd(Window):
    default_width = 270
    default_height = 90
    default_minSize = (default_width, default_height)
    default_windowID = 'StoreFleetSetupWnd'

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.DefineButtons(uiconst.OKCANCEL, okFunc=self.Confirm, cancelFunc=self.Cancel)
        caption = localization.GetByLabel('UI/Fleet/FleetWindow/StoreFleetSetup')
        self.SetCaption(caption)
        self.SetTopparentHeight(0)
        self.MakeUnResizeable()
        oldSetupName = attributes.get('oldSetupName', None)
        self.maxLength = 15
        self.funcValidator = self.CheckName
        self.ConstructLayout(oldSetupName)

    def ConstructLayout(self, oldSetupName):
        cont = uicontrols.ContainerAutoSize(parent=self.sr.main, align=uiconst.TOTOP, padding=(const.defaultPadding,
         0,
         const.defaultPadding,
         const.defaultPadding), alignMode=uiconst.TOTOP)
        if oldSetupName:
            label = localization.GetByLabel('UI/Fleet/FleetWindow/StoreFleetSetupTextWithLastLoaded', oldFleetSetupName=oldSetupName)
        else:
            label = localization.GetByLabel('UI/Fleet/FleetWindow/StoreFleetSetupText')
        nameLabel = uicontrols.EveLabelSmall(parent=cont, name='nameLabel', align=uiconst.TOTOP, text=label, padLeft=6)
        self.newName = SinglelineEdit(name='namePopup', parent=cont, align=uiconst.TOTOP, maxLength=self.maxLength, OnReturn=self.Confirm, padLeft=6)
        motdText = localization.GetByLabel('UI/Fleet/FleetWindow/IncludeMotd')
        self.motdCb = uicontrols.Checkbox(text=motdText, parent=cont, configName='motdCb', checked=False, padLeft=6, align=uiconst.TOTOP)
        voiceText = localization.GetByLabel('UI/Fleet/FleetWindow/IncludeVoiceEnabledSetting')
        self.voiceCb = uicontrols.Checkbox(text=voiceText, parent=cont, configName='voiceCb', checked=False, padLeft=6, align=uiconst.TOTOP)
        freeMoveText = localization.GetByLabel('UI/Fleet/FleetWindow/IncludeFreeMoveSetting')
        self.freeMoveCb = uicontrols.Checkbox(text=freeMoveText, parent=cont, configName='freeMoveCb', checked=False, padLeft=6, align=uiconst.TOTOP)
        cw, ch = cont.GetAbsoluteSize()
        self.height = ch + 50
        uicore.registry.SetFocus(self.newName)

    def CheckName(self, name, *args):
        name = self.newName.GetValue()
        if not len(name) or len(name) and len(name.strip()) < 1:
            return localization.GetByLabel('UI/Common/PleaseTypeSomething')

    def Confirm(self, *args):
        newName = self.newName.GetValue()
        storeMotd = self.motdCb.GetValue()
        storeVoiceSettings = self.voiceCb.GetValue()
        storeFreeMove = self.freeMoveCb.GetValue()
        error = self.funcValidator(newName)
        if error:
            eve.Message('CustomInfo', {'info': error})
        else:
            self.result = {'setupName': newName,
             'storeMotd': storeMotd,
             'storeVoiceSettings': storeVoiceSettings,
             'storeFreeMove': storeFreeMove}
            self.SetModalResult(1)

    def Cancel(self, *args):
        self.result = None
        self.SetModalResult(0)


class StoredFleetSetupListWnd(Window):
    default_width = 270
    default_height = 90
    default_minSize = (default_width, default_height)
    default_windowID = 'StoredFleetSetupListWnd'
    __notifyevents__ = ['OnFleetSetupChanged']

    def ApplyAttributes(self, attributes):
        Window.ApplyAttributes(self, attributes)
        self.fleetSvc = attributes.fleetSvc
        self.SetTopparentHeight(0)
        self.SetCaption(localization.GetByLabel('UI/Fleet/FleetWindow/SetupsOverview'))
        self.scroll = uicls.ScrollContainer(parent=self.sr.main, padding=4)
        self.LoadSetups()

    def LoadSetups(self):
        fleetSetups = self.fleetSvc.GetFleetSetups()
        orderedFleetSetups = [ (fleetSetupName, setup) for fleetSetupName, setup in fleetSetups.iteritems() ]
        orderedFleetSetups.sort()
        for fleetSetupName, setup in orderedFleetSetups:
            StoredFleetSetup(parent=self.scroll, name=fleetSetupName, setupInfo=setup, settingConfigName=fleetSetupName, fleetSvc=self.fleetSvc)

    def OnFleetSetupChanged(self):
        self.scroll.Flush()
        self.LoadSetups()


class StoredFleetSetup(Container):
    default_height = 30
    default_align = uiconst.TOTOP
    default_state = uiconst.UI_NORMAL
    disabledOpacity = 0.3

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.fleetSvc = attributes.fleetSvc
        self.setupInfo = setupInfo = attributes.get('setupInfo', {})
        motd = setupInfo.get('motd', None)
        isFreeMove = setupInfo.get('isFreeMove', None)
        isVoiceEnabled = setupInfo.get('isVoiceEnabled', None)
        settingName = setupInfo.get('setupName')
        self.settingConfigName = attributes.get('settingConfigName', settingName)
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, color=(1, 1, 1, 0.15))
        nameLabel = uicontrols.EveLabelSmall(parent=self, name='nameLabel', align=uiconst.CENTERLEFT, text=settingName, padLeft=6, state=uiconst.UI_NORMAL)
        nameLabel.hint = self.GetMouseOver(setupInfo)
        nameLabel.GetMenu = self.GetMenu
        deleteBtn = uicontrols.ButtonIcon(parent=self, texturePath='res:/UI/Texture/Icons/38_16_111.png', pos=(8, 0, 16, 16), align=uiconst.CENTERRIGHT, func=self.DeleteSetup, hint=localization.GetByLabel('UI/Common/Buttons/Delete'))
        settingCont = Container(parent=self, left=deleteBtn.width + deleteBtn.left + 12, align=uiconst.TORIGHT, width=54)
        motdCont = Container(parent=settingCont, name='motdCont', align=uiconst.TOLEFT, width=18)
        voiceCont = Container(parent=settingCont, name='voiceCont', align=uiconst.TOLEFT, width=18)
        freeMoveCont = Container(parent=settingCont, name='freeMoveCont', align=uiconst.TOLEFT, width=18)
        iconPos = (0, 0, 16, 16)
        if motd is not None:
            sprite = uiprimitives.Sprite(parent=motdCont, pos=iconPos, align=uiconst.CENTER, texturePath='res:/ui/texture/icons/6_64_7.png')
            sprite.hint = localization.GetByLabel('UI/Chat/ChannelMotd', motd=motd)
            if not motd:
                sprite.opacity = self.disabledOpacity
        if isVoiceEnabled is not None:
            sprite = uiprimitives.Sprite(parent=freeMoveCont, pos=iconPos, align=uiconst.CENTER, texturePath='res:/ui/texture/icons/73_16_35.png')
            if isVoiceEnabled:
                sprite.hint = localization.GetByLabel('UI/Fleet/FleetWindow/VoiceEnabled')
            else:
                sprite.hint = localization.GetByLabel('UI/Fleet/FleetWindow/VoiceDisabled')
                sprite.opacity = self.disabledOpacity
        if isFreeMove is not None:
            sprite = uiprimitives.Sprite(parent=voiceCont, pos=iconPos, align=uiconst.CENTER, texturePath='res:/ui/texture/icons/44_32_32.png')
            if isFreeMove:
                sprite.hint = localization.GetByLabel('UI/Fleet/FleetWindow/FreeMoveOn')
            else:
                sprite.hint = localization.GetByLabel('UI/Fleet/FleetWindow/FreeMoveOff')
                sprite.opacity = self.disabledOpacity

    def DeleteSetup(self):
        self.fleetSvc.DeleteFleetSetup(setupName=self.settingConfigName)

    def GetMenu(self, *args):
        if self.fleetSvc.IsCommanderOrBoss():
            return [(uiutil.MenuLabel('UI/Fleet/FleetWindow/LoadFleetSetup'), self.fleetSvc.LoadSetup, (self.settingConfigName,))]
        return []

    def GetMouseOver(self, setup):
        allWingsInfo = setup['wingsInfo']
        textList = []
        unnamedText = localization.GetByLabel('UI/Fleet/FleetWindow/UnnamedSquad')
        for wingInfo in allWingsInfo.itervalues():
            textList.append('* %s' % wingInfo['wingName'])
            textList += [ '  - %s' % (squadName or unnamedText) for squadName in wingInfo['squadNames'] ]

        text = '<br>'.join(textList)
        return text
