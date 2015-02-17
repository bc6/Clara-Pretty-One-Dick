#Embedded file name: notifications/client/notificationSettings\notificationSettingHandler.py
V_ALIGN = 'VAlign'
H_ALIGN = 'HAlign'
NOTIFICATION_SETTINGS = 'notificationSettings'
LAST_SEEN_TIME = 'lastSeenTime'
SOUND_ENABLED = 'soundEnabled'
STACK_SIZE = 'stackSize'
FADE_TIME = 'fadeTime'
POPUPS_ENABLED = 'popupsEnabled'
BADGE_OFFSET = 'badgeOffset'
HISTORY_HIGHT_KEY = 'historyHeight'
WIDGET_ENABLED = 'widgetEnabled'
REPOSITION_COUNT_KEY = 'repositionCount'

class NotificationSettingData(object):

    def __init__(self, notificationID, showPopup, showAtAll, group):
        self.notificationID = notificationID
        self.showPopup = showPopup
        self.showAtAll = showAtAll
        self.group = group

    def GetSingleValueFromStatus(self):
        value = 0
        if self.showAtAll:
            value += 1
        if self.showPopup:
            value += 2
        return value

    @staticmethod
    def GetShowAtAllShowPopupFromValue(value):
        if value == 3:
            return (True, True)
        elif value == 2:
            return (False, True)
        elif value == 1:
            return (True, False)
        else:
            return (False, False)

    def toTuple(self):
        return (self.notificationID, self.GetSingleValueFromStatus(), self.group)

    def IsEqual(self, notificationSettingsData):
        return self.notificationID == notificationSettingsData.notificationID and self.showAtAll == notificationSettingsData.showAtAll and self.showPopup == notificationSettingsData.showPopup and self.group == notificationSettingsData.group

    @staticmethod
    def fromTuple(tuple):
        showAtAll, showPopup = NotificationSettingData.GetShowAtAllShowPopupFromValue(tuple[1])
        return NotificationSettingData(notificationID=tuple[0], showPopup=showPopup, showAtAll=showAtAll, group=tuple[2])


from eve.common.script.util import notificationconst as notificationConst
from notifications.client.notificationSettings.notificationSettingConst import ExpandAlignmentConst

class NotificationSettingHandler(object):
    MIN_HISTORY_HEIGHT = 100
    MAX_HISTORY_HEIGHT = 1000
    prefix = 'exp_'
    ALL_NOTIFICATIONSETTINGS = {HISTORY_HIGHT_KEY: 'notification_historyHeight',
     BADGE_OFFSET: 'notification_badge_offset',
     POPUPS_ENABLED: 'notificationSettingsPopupsEnabled',
     FADE_TIME: 'notificationSettingsFadeTime',
     STACK_SIZE: 'notificationSettingsStackSize',
     SOUND_ENABLED: 'notificationSettingsSoundEnabled',
     LAST_SEEN_TIME: 'lastSeenNotificationTime',
     NOTIFICATION_SETTINGS: 'notificationSettingsData',
     H_ALIGN: 'notificationSettingsHorizontalAlignment',
     V_ALIGN: 'notificationSettingsVerticalAlignment',
     WIDGET_ENABLED: 'notificationSettingsWidgetEnabled',
     REPOSITION_COUNT_KEY: 'notificationSettingsRepositionCount'}

    def __init__(self, settingHolder = None, noneMode = False, charSettingsHolder = None):
        if settingHolder is None:
            self.mainSettingsHolder = settings.char.notifications
        else:
            self.mainSettingsHolder = settingHolder
        if charSettingsHolder is None:
            self.mainCharacterSettingsHolder = settings.char.notifications
        self.noneMode = noneMode

    def GetNotificationWidgetEnabled(self):
        return self.GetSetting(WIDGET_ENABLED, default=True)

    def SetNotificationWidgetEnabled(self, value):
        self.SetSetting(WIDGET_ENABLED, value)
        sm.ScatterEvent('OnLocalNotificationSettingChanged')

    def ToggleNotificationWidgetEnabled(self):
        self.SetNotificationWidgetEnabled(not self.GetNotificationWidgetEnabled())

    def _sanitizeHeight(self, height):
        return min(self.MAX_HISTORY_HEIGHT, max(height, self.MIN_HISTORY_HEIGHT))

    def DeleteAllSettings(self):
        for key, value in self.ALL_NOTIFICATIONSETTINGS.iteritems():
            self.mainSettingsHolder.Delete(value)

    def GetSetting(self, key, default):
        if self.noneMode:
            return default
        return self.mainSettingsHolder.Get(self.ALL_NOTIFICATIONSETTINGS[key], default)

    def SetSetting(self, key, value):
        if self.noneMode:
            return
        self.mainSettingsHolder.Set(self.ALL_NOTIFICATIONSETTINGS[key], value)

    def GetPreferredHeight(self):
        return self._sanitizeHeight(self.GetSetting(key=HISTORY_HIGHT_KEY, default=400))

    def SetPreferredHeight(self, height):
        self.SetSetting(HISTORY_HIGHT_KEY, self._sanitizeHeight(height))

    def GetNotificationBadgeOffset(self):
        return self.GetSetting(BADGE_OFFSET, default=(5, 5))

    def SetNotificationBadgeOffset(self, position):
        self.SetSetting(BADGE_OFFSET, position)
        self.IncrementRepositionCount()

    def TogglePopupsEnabled(self):
        self.SetPopupsEnabled(not self.GetPopupsEnabled())

    def SetPopupsEnabled(self, status):
        self.SetSetting(POPUPS_ENABLED, value=status)

    def GetPopupsEnabled(self):
        return self.GetSetting(POPUPS_ENABLED, default=True)

    def SaveFadeTime(self, time):
        self.SetSetting(FADE_TIME, value=time)

    def GetFadeTime(self):
        return self.GetSetting(FADE_TIME, default=3)

    def SaveStackSize(self, stackSize):
        self.SetSetting(STACK_SIZE, stackSize)

    def ToggleSoundEnabled(self):
        self.SetNotificationSoundEnabled(not self.GetNotificationSoundEnabled())

    def SetNotificationSoundEnabled(self, enabled):
        self.SetSetting(SOUND_ENABLED, enabled)

    def GetNotificationSoundEnabled(self):
        return self.GetSetting(SOUND_ENABLED, default=True)

    def GetStackSize(self):
        return self.GetSetting(STACK_SIZE, default=3)

    def GetRepositionCount(self):
        return self.GetSetting(REPOSITION_COUNT_KEY, default=0)

    def IncrementRepositionCount(self):
        currentPosition = self.GetRepositionCount()
        currentPosition = currentPosition + 1
        self._SetRepositionCount(value=currentPosition)

    def _SetRepositionCount(self, value):
        self.SetSetting(REPOSITION_COUNT_KEY, value)

    def SerializeSettings(self, settingsData):
        serialized = {}
        for key, value in settingsData.iteritems():
            serialized[key] = value.toTuple()

        return serialized

    def DeserializeSettings(self, settingsData):
        deserialized = {}
        for key, value in settingsData.iteritems():
            deserialized[key] = NotificationSettingData.fromTuple(value)

        return deserialized

    def SaveSettings(self, settingsData):
        cleanData = self.GetOnlyDifferentFromDefault(settingsData)
        serialized = self.SerializeSettings(cleanData)
        self.SetSetting(NOTIFICATION_SETTINGS, serialized)

    def LoadSettings(self):
        notificationSettings = None
        defaultSettings = self.GetDefaultNotificationSettings()
        serialized = self.GetSetting(NOTIFICATION_SETTINGS, default=None)
        if serialized:
            notificationSettings = self.DeserializeSettings(serialized)
            for key, value in notificationSettings.iteritems():
                defaultSettings[key] = value

        return defaultSettings

    def LoadSavedSettings(self):
        notificationSettings = None
        serialized = self.GetSetting(NOTIFICATION_SETTINGS, default=None)
        if serialized:
            notificationSettings = self.DeserializeSettings(serialized)
        return notificationSettings

    def GetOnlyDifferentFromDefault(self, settingsData):
        difference = {}
        defaultSettings = self.GetDefaultNotificationSettings()
        for notificationId, data in settingsData.iteritems():
            if not data.IsEqual(defaultSettings[notificationId]):
                difference[notificationId] = data

        return difference

    def GetDefaultNotificationSettings(self):
        newDict = {}
        for group, list in notificationConst.groupTypes.iteritems():
            for notification in list:
                newDict[notification] = NotificationSettingData(notificationID=notification, showPopup=True, showAtAll=True, group=group)

        return newDict

    def GetShowPopupStatusForGroup(self, groupID, settings):
        enabled = False
        for setting in settings.itervalues():
            if setting.group == groupID and setting.showPopup:
                enabled = True
                break

        return enabled

    def GetVisibilityStatusForGroup(self, groupID, settings):
        enabled = False
        for setting in settings.itervalues():
            if setting.group == groupID and setting.showAtAll:
                enabled = True
                break

        return enabled

    def SetHorizontalExpandAlignment(self, value):
        if value in ExpandAlignmentConst.EXPAND_ALIGNMENTS_HORIZONTAL:
            self.SetSetting(H_ALIGN, value=value)
            sm.ScatterEvent('OnNotificationAlignmentChanged', '')

    def SetVerticalExpandAlignment(self, value):
        if value in ExpandAlignmentConst.EXPAND_ALIGNMENTS_VERTICAL:
            self.SetSetting(V_ALIGN, value=value)
            sm.ScatterEvent('OnNotificationAlignmentChanged', '')

    def GetHorizontalExpandAlignment(self):
        return self.GetSetting(H_ALIGN, default=ExpandAlignmentConst.EXPAND_ALIGNMENT_HORIZONTAL_LEFT)

    def GetVerticalExpandAlignment(self):
        return self.GetSetting(V_ALIGN, default=ExpandAlignmentConst.EXPAND_ALIGNMENT_VERTICAL_UP)

    def GetLastSeenTime(self):
        return self.mainCharacterSettingsHolder.Get(self.ALL_NOTIFICATIONSETTINGS[LAST_SEEN_TIME], 0)

    def SetLastSeenTime(self, time):
        self.mainCharacterSettingsHolder.Set(self.ALL_NOTIFICATIONSETTINGS[LAST_SEEN_TIME], time)

    def GetLastHistoryTimeCleanTime(self):
        return self.mainCharacterSettingsHolder.Get('lastHistoryTimeCleanTime', 0)

    def GetLastSeenNotificationId(self):
        return self.mainCharacterSettingsHolder.Get('lastSeenNotificationId', -1)

    def GetLastClearedNotificationId(self):
        return self.mainCharacterSettingsHolder.Get('lastClearedNotificationId', 0)

    def SetLastHistoryCleanTime(self, time):
        self.mainCharacterSettingsHolder.Set('lastHistoryTimeCleanTime', time)

    def SetLastClearedNotificationId(self, notificationID):
        self.mainCharacterSettingsHolder.Set('lastClearedNotificationId', notificationID)

    def SetLastSeenNotificationId(self, notificationID):
        self.mainCharacterSettingsHolder.Set('lastSeenNotificationId', notificationID)
