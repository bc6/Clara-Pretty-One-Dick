#Embedded file name: eve/client/script/ui/shared/neocom/corporation\corp_ui_member_autokicks.py
import carbonui.const as uiconst
from carbonui.primitives.container import Container
from eve.client.script.ui.control.entries import Generic
from eve.client.script.ui.control import entries as listentry
from eve.client.script.ui.control.eveScroll import Scroll
from eve.common.lib.appConst import defaultPadding
import localization

class CorpAutoKicks(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.autoKicksScroll = Scroll(name='applicationsScroll', parent=self, align=uiconst.TOALL, padding=(defaultPadding,
         defaultPadding,
         defaultPadding,
         defaultPadding))

    def Load(self, args):
        sm.GetService('corpui').LoadTop('res:/ui/Texture/WindowIcons/corporationmembers.png', localization.GetByLabel('UI/Corporations/BaseCorporationUI/AutoKickManagement'), localization.GetByLabel('UI/Corporations/BaseCorporationUI/AutoKickDescription'))
        pendingKicks = sm.GetService('corp').GetPendingAutoKicks()
        scrolllist = []
        for characterID, kickedByCharacterID in pendingKicks:
            characterIDLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(characterID).name, info=('showinfo', const.typeCharacterAmarr, characterID))
            kickedByCharacterIDLink = localization.GetByLabel('UI/Contracts/ContractsWindow/ShowInfoLink', showInfoName=cfg.eveowners.Get(kickedByCharacterID).name, info=('showinfo', const.typeCharacterAmarr, kickedByCharacterID))
            entry = listentry.Get(data={'label': '%s<t>%s' % (characterIDLink, kickedByCharacterIDLink)}, decoClass=KickEntry)
            scrolllist.append(entry)

        headers = [localization.GetByLabel('UI/Corporations/CorporationWindow/Members/CorpMemberName'), localization.GetByLabel('UI/Corporations/CorporationWindow/Members/KickCreatedBy')]
        self.autoKicksScroll.Load(contentList=scrolllist, headers=headers, noContentHint=localization.GetByLabel('UI/Corporations/CorporationWindow/Members/NoPendingAutoKicks'))


class KickEntry(Generic):

    def Load(self, node):
        Generic.Load(self, node)
        self.sr.label.state = uiconst.UI_NORMAL
