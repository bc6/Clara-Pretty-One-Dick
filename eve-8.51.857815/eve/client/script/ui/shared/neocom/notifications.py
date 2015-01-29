#Embedded file name: eve/client/script/ui/shared/neocom\notifications.py
from eve.client.script.ui.control.divider import Divider
import blue
import uiprimitives
import uicontrols
import eve.common.script.util.notificationconst as notificationConst
import uthread
import uiutil
import util
import listentry
import carbonui.const as uiconst
import base
import eve.common.script.util.notificationUtil as notificationUtil
import uicls
import localization
HINTCUTOFF = 100
DELETE_INTERVAL = 0.3 * const.SEC

class NotificationForm(uiprimitives.Container):
    """ This class contains the notification UI, which is found in the MAIL window"""
    __guid__ = 'form.NotificationForm'
    __notifyevents__ = ['OnNotificationsRefresh', 'OnNewNotificationReceived', 'OnNotificationReadOutside']

    def Setup(self):
        sm.RegisterNotify(self)
        self.scrollHeight = 0
        self.DrawStuff()
        self.readTimer = 0
        self.viewing = None
        self.lastDeleted = 0

    def DrawStuff(self, *args):
        btns = uicontrols.ButtonGroup(btns=[[localization.GetByLabel('UI/Mail/Notifications/MarkAllAsRead'),
          self.MarkAllRead,
          None,
          81], [localization.GetByLabel('UI/Mail/Notifications/DeleteAll'),
          self.DeleteAll,
          None,
          81]], parent=self, idx=0)
        leftContWidth = settings.user.ui.Get('notifications_leftContWidth', 200)
        self.sr.leftCont = uiprimitives.Container(name='leftCont', parent=self, align=uiconst.TOLEFT, pos=(const.defaultPadding,
         0,
         leftContWidth,
         0))
        self.sr.leftScroll = uicontrols.Scroll(name='leftScroll', parent=self.sr.leftCont, padding=(0,
         const.defaultPadding,
         0,
         const.defaultPadding))
        self.sr.leftScroll.multiSelect = 0
        divider = Divider(name='divider', align=uiconst.TOLEFT, width=const.defaultPadding, parent=self, state=uiconst.UI_NORMAL)
        divider.Startup(self.sr.leftCont, 'width', 'x', 180, 250)
        self.sr.rightCont = uiprimitives.Container(name='rightCont', parent=self, align=uiconst.TOALL, pos=(0,
         0,
         const.defaultPadding,
         const.defaultPadding))
        dividerCont = uicontrols.DragResizeCont(name='dividerCont', settingsID='notificationsSplitSize', parent=self.sr.rightCont, align=uiconst.TOTOP_PROP, minSize=0.1, maxSize=0.9, defaultSize=0.7, clipChildren=True)
        self.sr.readingPaneCont = uiprimitives.Container(name='readingPaneCont', parent=self.sr.rightCont, align=uiconst.TOALL)
        self.sr.readingPane = uicls.EditPlainText(setvalue='', parent=self.sr.readingPaneCont, align=uiconst.TOALL, readonly=1)
        self.sr.msgCont = uiprimitives.Container(name='msgCont', parent=dividerCont)
        self.sr.msgScroll = uicontrols.Scroll(name='msgScroll', parent=self.sr.msgCont, padding=(0,
         const.defaultPadding,
         0,
         0))
        self.sr.msgScroll.sr.id = 'notifications_msgs'
        self.sr.msgScroll.sr.fixedColumns = {localization.GetByLabel('UI/Mail/Status'): 52}
        self.sr.msgScroll.OnSelectionChange = self.MsgScrollSelectionChange
        self.sr.msgScroll.OnDelete = self.DeleteFromKeyboard
        self.inited = True

    def LoadNotificationForm(self, *args):
        self.LoadLeftSide()

    def OnClose_(self, *args):
        settings.user.ui.Set('notifications_leftContWidth', self.sr.leftCont.width)
        settings.user.ui.Set('notifications_readingContHeight', self.sr.readingPaneCont.height)
        sm.GetService('mailSvc').SaveChangesToDisk()
        sm.UnregisterNotify(self)

    def SelectGroupById(self, groupID):
        for entry in self.sr.leftScroll.GetNodes():
            if entry.groupID == groupID:
                panel = entry.panel
                if panel is not None:
                    self.UpdateCounters()
                    panel.OnClick()

    def LoadLeftSide(self):
        scrolllist = self.GetStaticLabelsGroups()
        self.sr.leftScroll.Load(contentList=scrolllist)
        lastViewedID = settings.char.ui.Get('mail_lastnotification', None)
        for entry in self.sr.leftScroll.GetNodes():
            if entry.groupID is None:
                continue
            if entry.groupID == lastViewedID:
                panel = entry.panel
                if panel is not None:
                    self.UpdateCounters()
                    panel.OnClick()
                    return

        self.UpdateCounters()
        if len(self.sr.leftScroll.GetNodes()) > 0:
            entry = self.sr.leftScroll.GetNodes()[0]
            panel = entry.panel
            if panel is not None:
                panel.OnClick()

    def GetStaticLabelsGroups(self):
        """
            Gets the groups for the static labels
        """
        scrolllist = []
        lastViewedID = settings.char.ui.Get('mail_lastnotification', None)
        for groupID, labelPath in notificationUtil.groupNamePaths.iteritems():
            label = localization.GetByLabel(labelPath)
            entry = self.GetGroupEntry(groupID, label, groupID == lastViewedID)
            strippedLabel = uiutil.StripTags(label, stripOnly=['localized'])
            scrolllist.append((strippedLabel.lower(), entry))

        scrolllist = uiutil.SortListOfTuples(scrolllist)
        entry = self.GetGroupEntry(const.notificationGroupUnread, localization.GetByLabel('UI/Mail/Unread'), const.notificationGroupUnread == lastViewedID)
        scrolllist.insert(0, entry)
        scrolllist.insert(1, listentry.Get('Space', {'height': 12}))
        return scrolllist

    def GetGroupEntry(self, groupID, label, selected = 0):
        data = {'GetSubContent': self.GetLeftGroups,
         'label': label,
         'id': ('notification', id),
         'state': 'locked',
         'BlockOpenWindow': 1,
         'disableToggle': 1,
         'expandable': 0,
         'showicon': 'hide',
         'showlen': 0,
         'groupItems': [],
         'hideNoItem': 1,
         'hideExpander': 1,
         'hideExpanderLine': 1,
         'selectGroup': 1,
         'isSelected': selected,
         'groupID': groupID,
         'OnClick': self.LoadGroupFromEntry,
         'MenuFunction': self.StaticMenu}
        entry = listentry.Get('Group', data)
        return entry

    def GetLeftGroups(self, *args):
        return []

    def LoadGroupFromEntry(self, entry, *args):
        group = entry.sr.node
        self.LoadGroupFromNode(group)

    def LoadGroupFromNode(self, node, refreshing = 0, selectedIDs = [], *args):
        group = node
        settings.char.ui.Set('mail_lastnotification', group.groupID)
        notifications = []
        if group.groupID == const.notificationGroupUnread:
            notifications = sm.GetService('notificationSvc').GetFormattedUnreadNotifications()
            senders = [ value.senderID for value in sm.GetService('notificationSvc').GetUnreadNotifications() ]
        else:
            notifications = sm.GetService('notificationSvc').GetFormattedNotifications(group.groupID)
            senders = [ value.senderID for value in sm.GetService('notificationSvc').GetNotificationsByGroupID(group.groupID) ]
        sm.GetService('mailSvc').PrimeOwners(senders)
        if not self or self.destroyed:
            return
        pos = self.sr.msgScroll.GetScrollProportion()
        scrolllist = []
        for each in notifications:
            senderName = ''
            if each.senderID is not None:
                senderName = cfg.eveowners.Get(each.senderID).ownerName
            label = '<t>' + senderName + '<t>' + each.subject + '<t>' + util.FmtDate(each.created, 'ls')
            if group.groupID == const.notificationGroupUnread:
                typeGroup = notificationConst.GetTypeGroup(each.typeID)
                labelPath = notificationUtil.groupNamePaths.get(typeGroup, None)
                if labelPath is None:
                    typeName = ''
                else:
                    typeName = localization.GetByLabel(labelPath)
                label += '<t>' + typeName
            hint = each.body.replace('<br>', '')
            hint = uiutil.TruncateStringTo(hint, HINTCUTOFF, localization.GetByLabel('UI/Common/MoreTrail'))
            data = util.KeyVal()
            data.cleanLabel = label
            data.parentNode = node
            data.label = label
            data.hint = hint
            data.id = each.notificationID
            data.typeID = each.typeID
            data.senderID = each.senderID
            data.data = util.KeyVal(read=each.processed)
            data.info = each
            data.OnClick = self.LoadReadingPaneFromEntry
            data.OnDblClick = self.DblClickNotificationEntry
            data.GetMenu = self.GetEntryMenu
            data.ignoreRightClick = 1
            data.isSelected = each.notificationID in selectedIDs
            data.Draggable_blockDrag = 1
            scrolllist.append(listentry.Get('MailEntry', data=data))

        scrollHeaders = [localization.GetByLabel('UI/Mail/Status'),
         localization.GetByLabel('UI/Mail/Sender'),
         localization.GetByLabel('UI/Mail/Subject'),
         localization.GetByLabel('UI/Mail/Received')]
        if group.groupID == const.notificationGroupUnread:
            scrollHeaders.append(localization.GetByLabel('UI/Mail/Notifications/GroupName'))
        if not self or self.destroyed:
            return
        self.sr.msgScroll.Load(contentList=scrolllist, headers=scrollHeaders, noContentHint=localization.GetByLabel('UI/Mail/Notifications/NoNotifications'))
        if not refreshing:
            self.ClearReadingPane()
        else:
            self.sr.msgScroll.ScrollToProportion(pos)
        self.UpdateCounters()

    def StaticMenu(self, node, *args):
        m = []
        if node.groupID != const.notificationGroupUnread:
            m.append((uiutil.MenuLabel('UI/Mail/Notifications/MarkAllAsRead'), self.MarkAllReadInGroup, (node.groupID,)))
            m.append(None)
            m.append((uiutil.MenuLabel('UI/Mail/Notifications/DeleteAll'), self.DeleteAllFromGroup, (node.groupID,)))
        return m

    def DeleteAll(self, *args):
        if eve.Message('EvemailNotificationsDeleteAll', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            sm.GetService('notificationSvc').DeleteAll()

    def MarkAllRead(self, *args):
        if eve.Message('EvemailNotificationsMarkAllRead', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            sm.GetService('notificationSvc').MarkAllRead()

    def DeleteAllFromGroup(self, groupID, *args):
        if eve.Message('EvemailNotificationsDeleteGroup', {}, uiconst.YESNO, suppress=uiconst.ID_YES) == uiconst.ID_YES:
            sm.GetService('notificationSvc').DeleteAllFromGroup(groupID)

    def MarkAllReadInGroup(self, groupID, *args):
        sm.GetService('notificationSvc').MarkAllReadInGroup(groupID)

    def GetEntryMenu(self, entry, *args):
        m = []
        sel = self.sr.msgScroll.GetSelected()
        selIDs = [ x.id for x in sel ]
        msgID = entry.sr.node.id
        if msgID not in selIDs:
            selIDs = [msgID]
            sel = [entry.sr.node]
        unread = {}
        for each in sel:
            if not each.data.read:
                unread[each.id] = each

        if len(unread) > 0:
            m.append((uiutil.MenuLabel('UI/Mail/Notifications/MarkAsRead'), self.MarkAsRead, (unread.values(), unread.keys())))
        m.append(None)
        if len(selIDs) > 0:
            m.append((uiutil.MenuLabel('UI/Mail/Notifications/Delete'), self.DeleteNotifications, (sel, selIDs)))
        return m

    def MarkAsRead(self, notifications, notificationIDs, *args):
        sm.GetService('notificationSvc').MarkAsRead(notificationIDs)
        self.UpdateCounters()
        self.SetMsgEntriesAsRead(notifications)

    def DblClickNotificationEntry(self, entry):
        messageID = entry.sr.node.id
        info = entry.sr.node.info
        sm.GetService('notificationSvc').OpenNotificationReadingWnd(info)

    def LoadReadingPaneFromEntry(self, entry):
        uthread.new(self.LoadReadingPaneFromNode, entry.sr.node)

    def LoadReadingPaneFromNode(self, node):
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if not shift:
            self.LoadReadingPane(node)

    def LoadReadingPane(self, node):
        self.readTimer = 0
        info = node.info
        txt = sm.GetService('notificationSvc').GetReadingText(node.senderID, info.subject, info.created, info.body)
        self.sr.readingPane.SetText(txt)
        self.viewing = node.id
        if not node.data.read:
            self.MarkAsRead([node], [node.id])

    def ClearReadingPane(self):
        self.sr.readingPane.SetText('')
        self.viewing = None

    def SetMsgEntriesAsRead(self, nodes):
        for node in nodes:
            self.TryReloadNode(node)

    def TryReloadNode(self, node):
        node.data.read = 1
        panel = node.Get('panel', None)
        if panel is None:
            return
        panel.LoadMailEntry(node)

    def MsgScrollSelectionChange(self, sel = [], *args):
        """
            when what is selected in the message scroll has changed, we need to
            figure out what toolbar buttons should be visible
        """
        if len(sel) == 0:
            return
        node = sel[0]
        if self.viewing != node.id:
            self.readTimer = base.AutoTimer(1000, self.LoadReadingPane, node)

    def DeleteFromKeyboard(self, *args):
        if blue.os.GetWallclockTime() - self.lastDeleted < DELETE_INTERVAL:
            eve.Message('uiwarning03')
            return
        sel = self.sr.msgScroll.GetSelected()
        ids = [ each.id for each in sel ]
        self.DeleteNotifications(sel, ids)
        self.lastDeleted = blue.os.GetWallclockTime()

    def DeleteNotifications(self, notificationEntries, ids):
        if len(notificationEntries) < 1:
            return
        idx = notificationEntries[0].idx
        ids = []
        for entry in notificationEntries:
            ids.append(entry.id)

        sm.GetService('notificationSvc').DeleteNotifications(ids)
        sm.ScatterEvent('OnMessageChanged', const.mailTypeNotifications, ids, 'deleted')
        self.sr.msgScroll.RemoveEntries(notificationEntries)
        if self.viewing in ids:
            self.ClearReadingPane()
        self.UpdateCounters()
        if len(self.sr.msgScroll.GetNodes()) < 1:
            self.sr.msgScroll.Load(contentList=[], headers=[], noContentHint=localization.GetByLabel('UI/Mail/Notifications/NoNotifications'))
            return
        numChildren = len(self.sr.msgScroll.GetNodes())
        newIdx = min(idx, numChildren - 1)
        newSelectedNode = self.sr.msgScroll.GetNode(newIdx)
        if newSelectedNode is not None:
            self.sr.msgScroll.SelectNode(newSelectedNode)

    def SelectNodeByNotificationID(self, notificationID):
        nodes = self.sr.msgScroll.GetNodes()
        for node in nodes:
            if node.id == notificationID:
                self.sr.msgScroll.SelectNode(node)
                break

    def OnNotificationsRefresh(self):
        self.LoadLeftSide()

    def OnNewNotificationReceived(self, *args):
        self.UpdateCounters()

    def OnNotificationReadOutside(self, notificationID):
        self.UpdateCounters()
        for node in self.sr.msgScroll.GetNodes():
            if node.id == notificationID:
                self.SetMsgEntriesAsRead([node])
                return

    def UpdateCounters(self):
        """
            Updates the 'new notification' counter for all the groups
        """
        unreadCounts = sm.GetService('notificationSvc').GetAllUnreadCount()
        for each in self.sr.leftScroll.GetNodes():
            if each.groupID is None:
                continue
            count = unreadCounts.get(each.groupID, 0)
            self.TryChangePanelLabel(each, count)

    def TryChangePanelLabel(self, node, count):
        panel = node.Get('panel', None)
        if panel is None:
            return
        panelLabel = self.GetPanelLabel(node.cleanLabel, count)
        panel.sr.label.text = panelLabel

    def GetPanelLabel(self, label, count):
        if count > 0:
            return localization.GetByLabel('UI/Mail/Notifications/GroupUnreadLabel', groupName=label, unreadCount=count)
        else:
            return label
