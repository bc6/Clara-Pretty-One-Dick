#Embedded file name: notifications/client/controls\treeViewSettingsItem.py
from eve.client.script.ui.control.treeViewEntry import TreeViewEntry
from notifications.client.controls.notificationSettingEntityDeco import NotificationSettingEntityDeco
from eve.client.script.ui.control.checkbox import Checkbox
import carbonui.const as uiconst
import localization

class TreeViewSettingsItem(TreeViewEntry):
    default_name = 'TreeViewEntrySettings'

    def ApplyAttributes(self, attributes):
        TreeViewEntry.ApplyAttributes(self, attributes)
        if hasattr(self.data, 'settings'):
            self.settings = self.data.settings
            if self.settings:
                self.GetMenuCallback = self.settings[NotificationSettingEntityDeco.GETMENU_CALLBACK]
                visibilityChecked = self.settings[NotificationSettingEntityDeco.VISIBILITY_CHECKED_KEY]
                showPopupChecked = self.settings[NotificationSettingEntityDeco.POPUP_CHECKED_KEY]
                self.visibilityCallBack = self.settings[NotificationSettingEntityDeco.VISIBILITY_CHANGED_CALLBACK_KEY]
                self.showPopupCallBack = self.settings[NotificationSettingEntityDeco.POPUP_CHANGED_CALLBACK_KEY]
                self.popupCheckBox = Checkbox(name='UsepopupNotifications', text='', parent=self.topRightCont, align=uiconst.TORIGHT, checked=showPopupChecked, callback=self.OnPopupNotificationToggle, hint=localization.GetByLabel('Notifications/NotificationSettings/PopupVisibilityCheckboxTooltip'))
                self.visibilityChckbox = Checkbox(name='visibilityNotification', text='', parent=self.topRightCont, align=uiconst.TORIGHT, checked=visibilityChecked, callback=self.OnVisibiltyToggle, hint=localization.GetByLabel('Notifications/NotificationSettings/HistoryVisibilityCheckboxTooltip'))
                self.isGroup = self.settings['isGroup']
                self.id = self.settings['id']

    def OnPopupNotificationToggle(self, checkbox):
        if self.isGroup:
            for child in self.childCont.children:
                child.UpdatePopupCheckBox(checkbox._checked, report=True)

        self.showPopupCallBack(self.isGroup, self.id, checkbox._checked)

    def OnVisibiltyToggle(self, checkbox):
        if self.isGroup:
            for child in self.childCont.children:
                child.UpdateVisibilitySetting(checkbox._checked, report=True)

        self.visibilityCallBack(self.isGroup, self.id, checkbox._checked)

    def OnOneClick(self, *args):
        print 'click'

    def GetMenu(self):
        return self.GetMenuCallback(self.isGroup, self.id)

    def GetTreeViewEntryClassByTreeData(self, treeData):
        """ Can be overridden to return custom tree view entry classes """
        return TreeViewSettingsItem

    def UpdateVisibilitySetting(self, on, report = False):
        self.visibilityChckbox.SetChecked(onoff=on, report=report)

    def UpdatePopupCheckBox(self, on, report = False):
        self.popupCheckBox.SetChecked(onoff=on, report=report)
