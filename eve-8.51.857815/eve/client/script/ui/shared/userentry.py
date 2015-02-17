#Embedded file name: eve/client/script/ui/shared\userentry.py
import math
from eve.client.script.ui.shared.stateFlag import GetStateFlagFromData, AddAndSetFlagIcon
import uiprimitives
import uicontrols
import uix
import carbonui.const as uiconst
import uiutil
import util
import uthread
import blue
import sys
import state
import trinity
import localization
import telemetry
from carbonui.control.scrollentries import SE_BaseClassCore

class User(SE_BaseClassCore):
    """
        This listentry should really rather be called 'Owner' since it supports all types of owners (char/corp/alliance/faction)
    """
    __guid__ = 'listentry.User'
    __params__ = ['charID']
    __notifyevents__ = ['OnContactLoggedOn',
     'OnContactLoggedOff',
     'OnClientContactChange',
     'OnPortraitCreated',
     'OnContactNoLongerContact',
     'OnStateSetupChance',
     'OnMyFleetInited',
     'OnFleetJoin_Local',
     'OnFleetLeave_Local',
     'ProcessOnUIAllianceRelationshipChanged',
     'OnContactChange',
     'OnBlockContacts',
     'OnUnblockContacts',
     'OnCrimewatchEngagementUpdated',
     'OnSuspectsAndCriminalsUpdate']
    isDragObject = True
    charid = None
    selected = 0
    big = 0
    id = None
    groupID = None
    picloaded = 0
    fleetCandidate = 0
    label = None
    slimuser = False

    def Startup(self, *args):
        self.sr.picture = uiprimitives.Container(parent=self, pos=(0, 0, 64, 64), name='picture', state=uiconst.UI_DISABLED, align=uiconst.RELATIVE)
        self.sr.picture.width = 32
        self.sr.picture.height = 32
        self.sr.picture.left = 2
        self.sr.picture.top = 2
        self.sr.extraIconCont = uiprimitives.Container(name='extraIconCont', parent=self, idx=0, pos=(0, 0, 16, 16), align=uiconst.BOTTOMLEFT, state=uiconst.UI_HIDDEN)
        self.sr.namelabel = uicontrols.EveLabelMedium(text='', parent=self, state=uiconst.UI_DISABLED, idx=0)
        self.sr.contactLabels = uicontrols.EveLabelMedium(text='', parent=self, state=uiconst.UI_DISABLED, idx=0, align=uiconst.BOTTOMLEFT)
        self.sr.contactLabels.top = 2
        self.sr.voiceIcon = None
        self.sr.eveGateIcon = None
        l = uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, idx=0, color=uiconst.ENTRY_LINE_COLOR)
        l.opacity = 0.05
        self.sr.standingLabel = uicontrols.EveLabelMedium(text='', parent=self, state=uiconst.UI_DISABLED, idx=0, align=uiconst.TOPRIGHT)
        self.sr.statusIcon = uiprimitives.Sprite(parent=self, name='statusIcon', align=uiconst.TOPRIGHT, pos=(3, 3, 10, 10), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Chat/Status.png', idx=0)
        self.sr.corpApplicationLabel = uicontrols.EveLabelMedium(text='', parent=self, state=uiconst.UI_DISABLED, idx=0, align=uiconst.CENTERRIGHT)
        self.sr.corpApplicationLabel.left = 16
        sm.RegisterNotify(self)

    def PreLoad(node):
        data = node
        charinfo = data.Get('info', None) or cfg.eveowners.Get(data.charID)
        data.info = charinfo
        if data.GetLabel:
            data.label = data.GetLabel(data)
        elif not data.Get('label', None):
            label = charinfo.name
            if data.bounty:
                label += '<br>'
                label += localization.GetByLabel('UI/Common/BountyAmount', bountyAmount=util.FmtISK(data.bounty.bounty, 0))
            elif data.killTime:
                label += '<br>' + localization.GetByLabel('UI/PeopleAndPlaces/ExpiresTime', expires=data.killTime)
            data.label = label
        invtype = cfg.invtypes.Get(data.info.typeID)
        data.invtype = invtype
        data.IsCharacter = invtype.groupID == const.groupCharacter
        data.IsCorporation = invtype.groupID == const.groupCorporation
        data.IsFaction = invtype.groupID == const.groupFaction
        data.IsAlliance = invtype.groupID == const.groupAlliance
        if data.IsCharacter and util.IsDustCharacter(data.charID):
            data.isDustCharacter = True
        if data.IsCorporation and not util.IsNPC(data.charID):
            logoData = cfg.corptickernames.Get(data.charID)

    def Load(self, node):
        self.sr.node = node
        data = node
        self.name = data.info.name
        self.sr.namelabel.text = data.label
        self.charid = self.id = data.itemID = data.charID
        self.picloaded = 0
        self.sr.parwnd = data.Get('dad', None)
        self.fleetCandidate = data.Get('fleetster', 1) and not data.info.IsNPC()
        self.confirmOnDblClick = data.Get('dblconfirm', 1)
        self.leaveDadAlone = data.Get('leavedad', 0)
        self.slimuser = data.Get('slimuser', False)
        self.data = {'Name': self.name,
         'charid': data.charID}
        self.inWatchlist = sm.GetService('addressbook').IsInWatchlist(data.charID)
        self.isContactList = data.Get('contactType', None)
        self.applicationDate = data.Get('applicationDate', None)
        self.contactLevel = None
        if self.isContactList:
            self.contactLevel = data.contactLevel
            self.sr.namelabel.top = 2
            self.SetLabelText()
        else:
            self.sr.namelabel.SetAlign(uiconst.CENTERLEFT)
        self.isCorpOrAllianceContact = data.contactType and data.contactType != 'contact'
        data.listvalue = [data.info.name, data.charID]
        level = self.sr.node.Get('sublevel', 0)
        subLevelOffset = 16
        self.sr.picture.left = 2 + max(0, subLevelOffset * level)
        self.LoadPortrait()
        if data.IsCharacter:
            uthread.new(self.SetRelationship, data)
            self.sr.statusIcon.state = uiconst.UI_HIDDEN
            if data.charID != eve.session.charid:
                if not util.IsNPC(data.charID) and not self.isCorpOrAllianceContact and self.inWatchlist:
                    try:
                        self.SetOnline(sm.GetService('onlineStatus').GetOnlineStatus(data.charID, fetch=False))
                    except IndexError:
                        sys.exc_clear()

            if node.isDustCharacter:
                self.ShowDustBackground()
        else:
            self.sr.statusIcon.state = uiconst.UI_HIDDEN
            if data.charID != eve.session.charid:
                uthread.new(self.SetRelationship, data)
        self.sr.namelabel.left = 40 + max(0, subLevelOffset * level)
        self.sr.contactLabels.left = 40
        if self.sr.node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        if not self.isCorpOrAllianceContact:
            self.contactLevel = sm.GetService('addressbook').GetStandingsLevel(self.charid, 'contact')
            self.SetBlocked(1)
        else:
            self.SetBlocked(0)
        if self.isCorpOrAllianceContact:
            self.SetStandingText(self.contactLevel)
        if self.applicationDate:
            self.sr.corpApplicationLabel.SetText(localization.GetByLabel('UI/Corporations/Applied', applydate=self.applicationDate))
            self.sr.corpApplicationLabel.Show()
            data.Set('sort_' + localization.GetByLabel('UI/Common/Date'), self.applicationDate)
            data.Set('sort_' + localization.GetByLabel('UI/Common/Name'), data.info.name)
        else:
            self.sr.corpApplicationLabel.SetText('')
            self.sr.corpApplicationLabel.Hide()

    def ShowDustBackground(self):
        dustBackground = getattr(self, 'dustBackground', None)
        blueColor = util.Color.DUST[:3]
        from carbonui.primitives.gradientSprite import GradientConst
        from carbonui.primitives.gradientSprite import Gradient2DSprite
        if dustBackground is None:
            blueColorSqrt = (math.sqrt(blueColor[0]), math.sqrt(blueColor[1]), math.sqrt(blueColor[2]))
            self.dustBackground = Gradient2DSprite(bgParent=self, idx=0, name='gradient2d', rgbHorizontal=[0, 1], rgbVertical=[0, 1], rgbDataHorizontal=[blueColorSqrt, blueColorSqrt], rgbDataVertical=[blueColorSqrt, blueColorSqrt], rgbInterp='bezier', alphaHorizontal=[0, 1], alphaDataHorizontal=[1.0, 1.0], alphaVertical=[0, 0.5, 1], alphaDataVertical=[0.25, 0.1, 0.0], textureSize=16)
        self.dustBackground.display = True
        dustBackgroundLine = getattr(self, 'dustBackgroundLine', None)
        if dustBackgroundLine is None:
            self.dustBackgroundLine = uicontrols.GradientSprite(parent=self, pos=(0, 0, 0, 1), align=uiconst.TOTOP, rgbData=[(0, blueColor), (0.5, blueColor), (1.0, blueColor)], alphaData=[(0, 0.2), (0.5, 1), (1.0, 0.2)], alphaInterp=GradientConst.INTERP_LINEAR, colorInterp=GradientConst.INTERP_LINEAR, idx=0, state=uiconst.UI_DISABLED)
        self.dustBackgroundLine.display = True

    def GetValue(self):
        return [self.name, self.id]

    def GetDynamicHeight(node, width):
        if '<br>' in node.label:
            node.height = max(37, uix.GetTextHeight(node.label, linespace=11))
        else:
            node.height = 37
        return node.height

    def OnContactLoggedOn(self, charID):
        if self and not self.destroyed and charID == self.charid and charID != eve.session.charid and not util.IsNPC(charID):
            self.SetOnline(1)

    def OnContactLoggedOff(self, charID):
        if self and not self.destroyed and charID == self.charid and charID != eve.session.charid and not util.IsNPC(charID):
            self.SetOnline(0)

    def OnClientContactChange(self, charID, online):
        if online:
            self.OnContactLoggedOn(charID)
        else:
            self.OnContactLoggedOff(charID)

    def OnContactNoLongerContact(self, charID):
        if self and not self.destroyed and charID == self.charid and charID != eve.session.charid:
            self.SetOnline(None)

    def OnPortraitCreated(self, charID):
        if self.destroyed:
            return
        if self.sr.node and charID == self.sr.node.charID and not self.picloaded:
            self.LoadPortrait(orderIfMissing=False)

    def OnContactChange(self, contactIDs, contactType = None):
        if self.destroyed:
            return
        self.SetRelationship(self.sr.node)
        if self.charid in contactIDs:
            if sm.GetService('addressbook').IsInAddressBook(self.charid, contactType):
                if not self.isContactList:
                    self.isContactList = contactType
            else:
                self.isContactList = None
            self.inWatchlist = sm.GetService('addressbook').IsInWatchlist(self.charid)
            if not self.inWatchlist:
                isBlocked = sm.GetService('addressbook').IsBlocked(self.charid)
                if isBlocked:
                    self.sr.statusIcon.state = uiconst.UI_DISABLED
                    self.sr.statusIcon.SetRGB(1.0, 1.0, 1.0)
                else:
                    self.sr.statusIcon.state = uiconst.UI_HIDDEN
            else:
                self.sr.statusIcon.state = uiconst.UI_DISABLED

    def OnBlockContacts(self, contactIDs):
        if not self or self.destroyed:
            return
        if self.charid in contactIDs:
            self.SetBlocked(1)

    def OnUnblockContacts(self, contactIDs):
        if not self or self.destroyed:
            return
        if self.charid in contactIDs:
            self.SetBlocked(0)

    def OnStateSetupChance(self, what):
        if self.destroyed:
            return
        self.SetRelationship(self.sr.node)

    def ProcessOnUIAllianceRelationshipChanged(self, *args):
        if self.destroyed:
            return
        self.SetRelationship(self.sr.node)

    def OnFleetJoin_Local(self, memberInfo, state = 'Active'):
        if self.destroyed:
            return
        myID = util.GetAttrs(self, 'sr', 'node', 'charID')
        charID = memberInfo.charID
        if myID is not None and charID == myID:
            uthread.new(self.SetRelationship, self.sr.node)

    def OnFleetLeave_Local(self, memberInfo):
        if self.destroyed:
            return
        myID = util.GetAttrs(self, 'sr', 'node', 'charID')
        charID = memberInfo.charID
        if myID is not None and charID == myID or charID == session.charid:
            uthread.new(self.SetRelationship, self.sr.node)

    def OnMyFleetInited(self):
        if self.destroyed:
            return
        uthread.new(self.SetRelationship, self.sr.node)

    def SetOnline(self, online):
        if self.destroyed:
            return
        if self.slimuser:
            return
        if online is None or not self.inWatchlist or self.isCorpOrAllianceContact:
            self.sr.statusIcon.state = uiconst.UI_HIDDEN
        else:
            self.sr.statusIcon.SetRGB(float(not online) * 0.75, float(online) * 0.75, 0.0)
            if online:
                self.sr.statusIcon.hint = localization.GetByLabel('UI/Common/Online')
            else:
                self.sr.statusIcon.hint = localization.GetByLabel('UI/Common/Offline')
            self.sr.statusIcon.state = uiconst.UI_DISABLED

    def SetBlocked(self, blocked):
        isBlocked = sm.GetService('addressbook').IsBlocked(self.charid)
        if blocked and isBlocked and not self.isCorpOrAllianceContact:
            self.sr.statusIcon.SetTexturePath('res:/UI/Texture/classes/Chat/Blocked.png')
            self.sr.statusIcon.state = uiconst.UI_DISABLED
        elif self.inWatchlist:
            self.sr.statusIcon.SetTexturePath('res:/UI/Texture/classes/Chat/Status.png')
        else:
            self.sr.statusIcon.state = uiconst.UI_HIDDEN

    def SetLabelText(self):
        labelMask = sm.GetService('addressbook').GetLabelMask(self.charid)
        self.sr.node.labelMask = labelMask
        labeltext = sm.GetService('addressbook').GetLabelText(labelMask, self.isContactList)
        if not self or self.destroyed:
            return
        self.sr.contactLabels.text = labeltext

    def SetStandingText(self, standing):
        self.sr.standingLabel.text = standing
        self.sr.standingLabel.left = 2
        self.sr.standingLabel.top = 2

    def SetRelationship(self, data, debugFlag = None):
        if self.destroyed:
            return
        if self.slimuser:
            return
        if not data:
            return
        flag = None
        if data.Get('contactType', None):
            if self.contactLevel is None:
                return
            if self.contactLevel > const.contactGoodStanding:
                flag = state.flagStandingHigh
            elif self.contactLevel <= const.contactGoodStanding and self.contactLevel > const.contactNeutralStanding:
                flag = state.flagStandingGood
            elif self.contactLevel == const.contactNeutralStanding:
                flag = state.flagStandingNeutral
            elif self.contactLevel >= const.contactBadStanding and self.contactLevel < const.contactNeutralStanding:
                flag = state.flagStandingBad
            elif self.contactLevel <= const.contactBadStanding:
                flag = state.flagStandingHorrible
        else:
            flag = GetStateFlagFromData(data)
        if flag:
            AddAndSetFlagIcon(self, flag=flag, top=20, left=4)

    def LoadPortrait(self, orderIfMissing = True):
        self.sr.picture.Flush()
        if self.sr.node is None:
            return
        if uiutil.GetOwnerLogo(self.sr.picture, self.id, size=32, callback=True, orderIfMissing=orderIfMissing):
            self.picloaded = 1

    def RemoveFromListGroup(self, listGroupIDs, charIDs, listname):
        if self.destroyed:
            return
        if listGroupIDs:
            for listGroupID, charID in listGroupIDs:
                uicore.registry.RemoveFromListGroup(listGroupID, charID)

            sm.GetService('addressbook').RefreshWindow()
        if charIDs and listname:
            name = [localization.GetByLabel('UI/AddressBook/RemoveAddressBook1'), cfg.eveowners.Get(charIDs[0]).name][len(charIDs) == 1]
            if eve.Message('WarnDeleteFromAddressbook', {'name': name,
             'type': listname}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            sm.GetService('addressbook').DeleteEntryMulti(charIDs, None)

    def GetMenu(self):
        if self.destroyed:
            return
        m = []
        selected = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        multi = len(selected) > 1
        if multi:
            return self._GetMultiMenu(selected)
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.id, self.sr.node.invtype.typeID)
        if self.sr.node.Get('GetMenu', None) is not None:
            m += self.sr.node.GetMenu(self.sr.node)
        listGroupID = self.sr.node.Get('listGroupID', None)
        if listGroupID is not None:
            group = uicore.registry.GetListGroup(listGroupID)
            if group:
                if listGroupID not in [('buddygroups', 'all'), ('buddygroups', 'allcorps')]:
                    m.append(None)
                    m.append((uiutil.MenuLabel('UI/Common/RemoveFromGroup', {'groupname': group['label']}), self.RemoveFromListGroup, ([(listGroupID, self.charid)], [], '')))
        if self.sr.node.Get('MenuFunction', None):
            cm = [None]
            cm += self.sr.node.MenuFunction([self.sr.node])
            m += cm
        if self.isContactList is not None:
            if sm.GetService('addressbook').ShowLabelMenuAndManageBtn(self.isContactList):
                m.append(None)
                assignLabelMenu = sm.StartService('addressbook').GetAssignLabelMenu(selected, [self.charid], self.isContactList)
                if len(assignLabelMenu) > 0:
                    m.append((uiutil.MenuLabel('UI/Mail/AssignLabel'), assignLabelMenu))
                removeLabelMenu = sm.StartService('addressbook').GetRemoveLabelMenu(selected, [self.charid], self.isContactList)
                if len(removeLabelMenu) > 0:
                    m.append((uiutil.MenuLabel('UI/Mail/LabelRemove'), removeLabelMenu))
        return m

    def _GetMultiMenu(self, selected):
        """ 
            Populate right-click menu in the case where multiple entries are selected 
        """
        m = []
        charIDs = []
        multiCharIDs = []
        multiEveCharIDs = []
        listGroupIDs = {}
        listGroupID_charIDs = []
        onlyCharacters = True
        for entry in selected:
            listGroupID = entry.listGroupID
            if listGroupID:
                listGroupIDs[listGroupID] = 0
                listGroupID_charIDs.append((listGroupID, entry.charID))
            if entry.charID:
                charIDs.append((entry.charID, None))
                multiCharIDs.append(entry.charID)
                if not util.IsCharacter(entry.charID):
                    onlyCharacters = False
                elif util.IsDustCharacter(entry.charID):
                    multiEveCharIDs.append(entry.charID)

        if self.isContactList is None:
            if onlyCharacters:
                m += sm.GetService('menu').CharacterMenu(charIDs)
            if listGroupIDs:
                listname = ''
                delCharIDs = []
                rem = []
                for listGroupID, charID in listGroupID_charIDs:
                    if listGroupID in [('buddygroups', 'all'), ('buddygroups', 'allcorps')]:
                        if onlyCharacters:
                            return m
                        group = uicore.registry.GetListGroup(listGroupID)
                        listname = [localization.GetByLabel('UI/Generic/BuddyList')][listGroupID == ('buddygroups', 'all')]
                        delCharIDs.append(charID)
                        rem.append((listGroupID, charID))

                for each in rem:
                    listGroupID_charIDs.remove(each)

                foldername = 'folders'
                if len(listGroupIDs) == 1:
                    group = uicore.registry.GetListGroup(listGroupIDs.keys()[0])
                    if group:
                        foldername = group['label']
                label = ''
                if delCharIDs and listname:
                    label = localization.GetByLabel('UI/PeopleAndPlaces/RemoveMultipleFromAddressbook', removecount=len(delCharIDs))
                    if listGroupID_charIDs:
                        label += [', ']
                if listGroupID_charIDs:
                    label += localization.GetByLabel('UI/PeopleAndPlaces/RemoveFromFolder', foldername=foldername, removecount=len(listGroupID_charIDs))
                m.append((label, self.RemoveFromListGroup, (listGroupID_charIDs, delCharIDs, listname)))
        else:
            addressBookSvc = sm.GetService('addressbook')
            counter = len(selected)
            blocked = 0
            if self.isContactList == 'contact':
                editLabel = localization.GetByLabel('UI/PeopleAndPlaces/EditContacts', contactcount=counter)
                m.append((editLabel, addressBookSvc.EditContacts, [multiCharIDs, 'contact']))
                deleteLabel = localization.GetByLabel('UI/PeopleAndPlaces/RemoveContacts', contactcount=counter)
                m.append((deleteLabel, addressBookSvc.DeleteEntryMulti, [multiCharIDs, 'contact']))
                for charid in multiCharIDs:
                    if sm.GetService('addressbook').IsBlocked(charid):
                        blocked += 1

                if blocked == counter:
                    unblockLabel = localization.GetByLabel('UI/PeopleAndPlaces/UnblockContacts', contactcount=blocked)
                    m.append((unblockLabel, addressBookSvc.UnblockOwner, [multiCharIDs]))
            elif self.isContactList == 'corpcontact':
                editLabel = localization.GetByLabel('UI/PeopleAndPlaces/EditCorpContacts', contactcount=counter)
                m.append((editLabel, addressBookSvc.EditContacts, [multiCharIDs, 'corpcontact']))
                deleteLabel = localization.GetByLabel('UI/PeopleAndPlaces/RemoveCorpContacts', contactcount=counter)
                m.append((deleteLabel, addressBookSvc.DeleteEntryMulti, [multiCharIDs, 'corpcontact']))
            elif self.isContactList == 'alliancecontact':
                editLabel = localization.GetByLabel('UI/PeopleAndPlaces/EditAllianceContacts', contactcount=counter)
                m.append((editLabel, addressBookSvc.EditContacts, [multiCharIDs, 'alliancecontact']))
                deleteLabel = localization.GetByLabel('UI/PeopleAndPlaces/RemoveAllianceContacts', contactcount=counter)
                m.append((deleteLabel, addressBookSvc.DeleteEntryMulti, [multiCharIDs, 'alliancecontact']))
            m.append(None)
            assignLabelMenu = sm.StartService('addressbook').GetAssignLabelMenu(selected, multiCharIDs, self.isContactList)
            if len(assignLabelMenu) > 0:
                m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/AddContactLabel'), assignLabelMenu))
            removeLabelMenu = sm.StartService('addressbook').GetRemoveLabelMenu(selected, multiCharIDs, self.isContactList)
            if len(removeLabelMenu) > 0:
                m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveContactLabel'), removeLabelMenu))
            m.append(None)
            m.append((uiutil.MenuLabel('UI/Commands/CapturePortrait'), sm.StartService('photo').SavePortraits, [multiEveCharIDs]))
        if self.sr.node.Get('MenuFunction', None):
            cm = [None]
            cm += self.sr.node.MenuFunction(selected)
            m += cm
        return m

    def ShowInfo(self, *args):
        if self.destroyed:
            return
        sm.GetService('info').ShowInfo(cfg.eveowners.Get(self.charid).typeID, self.charid)

    def OnClick(self, *args):
        if self.destroyed:
            return
        eve.Message('ListEntryClick')
        self.sr.node.scroll.SelectNode(self.sr.node)
        if self.sr.node.Get('OnClick', None):
            self.sr.node.OnClick(self)

    def OnDblClick(self, *args):
        if self.destroyed:
            return
        if self.sr.node.Get('OnDblClick', None):
            self.sr.node.OnDblClick(self)
            return
        if self.sr.parwnd and hasattr(self.sr.parwnd, 'Select') and self.confirmOnDblClick:
            self.sr.parwnd.Select(self)
            self.sr.parwnd.Confirm()
            return
        if not self.leaveDadAlone and self.sr.parwnd and uicore.registry.GetModalWindow() == self.sr.parwnd:
            self.sr.parwnd.SetModalResult(uiconst.ID_OK)
            return
        onDblClick = settings.user.ui.Get('dblClickUser', 0)
        if onDblClick == 0:
            sm.GetService('info').ShowInfo(cfg.eveowners.Get(self.charid).typeID, self.charid)
        elif onDblClick == 1:
            sm.GetService('LSC').Invite(self.charid)

    def GetDragData(self, *args):
        if self and not self.destroyed and not self.slimuser:
            return self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        else:
            return []

    @classmethod
    def GetCopyData(cls, node):
        return node.label

    def OnSuspectsAndCriminalsUpdate(self, criminalizedCharIDs, decriminalizedCharIDs):
        if self.destroyed:
            return
        charID = util.GetAttrs(self, 'sr', 'node', 'charID')
        if charID is not None and (charID in criminalizedCharIDs or charID in decriminalizedCharIDs):
            uthread.new(self.SetRelationship, self.sr.node)

    def OnCrimewatchEngagementUpdated(self, otherCharId, timeout):
        if self.destroyed:
            return
        charID = util.GetAttrs(self, 'sr', 'node', 'charID')
        if charID is not None and charID == otherCharId:
            uthread.new(self.SetRelationship, self.sr.node)


class AgentEntry(SE_BaseClassCore):
    __guid__ = 'listentry.AgentEntry'
    default_name = 'AgentEntry'
    isDragObject = True

    def Startup(self, *args):
        self.divisionName = ''
        self.agentName = ''
        self.levelName = ''
        self.agentType = ''
        self.agentLocation = ''
        self.missionState = ''
        self.locationLabel = None
        uiprimitives.Line(parent=self, align=uiconst.TOBOTTOM, idx=0, color=uiconst.ENTRY_LINE_COLOR)
        picCont = uiprimitives.Container(parent=self, pos=(1, 0, 50, 0), name='picture', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOLEFT)
        self.sr.pic = uiprimitives.Sprite(parent=picCont, align=uiconst.TOALL, state=uiconst.UI_PICKCHILDREN)
        textCont = uiprimitives.Container(parent=self, name='textCont', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOALL, padLeft=6, padTop=2, padRight=6)
        self.textCont = uiprimitives.Container(parent=textCont, name='text', state=uiconst.UI_PICKCHILDREN, align=uiconst.TOALL, clipChildren=True, padTop=2)
        self.sr.namelabel = uicontrols.EveLabelMedium(text='', align=uiconst.TOPLEFT, parent=self.textCont)
        self.sr.levelLabel = uicontrols.EveLabelMedium(text='', align=uiconst.TOPLEFT, parent=self.textCont, top=14)
        self.sr.missionLabel = uicontrols.EveLabelMedium(text='', parent=self.textCont, align=uiconst.TOPRIGHT)
        self.agentChatBtn = uicontrols.ButtonIcon(name='removeButton', parent=self, align=uiconst.BOTTOMRIGHT, width=22, iconSize=16, left=3, top=-1, texturePath='res:/UI/Texture/classes/Chat/AgentChat.png', hint=localization.GetByLabel('UI/Chat/StartConversationAgent'), func=self.StartConversation)
        buttonIconOnMouseEnter = self.agentChatBtn.OnMouseEnter
        self.agentChatBtn.OnMouseEnter = (self.OnChatButtonMouseEnter, self.agentChatBtn, buttonIconOnMouseEnter)

    def PreLoad(node):
        data = node
        charinfo = data.Get('info', None) or cfg.eveowners.Get(data.charID)
        data.info = charinfo
        data.itemID = data.charID
        invtype = cfg.invtypes.Get(data.info.typeID)
        data.invtype = invtype

    def GetAgentInfo(self, data):
        charID = data.charID
        missionState = data.missionState
        missionStateLabel = {const.agentMissionStateAllocated: '<color=0xFFFFFF00>' + localization.GetByLabel('UI/Journal/JournalWindow/Agents/StateOffered'),
         const.agentMissionStateOffered: '<color=0xFFFFFF00>' + localization.GetByLabel('UI/Journal/JournalWindow/Agents/StateOffered'),
         const.agentMissionStateAccepted: '<color=0xff00FF00>' + localization.GetByLabel('UI/Journal/JournalWindow/Agents/StateAccepted'),
         const.agentMissionStateFailed: '<color=0xffeb3700>' + localization.GetByLabel('UI/Journal/JournalWindow/Agents/StateFailed')}
        if missionState is not None:
            self.missionState = missionStateLabel[missionState]
        self.agentName = cfg.eveowners.Get(charID).name
        agentInfo = sm.GetService('agents').GetAgentByID(charID)
        if agentInfo:
            agentDivision = sm.GetService('agents').GetDivisions()[agentInfo.divisionID].divisionName.replace('&', '&amp;')
            if charID in sm.GetService('agents').GetTutorialAgentIDs():
                self.agentType = localization.GetByLabel('UI/AgentFinder/TutorialAgentDivision', divisionName=agentDivision)
            elif agentInfo.agentTypeID == const.agentTypeEpicArcAgent:
                self.agentType = localization.GetByLabel('UI/AgentFinder/EpicArcAgentDivision', divisionName=agentDivision)
            elif agentInfo.agentTypeID in (const.agentTypeGenericStorylineMissionAgent, const.agentTypeStorylineMissionAgent):
                self.agentType = localization.GetByLabel('UI/AgentFinder/StorylineAgentDivision', divisionName=agentDivision)
            elif agentInfo.agentTypeID == const.agentTypeEventMissionAgent:
                self.agentType = localization.GetByLabel('UI/AgentFinder/EventAgentDivision', divisionName=agentDivision)
            elif agentInfo.agentTypeID == const.agentTypeCareerAgent:
                self.agentType = localization.GetByLabel('UI/AgentFinder/CareerAgentDivision', divisionName=agentDivision)
            elif agentInfo.agentTypeID == const.agentTypeAura:
                self.agentType = ''
            else:
                self.agentType = localization.GetByLabel('UI/AgentFinder/LevelAgentDivision', agentLevel=uiutil.GetLevel(agentInfo.level), divisionName=agentDivision)
            if agentInfo.stationID and session.stationid != agentInfo.stationID:
                self.agentLocation = localization.GetByLabel('UI/Agents/LocatedAt', station=agentInfo.stationID)
        else:
            self.agentChatBtn.display = False

    def Load(self, node):
        self.sr.node = node
        data = node
        if self.sr.node.Get('selected', 0):
            self.Select()
        else:
            self.Deselect()
        self.GetAgentInfo(data)
        if self.agentLocation != '':
            if not self.locationLabel:
                self.locationLabel = uicontrols.EveLabelMedium(text=self.agentLocation, top=14, parent=self.textCont)
            self.sr.levelLabel.top = 28
        self.name = data.info.name
        self.sr.namelabel.text = self.agentName
        self.sr.missionLabel.text = self.missionState
        if self.levelName == '':
            levelText = self.agentType
        else:
            levelText = self.levelName
        self.sr.levelLabel.text = levelText
        self.charID = data.charID
        sm.GetService('photo').GetPortrait(self.charID, 64, self.sr.pic)

    def GetMenu(self):
        if self.destroyed:
            return
        m = []
        selected = self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        multi = len(selected) > 1
        if multi:
            return self._GetMultiMenu(selected)
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.charID, self.sr.node.invtype.typeID)
        if self.sr.node.Get('GetMenu', None) is not None:
            m += self.sr.node.GetMenu(self.sr.node)
        listGroupID = self.sr.node.Get('listGroupID', None)
        if listGroupID is not None:
            group = uicore.registry.GetListGroup(listGroupID)
            if group:
                if not listGroupID == ('agentgroups', 'all'):
                    m.append(None)
                    m.append((uiutil.MenuLabel('UI/Common/RemoveFromGroup', {'groupname': group['label']}), self.RemoveFromListGroup, ([(listGroupID, self.charID)], [], '')))
        if self.sr.node.Get('MenuFunction', None):
            cm = [None]
            cm += self.sr.node.MenuFunction([self.sr.node])
            m += cm
        return m

    def _GetMultiMenu(self, selected):
        """ 
            Populate right-click menu in the case where multiple entries are selected 
        """
        m = []
        charIDs = []
        multiCharIDs = []
        listGroupIDs = {}
        listGroupID_charIDs = []
        onlyCharacters = True
        for entry in selected:
            listGroupID = entry.listGroupID
            if listGroupID:
                listGroupIDs[listGroupID] = 0
                listGroupID_charIDs.append((listGroupID, entry.charID))
            if entry.charID:
                charIDs.append((entry.charID, None))
                multiCharIDs.append(entry.charID)
                if not util.IsCharacter(entry.charID):
                    onlyCharacters = False

        if onlyCharacters:
            m += sm.GetService('menu').CharacterMenu(charIDs)
        if listGroupIDs:
            listname = ''
            delCharIDs = []
            rem = []
            for listGroupID, charID in listGroupID_charIDs:
                if listGroupID == ('agentgroups', 'all'):
                    if onlyCharacters:
                        return m
                    group = uicore.registry.GetListGroup(listGroupID)
                    listname = [localization.GetByLabel('UI/Agents/AgentList'), localization.GetByLabel('UI/Generic/BuddyList')][listGroupID == ('buddygroups', 'all')]
                    delCharIDs.append(charID)
                    rem.append((listGroupID, charID))

            for each in rem:
                listGroupID_charIDs.remove(each)

            foldername = 'folders'
            if len(listGroupIDs) == 1:
                group = uicore.registry.GetListGroup(listGroupIDs.keys()[0])
                if group:
                    foldername = group['label']
            label = ''
            if delCharIDs and listname:
                label = localization.GetByLabel('UI/PeopleAndPlaces/RemoveMultipleFromAddressbook', removecount=len(delCharIDs))
                if listGroupID_charIDs:
                    label += [', ']
            if listGroupID_charIDs:
                label += localization.GetByLabel('UI/PeopleAndPlaces/RemoveFromFolder', foldername=foldername, removecount=len(listGroupID_charIDs))
            m.append((label, self.RemoveFromListGroup, (listGroupID_charIDs, delCharIDs, listname)))
        if self.sr.node.Get('MenuFunction', None):
            cm = [None]
            cm += self.sr.node.MenuFunction(selected)
            m += cm
        return m

    def ShowInfo(self, *args):
        if self.destroyed:
            return
        sm.GetService('info').ShowInfo(cfg.eveowners.Get(self.charID).typeID, self.charID)

    def GetDragData(self, *args):
        if self and not self.destroyed:
            return self.sr.node.scroll.GetSelectedNodes(self.sr.node)
        else:
            return []

    def OnClick(self, *args):
        if self.destroyed:
            return
        eve.Message('ListEntryClick')
        self.sr.node.scroll.SelectNode(self.sr.node)
        if self.sr.node.Get('OnClick', None):
            self.sr.node.OnClick(self)

    @telemetry.ZONE_METHOD
    def OnDblClick(self, *args):
        if self.destroyed:
            return
        if self.sr.node.Get('OnDblClick', None):
            self.sr.node.OnDblClick(self)
            return
        agentInfo = sm.GetService('agents').GetAgentByID(self.charID)
        if session.stationid and agentInfo:
            sm.GetService('agents').InteractWith(self.charID)
            return
        self.ShowInfo()

    def GetHeight(self, *args):
        node, width = args
        node.height = 51
        return node.height

    def RemoveFromListGroup(self, listGroupIDs, charIDs, listname):
        if self.destroyed:
            return
        if listGroupIDs:
            for listGroupID, charID in listGroupIDs:
                uicore.registry.RemoveFromListGroup(listGroupID, charID)

            sm.GetService('addressbook').RefreshWindow()
        if charIDs and listname:
            name = [localization.GetByLabel('UI/AddressBook/RemoveAddressBook1'), cfg.eveowners.Get(charIDs[0]).name][len(charIDs) == 1]
            if eve.Message('WarnDeleteFromAddressbook', {'name': name,
             'type': listname}, uiconst.YESNO, suppress=uiconst.ID_YES) != uiconst.ID_YES:
                return
            sm.GetService('addressbook').DeleteEntryMulti(charIDs, None)

    def StartConversation(self, *args):
        if getattr(self, 'charID', None) is not None:
            sm.StartService('agents').InteractWith(self.charID)

    def OnChatButtonMouseEnter(self, btn, buttonIconOnMouseEnter, *args):
        self.OnMouseEnter()
        buttonIconOnMouseEnter()
