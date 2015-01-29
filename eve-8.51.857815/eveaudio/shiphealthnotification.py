#Embedded file name: eveaudio\shiphealthnotification.py
from brennivin import itertoolsext
from eve.common.lib.appConst import soundNotifications

class SoundNotification(object):

    def __init__(self, keyName):
        if isinstance(keyName, int):
            index = keyName
            namesToIndices = soundNotifications.get('NameToIndices')
            keyName = itertoolsext.first([ k for k, v in namesToIndices.items() if v == index ])
        notification = soundNotifications.get(keyName)
        self.activeFlagSettingsName = keyName + 'NotificationEnabled'
        self.healthThresholdSettingsName = keyName + 'Threshold'
        self.defaultThreshold = notification.get('defaultThreshold')
        self.notificationEventName = notification.get('soundEventName')
        self.localizationLabel = notification.get('localizationLabel')
        self.defaultStatus = notification.get('defaultStatus')
        self.hasBeenNotified = False
        self.name = keyName


class ShipSoundNotifications(object):

    def __init__(self):
        self.shield = SoundNotification('shield')
        self.armour = SoundNotification('armour')
        self.hull = SoundNotification('hull')
        self.capacitor = SoundNotification('capacitor')
        self.cargoHold = SoundNotification('cargoHold')


class ShipHealthNotifier(object):
    """
        Takes care of sending the UI warning sounds if health parameters go below the user settings for that item.
    """

    def __init__(self, sendEvent):
        self.soundNotifications = ShipSoundNotifications()
        self.sendEvent = sendEvent

    def OnDamageStateChange(self, shipID, damageState):
        """
            Check whether we need to notify the user about the damageState or not.
            This gets called from the game each time your damage state changes.
        """
        if session.shipid != shipID:
            return
        self.ProcessNotification(self.soundNotifications.shield, damageState[0])
        self.ProcessNotification(self.soundNotifications.armour, damageState[1])
        self.ProcessNotification(self.soundNotifications.hull, damageState[2])

    def OnCapacitorChange(self, currentCharge, maxCharge, percentageLoaded):
        """
            Listens for capacitor changes and sends a warning if the capacitor goes below what is indicated
            by the const file.
        
            After the capacitor goes back above the const level the system will reset and be ready
            to warn the player again.
        
            ARGUMENTS:
                currentCharge           A number representing the current charge of the capacitor
                maxCharge               A number representing the highest possible charge of the capacitor
                percentageLoaded        A number the represents the current percentage level of the capacitor
        """
        self.ProcessNotification(self.soundNotifications.capacitor, percentageLoaded)

    def OnCargoHoldChange(self, shipID, cargoHoldState, item, change):
        """
        Processes the cargo hold state and checks it against the threshold for the cargohold usage
        """
        if cargoHoldState.capacity == 0:
            return
        if shipID in item or shipID in change.values():
            cargoHoldFree = cargoHoldState.capacity - cargoHoldState.used
            percentageUsed = cargoHoldFree / cargoHoldState.capacity
            self.ProcessNotification(self.soundNotifications.cargoHold, percentageUsed)

    def ProcessNotification(self, soundNotification, currentDamageStateValue):
        """
        Processes a ship health state value and checks it against the settings threshold for that health state
        :type soundNotification: SoundNotification
        :param soundNotification: all values related to a sound notification as a SoundNotification class
        :param currentDamageStateValue: the current health value of the state to be processed 0.0 - 1.0
        :return:
        """
        enabled = settings.user.notifications.Get(soundNotification.activeFlagSettingsName, True)
        if not enabled:
            return
        damageStateThreshold = settings.user.notifications.Get(soundNotification.healthThresholdSettingsName, soundNotification.defaultThreshold)
        thresholdReached = currentDamageStateValue <= damageStateThreshold
        self._SendNotificationIfNeeded(soundNotification, thresholdReached)

    def _SendNotificationIfNeeded(self, soundNotification, thresholdReached):
        alreadyNotified = soundNotification.hasBeenNotified
        if thresholdReached and not alreadyNotified:
            self.sendEvent(soundNotification.notificationEventName)
            soundNotification.hasBeenNotified = True
        elif alreadyNotified:
            soundNotification.hasBeenNotified = thresholdReached
