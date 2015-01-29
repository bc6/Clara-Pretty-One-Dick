#Embedded file name: carbon/client/script/localization\localizationClient.py
import service
import blue
import uthread
import localization
import localization.settings
from localization.logger import LogInfo

class LocalizationClient(service.Service):
    __guid__ = 'svc.localizationClient'
    __notifyevents__ = ['OnSessionChanged', 'OnUpdateLocalizationTextCache']

    def __init__(self):
        service.Service.__init__(self)

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        self.broadcasting = False

    def OnSessionChanged(self, isremote, sess, change):
        if 'charid' in change and change['charid'][0] is None:
            if sess.role & service.ROLE_QA == service.ROLE_QA:
                sm.RemoteSvc('localizationServer').UpdateLocalizationQAWrap(localization.settings.qaSettings.LocWrapSettingsActive())
            hashData = localization.GetHashDataDictionary()
            if len(hashData) > 0 and not blue.pyos.packaged:
                LogInfo('Localization Client: preparing to load initial text and label data from server')
                sm.RemoteSvc('localizationServer').GetAllTextChanges(hashData)
                LogInfo('Localization Client: done asking for initial text and label data from server')

    def OnUpdateLocalizationTextCache(self, cacheData):
        """
        Called from the server to update text cache. (will not be receiving this on LIVE)
        """
        messagePerLanguage, metaDataPerLanguage, labelsDict = cacheData
        if messagePerLanguage or metaDataPerLanguage or labelsDict:
            localization.UpdateTextCache(messagePerLanguage, metaDataPerLanguage, labelsDict)
            if not self.broadcasting:
                self.broadcasting = True
                uthread.new(self.DeferredBroadcastMessage)

    def DeferredBroadcastMessage(self):
        blue.synchro.SleepWallclock(30000)
        if prefs.GetValue('localizationUpdateInChat', 0):
            sm.GetService('LSC').LocalEchoAll('<color=red>Your localization content has been updated.</color>', 'Localization')
        else:
            sm.GetService('gameui').Say('Your localization content has been updated.')
        self.broadcasting = False
