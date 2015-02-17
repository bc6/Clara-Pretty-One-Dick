#Embedded file name: eve/client/script/ui/shared/neocom/addressBook\contactNotificationEntry.py
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

class ContactNotificationEntry(listentry.Generic):
    __guid__ = 'listentry.ContactNotificationEntry'
    isDragObject = True

    def Startup(self, *args):
        listentry.Generic.Startup(self, args)
        picCont = uiprimitives.Container(name='picture', parent=self, align=uiconst.TOLEFT, width=32)
        textCont = uiprimitives.Container(name='textCont', parent=self, align=uiconst.TOALL, padLeft=2)
        self.sr.picture = uiprimitives.Container(name='picture', parent=picCont, align=uiconst.TOPLEFT, pos=(0, 0, 32, 32))
        self.sr.label = uicontrols.EveLabelMedium(text='', parent=textCont, align=uiconst.TOTOP, height=16, state=uiconst.UI_NORMAL)
        self.sr.messageLabel = uicontrols.EveLabelMedium(text='', parent=textCont, align=uiconst.TOTOP, height=16, state=uiconst.UI_DISABLED, left=5)

    def Load(self, node):
        self.sr.node = node
        self.notificationID = node.id
        self.senderID = node.senderID
        listentry.Generic.Load(self, node)
        self.sr.messageLabel.text = node.label2
        self.LoadContactEntry(node)
        self.hint = node.hint

    def LoadContactEntry(self, node):
        data = node.data
        uiutil.GetOwnerLogo(self.sr.picture, node.senderID, size=32, noServerCall=True)

    def GetDragData(self, *args):
        return self.sr.node.scroll.GetSelectedNodes(self.sr.node)

    def OnDropData(self, dragObj, nodes):
        pass

    def GetHeight(self, *args):
        node, width = args
        node.height = 34
        return node.height

    def GetMenu(self, *args):
        addressBookSvc = sm.GetService('addressbook')
        isContact = addressBookSvc.IsInAddressBook(self.senderID, 'contact')
        isBlocked = addressBookSvc.IsBlocked(self.senderID)
        m = []
        m.append((uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo))
        if isContact:
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/EditContact'), addressBookSvc.AddToPersonalMulti, (self.senderID, 'contact', True)))
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/RemoveContact'), addressBookSvc.DeleteEntryMulti, ([self.senderID], 'contact')))
        else:
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/AddContact'), addressBookSvc.AddToPersonalMulti, (self.senderID, 'contact')))
        if isBlocked:
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/UnblockContact'), addressBookSvc.UnblockOwner, ([self.senderID],)))
        else:
            m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/BlockContact'), addressBookSvc.BlockOwner, (self.senderID,)))
        m.append((uiutil.MenuLabel('UI/PeopleAndPlaces/DeleteNotification'), self.DeleteNotifications))
        return m

    def DeleteNotifications(self):
        sm.GetService('notificationSvc').DeleteNotifications([self.notificationID])
        sm.ScatterEvent('OnMessageChanged', const.mailTypeNotifications, [self.notificationID], 'deleted')
        sm.ScatterEvent('OnNotificationsRefresh')

    def ShowInfo(self, *args):
        if self.destroyed:
            return
        sm.GetService('info').ShowInfo(cfg.eveowners.Get(self.senderID).typeID, self.senderID)
