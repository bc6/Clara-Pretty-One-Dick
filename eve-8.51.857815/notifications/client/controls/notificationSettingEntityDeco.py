#Embedded file name: notifications/client/controls\notificationSettingEntityDeco.py
from eve.client.script.ui.control.baseListEntry import BaseListEntryCustomColumns
from eve.client.script.ui.control.checkbox import Checkbox

class NotificationSettingEntityDeco(BaseListEntryCustomColumns):
    default_name = 'NotificationSettingEntry'
    VISIBILITY_CHECKED_KEY = 'visibilityChecked'
    VISIBILITY_CHANGED_CALLBACK_KEY = 'onVisibilityChanged'
    POPUP_CHECKED_KEY = 'popupChecked'
    POPUP_CHANGED_CALLBACK_KEY = 'onPopupChanged'
    GETMENU_CALLBACK = 'menuCallBack'

    def ApplyAttributes(self, attributes):
        BaseListEntryCustomColumns.ApplyAttributes(self, attributes)
        self.AddColumnText('    ' + attributes.node.label)
        self.node = attributes.node
        visibilityChecked = self.node.get(self.VISIBILITY_CHECKED_KEY)
        popupChecked = self.node.get(self.POPUP_CHECKED_KEY)
        self.visibilityCallBack = self.node.get(self.VISIBILITY_CHANGED_CALLBACK_KEY)
        self.popupChangedCallback = self.node.get(self.POPUP_CHANGED_CALLBACK_KEY)
        self.getMenuCallBack = self.node.get(self.GETMENU_CALLBACK)
        visibiltyColumn = self.AddColumnContainer()
        self.visibilityCheckbox = Checkbox(name='visibiltyCheckbox', parent=visibiltyColumn, text='', checked=visibilityChecked, callback=self.OnVisibiltyCheckbox)
        containerColumn = self.AddColumnContainer()
        self.popupCheckBox = Checkbox(name='showPopupCheckBox', parent=containerColumn, text='', checked=popupChecked, callback=self.OnPopupChangedCheckbox)

    def forceSetPopupState(self, status):
        if not self.destroyed:
            self.popupCheckBox.SetChecked(status, report=False)

    def OnPopupChangedCheckbox(self, *args):
        self.popupChangedCallback(self.node)

    def OnVisibiltyCheckbox(self, *args):
        self.visibilityCallBack(self.node)

    def GetMenu(self):
        return self.getMenuCallBack(self.node)
