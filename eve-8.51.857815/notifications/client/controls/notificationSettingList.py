#Embedded file name: notifications/client/controls\notificationSettingList.py
from carbonui.control.scrollContainer import ScrollContainer
from carbonui.primitives.sprite import Sprite
from eve.client.script.ui.control.eveLabel import EveLabelMediumBold
from carbonui.primitives.container import Container
from notifications.client.controls.notificationSettingEntityDeco import NotificationSettingEntityDeco
from notifications.client.notificationSettings.notificationSettingHandler import NotificationSettingHandler
from notifications.client.notificationSettings.notificationSettingConst import ExpandAlignmentConst
import localization
import carbonui.const as uiconst
from carbonui.primitives.line import Line
import eve.common.script.util.notificationconst as notificationConst
from notifications.client.controls.treeViewSettingsItem import TreeViewSettingsItem
from notifications.common.formatters.mailsummary import MailSummaryFormatter
from notifications.common.formatting.notificationFormatMapping import NotificationFormatMapper

class NotificationSettingList(Container):

    def ApplyAttributes(self, attributes):
        Container.ApplyAttributes(self, attributes)
        self.lastVerticalBarEnabledStatus = False
        self.notificationSettingHandler = NotificationSettingHandler()
        self.notificationSettingData = self.notificationSettingHandler.LoadSettings()
        self.isDeveloperMode = attributes.get('developerMode', False)
        self._SetupUI()

    def _SetupUI(self):
        self.settingsDescriptionRowContainer = Container(name='Settings', height=16, align=uiconst.TOTOP, parent=self, padding=(5, 5, 10, 0))
        EveLabelMediumBold(name='Settings', align=uiconst.TOLEFT, parent=self.settingsDescriptionRowContainer, text=localization.GetByLabel('Notifications/NotificationSettings/CategorySubscriptions'), bold=True)
        Sprite(name='popupIcon', parent=self.settingsDescriptionRowContainer, align=uiconst.TORIGHT, texturePath='res:/UI/Texture/classes/Notifications/settingsPopupIcon.png', width=16, heigh=16, hint=localization.GetByLabel('Notifications/NotificationSettings/PopupVisibilityTooltip'))
        Sprite(name='visibilityIcon', parent=self.settingsDescriptionRowContainer, align=uiconst.TORIGHT, texturePath='res:/UI/Texture/classes/Notifications/settingsVisibleIcon.png', width=16, heigh=16, hint=localization.GetByLabel('Notifications/NotificationSettings/HistoryVisibilityTooltip'), padding=(0, 0, 6, 0))
        self._MakeSeperationLine(self)
        self.scrollList = ScrollContainer(name='scrollContainer', parent=self, align=uiconst.TOALL, padding=(5, 5, 5, 5))
        self.scrollList.OnScrolledVertical = self.VerticalScrollInject

    def _MakeSeperationLine(self, parent):
        Line(name='topLine', parent=parent, align=uiconst.TOTOP, weight=1, padBottom=2, opacity=0.3)

    def VerticalScrollInject(self, scrollTo):
        self.AdjustCategoryHeaderForScrollBar()

    def AdjustCategoryHeaderForScrollBar(self):
        if self.lastVerticalBarEnabledStatus == self.scrollList.verticalScrollBar.display:
            return
        if self.scrollList.verticalScrollBar.display:
            self.settingsDescriptionRowContainer.padRight = 10 + self.scrollList.verticalScrollBar.width
        else:
            self.settingsDescriptionRowContainer.padRight = 10
        self.lastVerticalBarEnabledStatus = self.scrollList.verticalScrollBar.display

    def getGroupScrollEntries(self):
        entries = []
        for group, list in notificationConst.groupTypes.iteritems():
            groupName = localization.GetByLabel(notificationConst.groupNamePathsNewNotifications[group])
            entries.append(self.GetGroupEntry(fakeID=group, groupName=groupName))

        return entries

    def PopulateScroll(self):
        entries = self.getGroupScrollEntries()
        entries.sort(key=lambda entr: entr.data.GetLabel().lower())
        for entry in entries:
            self.scrollList.children.append(entry)

    def GetGroupEntry(self, fakeID, groupName):
        from eve.client.script.ui.control.treeData import TreeData
        rawNotificationList = notificationConst.groupTypes[fakeID]
        groupSettings = {}
        self.AppendEntryData(data=groupSettings, visibilityChecked=self.notificationSettingHandler.GetVisibilityStatusForGroup(fakeID, self.notificationSettingData), showPopupChecked=self.notificationSettingHandler.GetShowPopupStatusForGroup(fakeID, self.notificationSettingData), isGroup=True, id=fakeID)
        childrenData = []
        for notification in rawNotificationList:
            settingLabel = notificationConst.notificationToSettingDescription.get(notification, None)
            settingName = localization.GetByLabel(settingLabel)
            params = {}
            setting = self.notificationSettingData[notification]
            self.AppendEntryData(data=params, visibilityChecked=setting.showAtAll, showPopupChecked=setting.showPopup, isGroup=False, id=notification)
            notificationData = TreeData(label=settingName, parent=None, isRemovable=False, settings=params, settingsID=notification)
            childrenData.append(notificationData)

        childrenData.sort(key=lambda childData: childData.GetLabel().lower())
        data = TreeData(label=groupName, parent=None, children=childrenData, icon=None, isRemovable=False, settings=groupSettings)
        entry = TreeViewSettingsItem(level=0, eventListener=self, data=data, settingsID=fakeID, defaultExpanded=False)
        return entry

    def AppendEntryData(self, data, visibilityChecked, showPopupChecked, isGroup, id):
        data.update({NotificationSettingEntityDeco.VISIBILITY_CHECKED_KEY: visibilityChecked,
         NotificationSettingEntityDeco.POPUP_CHECKED_KEY: showPopupChecked,
         NotificationSettingEntityDeco.VISIBILITY_CHANGED_CALLBACK_KEY: self.OnVisibilityEntryChangedNew,
         NotificationSettingEntityDeco.POPUP_CHANGED_CALLBACK_KEY: self.OnShowPopupEntryChangedNew,
         NotificationSettingEntityDeco.GETMENU_CALLBACK: self.GetMenuForEntry,
         'isGroup': isGroup,
         'id': id})

    def OnVisibilityEntryChangedNew(self, isGroup, id, checked):
        if not isGroup:
            self._setVisibilitySettingForNotification(id, checked)

    def OnShowPopupEntryChangedNew(self, isGroup, id, checked):
        if not isGroup:
            self._setPopupSettingForNotification(id, checked)

    def _setVisibilitySettingForNotification(self, id, on):
        notificationData = self.notificationSettingData[id]
        notificationData.showAtAll = on
        self.SaveAllData()

    def _setPopupSettingForNotification(self, id, on):
        notificationData = self.notificationSettingData[id]
        notificationData.showPopup = on
        self.SaveAllData()

    def SaveAllData(self):
        self.notificationSettingHandler.SaveSettings(self.notificationSettingData)

    def GetMenuForEntry(self, isGroup, nodeID):
        if isGroup or not self.isDeveloperMode:
            return []
        else:
            return [('spawnNotification %s' % nodeID, self.OnSpawnNotificationClick, [nodeID])]

    def OnSpawnNotificationClick(self, notificationID):
        mapper = NotificationFormatMapper()
        newFormatter = mapper.GetFormatterForType(notificationID)
        if newFormatter:
            import blue
            data = newFormatter.MakeSampleData()
            sm.ScatterEvent('OnNotificationReceived', 123, notificationID, 98000001, blue.os.GetWallclockTime(), data=data)
        else:
            from notifications.client.development.notificationDevUI import FakeNotificationMaker
            maker = FakeNotificationMaker()
            counter = 1
            agentStartID = 3008416
            someAgentID = agentStartID + counter
            senderID = 98000001
            corpStartID = 1000089
            someCorp = corpStartID + counter
            maker.ScatterSingleNotification(counter, notificationID, senderID, someAgentID, someCorp)
