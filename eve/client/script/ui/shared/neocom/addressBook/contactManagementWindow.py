#Embedded file name: eve/client/script/ui/shared/neocom/addressBook\contactManagementWindow.py
import math
import sys
import service
import uiprimitives
import uicontrols
from carbonui.primitives.containerAutoSize import ContainerAutoSize
from carbonui.primitives.frame import Frame
import uthread
import uix
import uiutil
import form
import util
from eve.client.script.ui.control import entries as listentry
import carbonui.const as uiconst
import uicls
import log
import localization
import telemetry
from eve.client.script.ui.shared.neocom.evemail import ManageLabelsBase

class ContactManagementWnd(uicontrols.Window):
    __guid__ = 'form.ContactManagementWnd'

    def ApplyAttributes(self, attributes):
        uicontrols.Window.ApplyAttributes(self, attributes)
        entityID = attributes.entityID
        level = attributes.level
        watchlist = attributes.watchlist
        isContact = attributes.isContact
        self.labelID = attributes.get('labelID', None)
        self.result = None
        self.SetCaption(localization.GetByLabel('UI/PeopleAndPlaces/ContactManagement'))
        self.minHeight = 105
        self.SetMinSize([250, self.minHeight])
        self.MakeUnResizeable()
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.entityID = entityID
        self.level = level
        self.watchlist = watchlist
        self.isContact = isContact
        self.notify = False
        self.ConstructLayout()

    def ConstructLayout(self):
        topCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 70), padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        imgCont = uiprimitives.Container(name='imgCont', parent=topCont, align=uiconst.TOLEFT, pos=(0, 0, 64, 0), padding=(0,
         0,
         const.defaultPadding,
         0))
        topRightCont = uiprimitives.Container(name='topRightCont', parent=topCont, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=(const.defaultPadding,
         0,
         0,
         0))
        nameCont = uiprimitives.Container(name='nameCont', parent=topRightCont, align=uiconst.TOTOP, pos=(0, 0, 0, 20))
        uiprimitives.Line(parent=nameCont, align=uiconst.TOBOTTOM)
        levelCont = uiprimitives.Container(name='levelCont', parent=topRightCont, align=uiconst.TOTOP, height=42, padding=(0,
         const.defaultPadding,
         0,
         0))
        self.standingList = {const.contactHighStanding: localization.GetByLabel('UI/PeopleAndPlaces/ExcellentStanding'),
         const.contactGoodStanding: localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'),
         const.contactNeutralStanding: localization.GetByLabel('UI/PeopleAndPlaces/NeutralStanding'),
         const.contactBadStanding: localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'),
         const.contactHorribleStanding: localization.GetByLabel('UI/PeopleAndPlaces/TerribleStanding')}
        levelList = self.standingList.keys()
        levelList.sort()
        levelText = self.standingList.get(self.level)
        self.levelText = uicontrols.EveLabelMedium(text=levelText, parent=levelCont, height=14, align=uiconst.TOTOP, state=uiconst.UI_DISABLED, idx=0)
        self.levelSelector = uicls.StandingLevelSelector(name='levelCont', parent=levelCont, align=uiconst.TOTOP, height=55, padTop=4, level=self.level)
        self.levelSelector.OnStandingLevelSelected = self.OnStandingLevelSelected
        charName = cfg.eveowners.Get(self.entityID).name
        uiutil.GetOwnerLogo(imgCont, self.entityID, size=64, noServerCall=True)
        label = uicontrols.EveLabelLargeBold(text=charName, parent=nameCont, left=0, align=uiconst.TOPLEFT, width=170, state=uiconst.UI_DISABLED, idx=0)
        nameCont.state = uiconst.UI_DISABLED
        nameCont.height = label.height + 2
        self.minHeight += nameCont.height
        topCont.height = max(topCont.height, nameCont.height + levelCont.height)
        labels = sm.GetService('addressbook').GetContactLabels('contact').values()
        if not self.isContact and len(labels):
            labelList = []
            labelCont = uiprimitives.Container(name='topCont', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 18), padding=(const.defaultPadding,
             0,
             0,
             const.defaultPadding))
            for label in labels:
                labelList.append((label.name, (label.name, label.labelID)))

            labelList = uiutil.SortListOfTuples(labelList)
            assignLabelText = '-- %s --' % localization.GetByLabel('UI/Mail/AssignLabel')
            labelList.insert(0, (assignLabelText, None))
            self.labelsCombo = uicontrols.Combo(label='', parent=labelCont, options=labelList, name='labelscombo', adjustWidth=True)
            self.minHeight += labelCont.height
            if self.labelID:
                self.labelsCombo.SetValue(self.labelID)
        if util.IsCharacter(self.entityID):
            splitter = uiprimitives.Container(name='splitter', parent=self.sr.main, align=uiconst.TOTOP, pos=(0, 0, 0, 1), padding=(0, 0, 0, 0))
            uiprimitives.Line(parent=splitter, align=uiconst.TOBOTTOM)
            bottomCont = uiprimitives.Container(name='bottomCont', parent=self.sr.main, align=uiconst.TOALL, pos=(0, 0, 0, 0), padding=const.defaultPadding)
            cbCont = uiprimitives.Container(name='cbCont', parent=bottomCont, align=uiconst.TOTOP, pos=(0, 0, 0, 16), state=uiconst.UI_HIDDEN)
            notifyCont = uiprimitives.Container(name='notifyCont', parent=bottomCont, align=uiconst.TOTOP, pos=(0, 0, 0, 95))
            cbCont.state = uiconst.UI_NORMAL
            self.inWatchlistCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/PeopleAndPlaces/AddContactToWatchlist'), parent=cbCont, configName='inWatchlistCb', retval=0, checked=self.watchlist, align=uiconst.TOTOP)
            self.sendNotificationCb = uicontrols.Checkbox(text=localization.GetByLabel('UI/PeopleAndPlaces/SendNotificationTo', contactName=charName), parent=notifyCont, configName='sendNotificationCb', retval=0, checked=0, align=uiconst.TOTOP)
            self.message = uicls.EditPlainText(setvalue='', parent=notifyCont, align=uiconst.TOALL, maxLength=120, padBottom=const.defaultPadding)
            self.minHeight += 120
        btnText = localization.GetByLabel('UI/PeopleAndPlaces/AddContact')
        if self.isContact:
            btnText = localization.GetByLabel('UI/PeopleAndPlaces/EditContact')
        self.btnGroup = uicontrols.ButtonGroup(btns=[[btnText,
          self.Confirm,
          (),
          81,
          1,
          1,
          0], [localization.GetByLabel('UI/Common/Buttons/Cancel'),
          self.Cancel,
          (),
          81,
          0,
          0,
          0]], parent=self.sr.main, idx=0)
        if self.level is None:
            self.levelText.text = localization.GetByLabel('UI/PeopleAndPlaces/SelectStanding')
            btn = self.btnGroup.GetBtnByLabel(btnText)
            uicore.registry.SetFocus(btn)
        uthread.new(self.SetWindowSize)

    def OnStandingLevelSelected(self, level):
        self.level = level
        self.levelText.text = self.standingList.get(self.level)

    def SetWindowSize(self):
        if self and not self.destroyed:
            self.height = self.minHeight
            self.SetMinSize([200, self.minHeight])

    def Confirm(self):
        if self.level is None:
            eve.Message('NoStandingsSelected')
            return
        relationshipID = self.level
        inWatchlist = False
        sendNotification = False
        message = None
        contactLabel = None
        if hasattr(self, 'labelsCombo'):
            contactLabel = self.labelsCombo.GetValue()
        if util.IsCharacter(self.entityID):
            inWatchlist = self.inWatchlistCb.checked
            sendNotification = self.sendNotificationCb.checked
            message = self.message.GetValue()
        self.result = (relationshipID,
         inWatchlist,
         sendNotification,
         message,
         contactLabel)
        if getattr(self, 'isModal', None):
            self.SetModalResult(1)

    def Cancel(self):
        self.result = None
        if getattr(self, 'isModal', None):
            self.SetModalResult(0)
