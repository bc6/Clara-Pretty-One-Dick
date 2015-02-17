#Embedded file name: notifications/client\notificationUI.py
import gatekeeper
from notifications.client.contactNotificationAdapter import ContactNotificationAdapter
from notifications.client.notificationSettings.notificationSettingHandler import NotificationSettingHandler
from notifications.common.notification import Notification
import blue
from carbon.common.script.sys.service import CoreService
from notifications.client.generator.notificationGenerator import NotificationGenerator
from notifications.client.notificationCenter import NotificationCenter
from notifications.client.notificationSettings.notificationSettingConst import ExperimentalConst
import localization
import gatekeeper.gatekeeperConst as gkConst

class NotificationUIService(CoreService):
    __guid__ = 'svc.notificationUIService'
    __notifyevents__ = ['OnNewNotificationReceived', 'OnSetDevice', 'OnLocalNotificationSettingChanged']
    __startupdependencies__ = ['settings', 'mailSvc', 'notificationSvc']

    def Run(self, memstream = None):
        self.notificationCenter = None
        self.notificationCache = None
        self.pendingNotificationCache = []
        self.cacheFillThread = None
        self.unreadCounter = 0
        self.notificationSettings = NotificationSettingHandler()
        self.notificationGenerator = NotificationGenerator()
        self.isEnabled = self.notificationSettings.GetNotificationWidgetEnabled()
        self.shouldShowOnEnable = False
        self.__developerMode = False
        self.contactNotificationAdapter = ContactNotificationAdapter()
        sm.RegisterNotify(self.contactNotificationAdapter)
        self.lastSeenMessageTime = self.notificationSettings.GetLastSeenTime()
        self.lastHistoryTimeCleanTime = self.notificationSettings.GetLastHistoryTimeCleanTime()
        self.lastSeenNotificationId = self.notificationSettings.GetLastSeenNotificationId()
        self.lastClearedNotificationId = self.notificationSettings.GetLastClearedNotificationId()

    def OnLocalNotificationSettingChanged(self):
        self.UpdateEnabledStatus()

    def Stop(self, memStream = None):
        CoreService.Stop(self, memStream)
        sm.UnregisterNotify(self.contactNotificationAdapter)

    def PlaySound(self, eventName):
        if self.notificationSettings.GetNotificationSoundEnabled():
            sm.GetService('audio').SendUIEvent(eventName)

    def ToggleDeveloperMode(self):
        print 'TogglingDeveloperMode'
        self.__developerMode = not self.__developerMode
        print 'DeveloperMode is ' + str(self.__developerMode)

    def IsDeveloperMode(self):
        return self.__developerMode

    def IsEnabled(self):
        return self.isEnabled

    def OnNewNotificationReceived(self, notification):
        if self.isEnabled:
            self._InsertNotification(notification)
            self._DisplayNotificationIfPossible(notification)

    def SpawnFakeNotifications(self):
        self.notificationGenerator.Start()

    def ResetUnreadCounter(self):
        if self.notificationCache and len(self.notificationCache) > 0:
            self._SetLastReadTime(self.notificationCache[0].created)
        self.unreadCounter = 0
        self._UpdateCounter()

    def _UpdateCounter(self):
        if self.notificationCenter:
            self.notificationCenter.SetBadgeValue(self.unreadCounter)
            if self.unreadCounter == 0:
                self.notificationCenter.hideBadge()
            else:
                self.notificationCenter.showBadge()

    def _IncrementCounter(self):
        self.unreadCounter = self.unreadCounter + 1
        self._UpdateCounter()

    def _SetLastReadTime(self, lastReadTimeStamp):
        self.lastSeenMessageTime = lastReadTimeStamp
        self.notificationSettings.SetLastSeenTime(self.lastSeenMessageTime)

    def _ShouldIncrementCounterForNotification(self, notification):
        notificationSetting = self.notificationSettings.LoadSettings()
        specificSetting = notificationSetting.get(notification.typeID)
        if specificSetting and specificSetting.showAtAll:
            return True
        return False

    def _IncrementCounterIfIShould(self, notification):
        if self._ShouldIncrementCounterForNotification(notification):
            self._IncrementCounter()

    def _InsertNotification(self, notification):
        self._IncrementCounterIfIShould(notification)
        if self.notificationCache is None:
            self.pendingNotificationCache.append(notification)
        else:
            self.notificationCache.insert(0, notification)

    def _DisplayNotificationIfPossible(self, notification):
        if self.notificationCenter:
            self.notificationCenter.DisplaySingleNotification(notification)

    def ClearHistory(self):
        self.lastHistoryTimeCleanTime = self.lastSeenMessageTime
        self.lastClearedNotificationId = self.lastSeenNotificationId
        self.notificationSettings.SetLastHistoryCleanTime(self.lastHistoryTimeCleanTime)
        self.notificationSettings.SetLastClearedNotificationId(self.lastClearedNotificationId)
        self.ClearCache()

    def UnClearHistory(self):
        self.lastHistoryTimeCleanTime = 0
        self.lastClearedNotificationId = 0
        self.lastSeenNotificationId = 0
        self.notificationSettings.SetLastHistoryCleanTime(self.lastHistoryTimeCleanTime)
        self.notificationSettings.SetLastClearedNotificationId(self.lastClearedNotificationId)
        self.SaveLastSeenNotificationId()
        self.ClearCache()

    def SaveLastSeenNotificationId(self):
        self.notificationSettings.SetLastSeenNotificationId(self.lastSeenNotificationId)

    def OnSetDevice(self):
        pass

    def _IsCacheInitialized(self):
        return self.notificationCache is not None

    def _CheckAndFillCache(self):
        if self.notificationCache is None:
            self.notificationCache = self._NotificationProvider(sortThem=False)
            self.notificationCache.extend(self.pendingNotificationCache)
            self.pendingNotificationCache = []
            self._SortNotifications(self.notificationCache)
            counter = 0
            for notification in self.notificationCache:
                if notification.created > self.lastSeenMessageTime and self._ShouldIncrementCounterForNotification(notification):
                    counter += 1
                self.lastSeenNotificationId = max(notification.notificationID, self.lastSeenNotificationId)

            self.SaveLastSeenNotificationId()
            self.unreadCounter = counter
            self._UpdateCounter()
            self._NotifyInitialized()

    def _NotifyInitialized(self):
        if self.notificationCenter:
            self.notificationCenter.SetCacheIsInitialized(True)

    def _NotifyUnInitialized(self):
        if self.notificationCenter:
            self.notificationCenter.SetCacheIsInitialized(False)

    def UpdateEnabledStatus(self):
        if self.notificationSettings.GetNotificationWidgetEnabled():
            self.SetEnabled(True)
        else:
            self.SetEnabled(False)

    def SetEnabled(self, value):
        if value is self.isEnabled:
            return
        if self.shouldShowOnEnable and value is True:
            self.isEnabled = True
            self.Show()
        else:
            self.TearDown()
            self.isEnabled = value

    def _StartCheckAndFillCacheThread(self):
        import uthread
        uthread.new(self._CheckAndFillCache)

    def Show(self):
        self.shouldShowOnEnable = True
        if self.isEnabled:
            self._ConstructNotificationCenter()
            self._StartCheckAndFillCacheThread()
        else:
            self.UpdateEnabledStatus()

    def ToggleEnabledFlag(self):
        if self.isEnabled:
            self.Hide()
            self.isEnabled = False
        else:
            self.isEnabled = True
            self.Show()

    def Hide(self):
        self.shouldShowOnEnable = False
        self.TearDown()

    def TearDown(self):
        if self.isEnabled:
            self._TearDownNotificationCenter()
        self.ClearCache(refillCache=False)

    def _TearDownNotificationCenter(self):
        if self.notificationCenter:
            self.notificationCenter.deconstruct()
            self.notificationCenter = None

    def _OnNotificationCenterReconstructed(self):
        self._UpdateCounter()

    def _ConstructNotificationCenter(self):
        if self.isEnabled:
            self._TearDownNotificationCenter()
            self.notificationCenter = NotificationCenter(onReconstructCallBack=self._OnNotificationCenterReconstructed, developerMode=self.IsDeveloperMode(), audioCallback=self.PlaySound)
            self.notificationCenter.Construct(notificationProviderFunction=self._PersonalCachedProvider)
            self.notificationCenter.SetCacheIsInitialized(self._IsCacheInitialized())
            self._UpdateCounter()

    def _PersonalCachedProvider(self):
        if self.notificationCache is None:
            self._CheckAndFillCache()
        else:
            self.ResetUnreadCounter()
        return self.notificationCache

    def _SortNotifications(self, notificationList):
        notificationList.sort(key=lambda notification: notification.created, reverse=True)

    def _NotificationProvider(self, sortThem = True):
        from notifications.client.development.skillHistoryProvider import SkillHistoryProvider
        skillNotifications = SkillHistoryProvider(onlyShowAfterDate=self.lastHistoryTimeCleanTime).provide()
        achievementNotifications = self.GetAchievementNotifications()
        restOfNotifications = sm.GetService('notificationSvc').GetAllFormattedNotifications(fromID=self.lastClearedNotificationId)
        sortedList = skillNotifications + restOfNotifications + achievementNotifications
        if sortThem:
            self._SortNotifications(sortedList)
        return sortedList

    def GetAchievementNotifications(self):
        if not gatekeeper.user.IsInCohort(gkConst.cohortPirateUnicornsNPETwo):
            return []
        from notifications.client.development.achievementHistoryProvider import AchievementHistoryProvider
        notifications = AchievementHistoryProvider(onlyShowAfterDate=self.lastHistoryTimeCleanTime).provide()
        achievementNotifications = sm.GetService('notificationSvc').FormatNotifications(notifications)
        return achievementNotifications

    def ClearCache(self, refillCache = True):
        self.notificationCache = None
        sm.GetService('notificationSvc').ClearAllNotificationsCache()
        self._NotifyUnInitialized()
        if refillCache:
            self._CheckAndFillCache()
