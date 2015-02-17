#Embedded file name: eve/client/script/ui/shared\incursionSvc.py
from service import Service
import blue
from trinity.evePostProcess import POST_PROCESS_INCURSION_OVERLAY
import uthread
from pychartdir import XYChart, Transparent, PNG
import os
import talecommon as taleCommon
import localization
INCURSION_CHAT_WARNING_DELAY = 20
INCURSION_CHAT_CLOSE_DELAY = 120
WHITE = 16777215
BLACK = 0
GRAY = 8947848
DARKGRAY = 4473924
PLOT_OFFSET = 50
PLOT_RIGHT_MARGIN = 8
PLOT_BOTTOM_MARGIN = 45
LEGEND_OFFSET = 18
COLOR_HIGH_SEC = 34816
COLOR_LOW_SEC = 13404160
COLOR_NULL_SEC = 16711680
VISUAL_STYLE_FADE_TIME = 5.0 * const.SEC
INCURSION_CLASS_ID = 2

class IncursionSvc(Service):
    """
    service to act as the backbone of incursion UI interaction
    """
    __guid__ = 'svc.incursion'
    __notifyevents__ = ['OnTaleStart',
     'OnTaleEnd',
     'OnSessionChanged',
     'OnTaleData']
    __startupdependencies__ = ['visualEffect']

    def Run(self, *args):
        Service.Run(self, *args)
        self.incursionData = None
        self.enableSoundOverrides = False
        self.stationAudioPlaying = False
        self.addStationSoundThreadRunning = False
        self.isDisablingHud = False
        self.isActivatingHud = False
        self.constellationForJoinedTaleID = {}
        self.waitingIncursionChannelTaleID = set()
        self.rewardsByID = {}
        self.soundUrlByKey = {'hangar': 10004,
         const.groupStation: 10007,
         const.groupAsteroidBelt: 10003,
         'enterSystem': 10005}

    def OnTaleData(self, solarSystemID, data):
        """
        Sent when ever we enter a tale system
        """
        for taleData in data.itervalues():
            self.StartIncursion(taleData, fadeEffect=False, reason='Entered incursion system')

    def OnTaleStart(self, data):
        self.StartIncursion(data, fadeEffect=True, reason='Tale just started')

    def StartIncursion(self, data, fadeEffect = False, reason = None):
        """
        Note: there can never be two incursions on top of each other
        so this should only happen once per session change/tale start 
        """
        if data.templateClassID == INCURSION_CLASS_ID:
            self.LogInfo('Starting the incursion UI for tale', data.taleID, '. Reason:', reason)
            self.incursionData = data
            if session.solarsystemid and self._IsSystemInIncursion(session.solarsystemid):
                self._StartIncursionVisualEffects(session.solarsystemid)
            self.enableSoundOverrides = True
            self.JoinIncursionChat(data.taleID)
            soundURL = self.GetSoundUrlByKey('enterSystem')
            if soundURL is not None:
                sm.GetService('audio').SendUIEvent(soundURL)
            if session.stationid is not None:
                self.AddIncursionStationSoundIfApplicable()
            sm.GetService('infoPanel').UpdateIncursionsPanel()

    def OnTaleEnd(self, taleID):
        self.LogInfo('OnTaleEnd', taleID)
        self.enableSoundOverrides = False
        if session.solarsystemid:
            self._StopIncursionVisualEffects(session.solarsystemid)
        self.incursionData = None
        sm.GetService('infoPanel').UpdateIncursionsPanel()
        self.StartTimeoutOfIncursionChat(taleID)

    def OnSessionChanged(self, isremote, sess, change):
        """We want to disconnect the chat and remove the ui when we leave"""
        for taleID in self.constellationForJoinedTaleID:
            self.StartTimeoutOfIncursionChat(taleID)

        if 'solarsystemid' in change:
            oldSolarsystem, newSolarsystem = change['solarsystemid']
            if self.incursionData:
                if self._IsSystemInIncursion(oldSolarsystem):
                    self._StopIncursionVisualEffects(oldSolarsystem)
                if self._IsSystemInIncursion(newSolarsystem):
                    self._StartIncursionVisualEffects(newSolarsystem)
        if 'solarsystemid2' in change:
            oldSolarsystem, newSolarsystem = change['solarsystemid2']
            if self.incursionData:
                if self._IsSystemInIncursion(oldSolarsystem):
                    self.enableSoundOverrides = False
                if self._IsSystemInIncursion(newSolarsystem):
                    self.enableSoundOverrides = True
                else:
                    self.incursionData = None
                sm.GetService('infoPanel').UpdateIncursionsPanel()
        if 'stationid' in change:
            self.stationAudioPlaying = False
            oldStationID, newStationID = change['stationid']
            if newStationID != None:
                self.AddIncursionStationSoundIfApplicable()

    def _IsSystemInIncursion(self, solarsystemID):
        return self.incursionData is not None and solarsystemID in self.incursionData.incursedSystems

    def _StartIncursionVisualEffects(self, solarsystemID):
        self.visualEffect.ActivateVisualEffect(POST_PROCESS_INCURSION_OVERLAY)
        self.visualEffect.EnableGodrays(solarsystemID)

    def _StopIncursionVisualEffects(self, solarsystemID):
        self.visualEffect.DeactivateVisualEffect(POST_PROCESS_INCURSION_OVERLAY)
        self.visualEffect.DisableGodrays(solarsystemID)

    def _EndTimeoutOfIncursionChat(self, taleID):
        """Handle all cleanup of when the worker thread is exiting"""
        if taleID in self.waitingIncursionChannelTaleID:
            self.waitingIncursionChannelTaleID.remove(taleID)

    def IsTaleInTheCurrentSystem(self, taleID):
        """This figures out if the tale in question is running in our current solarsystem"""
        if self.incursionData is not None:
            if self.incursionData.taleID == taleID:
                return True
        return False

    def IsIncursionActive(self):
        """ Returns True if an incursion is active in current system """
        if self.incursionData is not None:
            return self.incursionData.templateClassID == INCURSION_CLASS_ID
        return False

    def GetActiveIncursionData(self):
        return self.incursionData

    def TimeoutOfIncursionChat_Thread(self, taleID):
        """Worker thread which waits and tests if we have gotten confirmation
        that we are still in a tale, and if not then we close the chat after
        two minutes"""
        lsc = sm.GetService('LSC')
        blue.pyos.synchro.SleepWallclock(INCURSION_CHAT_WARNING_DELAY * 1000)
        if self.IsTaleInTheCurrentSystem(taleID):
            self._EndTimeoutOfIncursionChat(taleID)
            return
        window = lsc.GetChannelWindow(('incursion' + str(taleID), taleID))
        if window:
            window.Speak(localization.GetByLabel('UI/Incursion/LeaveChat', minutesRemaining=INCURSION_CHAT_CLOSE_DELAY / 60), const.ownerSystem)
        blue.pyos.synchro.SleepWallclock(INCURSION_CHAT_CLOSE_DELAY * 1000)
        if self.IsTaleInTheCurrentSystem(taleID):
            self._EndTimeoutOfIncursionChat(taleID)
            return
        lsc.LeaveChannel([('incursion' + str(taleID), taleID)])
        if taleID in self.constellationForJoinedTaleID:
            del self.constellationForJoinedTaleID[taleID]
        self._EndTimeoutOfIncursionChat(taleID)

    def StartTimeoutOfIncursionChat(self, taleID):
        """Start the thread which handles the timeout of the chat
        this timeout is canceled if the tale information is received"""
        if taleID not in self.waitingIncursionChannelTaleID:
            self.waitingIncursionChannelTaleID.add(taleID)
            uthread.new(self.TimeoutOfIncursionChat_Thread, taleID).context = 'IncursionSvc::StartTimeoutOfIncursionChat'

    def JoinIncursionChat(self, taleID):
        channelID = ('incursion' + str(taleID), taleID)
        lsc = sm.GetService('LSC')
        lsc.JoinChannel([channelID])
        if taleID not in self.constellationForJoinedTaleID:
            self.constellationForJoinedTaleID[taleID] = session.constellationid
            window = lsc.GetChannelWindow(channelID)
            if window:
                constellationName = cfg.evelocations.Get(session.constellationid).name
                window.Speak(localization.GetByLabel('UI/Incursion/Announcement', constellationName=constellationName), const.ownerSystem)

    def GetConstellationNameFromTaleIDForIncursionChat(self, taleID):
        """This returns the constellation name which a tale is in
        Note: The only tales which can be looked up by this function is the ones which
        we have joined the chat for.
        If we cannot perform the lookup we will return the empty string"""
        if taleID in self.constellationForJoinedTaleID:
            return cfg.evelocations.Get(self.constellationForJoinedTaleID[taleID]).name
        return ''

    def GetDelayedRewardsByGroupIDs(self, rewardGroupIDs):
        rewardGroupIDs.sort()
        rewardsByRewardGroupID = sm.RemoteSvc('rewardMgr').GetDelayedRewardsByGroupIDs(tuple(rewardGroupIDs))
        return rewardsByRewardGroupID

    def GetRewardData(self, rewardID):
        reward = self.rewardsByID.get(rewardID, None)
        if not reward:
            reward = sm.RemoteSvc('rewardMgr').GetRewardData(rewardID)
        return reward

    def GetMaxRewardValue(self, rewardTables, rewardTypeID):
        """Returns the largest qualtity value from the rewardtables provided"""
        largestValue = 0
        for r in rewardTables:
            if r.rewardTypeID == rewardTypeID:
                largestValue = max((e.quantity for e in r.entries))

        return largestValue

    def GetMaxRewardValueByID(self, rewardID, rewardTypeID):
        """Return the largest quantity value from all the reward tables in rewardID"""
        reward = self.GetRewardData(rewardID)
        largestValue = 0
        for rewardCriteria, rewardTables in reward.immediateRewards.iteritems():
            largestValue = self.GetMaxRewardValue(rewardTables, rewardTypeID)

        for rewardCriteria, rewardTables in reward.delayedRewards.iteritems():
            largestValue = max(largestValue, self.GetMaxRewardValue(rewardTables, rewardTypeID))

        return largestValue

    def GetMaxRewardPlayerCount(self, rewardTables):
        return max((table.entries[-1].playerCount for table in rewardTables))

    def GetMinRewardPlayerCount(self, rewardTables):
        return min((table.entries[0].playerCount for table in rewardTables))

    def GetQuantityForCount(self, rewardTable, count):
        quantity = 0
        for entry in rewardTable.entries:
            if entry.playerCount <= count:
                quantity = entry.quantity
            else:
                break

        return quantity

    def DoRewardChart(self, rewardID, size, icon):
        path = 'cache://Pictures/Rewards/rewardchart2_%s_%d_%d.png' % (session.languageID, size, rewardID)
        res = blue.ResFile()
        try:
            if res.Open(path):
                icon.LoadTexture(path)
                icon.SetRect(0, 0, size, size)
            else:
                uthread.new(self.DoRewardChart_Thread, rewardID, size, icon).context = 'DoRewardChart'
        finally:
            res.Close()

    def DoRewardChart_Thread(self, rewardID, size, icon):
        """This function is generating the reward graph for the incursion journal
        The image is build opon data from the reward system, which is cached with the policy never, None, None"""
        reward = self.GetRewardData(rewardID)
        maxRewardValue = 0
        minPlayerCount = 0
        maxPlayerCount = 0
        allSecurityBandTable = None
        lowSecurityBandTable = None
        highSecurityBandTable = None
        for rewardCriteria, rewardTables in reward.immediateRewards.iteritems():
            if not rewardTables:
                continue
            if rewardCriteria == const.rewardCriteriaAllSecurityBands:
                maxRewardValue = self.GetMaxRewardValue(rewardTables, const.rewardTypeISK)
                minPlayerCount = self.GetMinRewardPlayerCount(rewardTables)
                maxPlayerCount = self.GetMaxRewardPlayerCount(rewardTables)
                allSecurityBandTable = rewardTables[0]
                break
            if rewardCriteria == const.rewardCriteriaHighSecurity:
                highSecurityBandTable = rewardTables[0]
            elif rewardCriteria == const.rewardCriteriaLowSecurity:
                lowSecurityBandTable = rewardTables[0]
            else:
                continue
            maxRewardValue = max(maxRewardValue, self.GetMaxRewardValue(rewardTables, const.rewardTypeISK))
            minPlayerCount = min(minPlayerCount, self.GetMinRewardPlayerCount(rewardTables))
            maxPlayerCount = max(maxPlayerCount, self.GetMaxRewardPlayerCount(rewardTables))

        scale = 1.0 / maxRewardValue
        majorTick = (maxPlayerCount - minPlayerCount) / 4
        data = []
        labels = []
        for x in xrange(minPlayerCount, maxPlayerCount + 1):
            if allSecurityBandTable is not None:
                quantity = self.GetQuantityForCount(allSecurityBandTable, x) * scale
                data.append(quantity)
            else:
                quantityHigh = self.GetQuantityForCount(highSecurityBandTable, x) * scale
                quantityLow = self.GetQuantityForCount(lowSecurityBandTable, x) * scale
                data.append((quantityHigh, quantityLow))
            labels.append(str(x))

        chart = XYChart(size, size, BLACK, GRAY, False)
        chart.setPlotArea(PLOT_OFFSET, PLOT_OFFSET, size - PLOT_OFFSET - PLOT_RIGHT_MARGIN, size - PLOT_OFFSET - PLOT_BOTTOM_MARGIN, DARKGRAY, -1, -1, GRAY, Transparent)
        if localization.util.GetLanguageID() == localization.const.LOCALE_SHORT_ENGLISH:
            font = 'arial.ttf'
            titleFont = 'arialbd.ttf'
        else:
            font = titleFont = uicore.font.GetFontDefault()
        chart.addLegend(LEGEND_OFFSET, LEGEND_OFFSET, 0, font, 8).setBackground(Transparent)
        legend = chart.getLegend()
        legend.setFontColor(WHITE)
        chart.addTitle(localization.GetByLabel('UI/Incursion/Reward/Title'), titleFont, 12, WHITE).setBackground(Transparent)
        yAxis = chart.yAxis()
        yAxis.setTitle(localization.GetByLabel('UI/Incursion/Reward/PayoutMultiplier'), font, 10, WHITE)
        yAxis.setColors(GRAY, WHITE)
        yAxis.setLinearScale(0, 1.02, 0.5, 0.25)
        xAxis = chart.xAxis()
        xAxis.setLabels(labels)
        xAxis.setLabelStep(majorTick)
        xAxis.setColors(GRAY, WHITE)
        xAxis.setTitle(localization.GetByLabel('UI/Incursion/Reward/NumberPilots'), font, 9, WHITE)
        layer = chart.addLineLayer2()
        layer.setLineWidth(1)
        if allSecurityBandTable is not None:
            layer.addDataSet(data, COLOR_HIGH_SEC, localization.GetByLabel('UI/Common/Ratio'))
        else:
            dataHigh, dataLow = zip(*data)
            layer.addDataSet(dataHigh, COLOR_HIGH_SEC, localization.GetByLabel('UI/Common/HighSec'))
            layer.addDataSet(dataLow, COLOR_NULL_SEC, localization.GetByLabel('UI/Common/LowNullSec'))
        directory = os.path.normpath(os.path.join(blue.paths.ResolvePath(u'cache:/'), 'Pictures', 'Rewards'))
        if not os.path.exists(directory):
            os.makedirs(directory)
        pictureName = 'rewardchart2_%s_%d_%d.png' % (session.languageID, size, rewardID)
        resPath = u'cache:/Pictures/Rewards/' + pictureName
        path = os.path.join(directory, pictureName)
        imageBuffer = chart.makeChart2(PNG)
        f = open(path, 'wb')
        f.write(imageBuffer)
        f.close()
        icon.LoadTexture(resPath)
        icon.SetRect(0, 0, size, size)

    def GetSoundUrlByKey(self, key):
        """
        Get a sound url by key if any is registered
        key: can be a item group or a string
        return a soundUrl or None if no key is found
        """
        if self.enableSoundOverrides == False:
            return
        soundID = self.soundUrlByKey.get(key, None)
        if soundID is not None:
            soundRecord = cfg.sounds.GetIfExists(soundID)
            if soundRecord is None:
                self.LogError('Unable to find a sound for key', key, 'and soundID', soundID)
                soundUrl = None
            else:
                soundUrl = soundRecord.soundFile
        else:
            soundUrl = None
        return soundUrl

    def AddIncursionStationSoundIfApplicable(self):
        if not self.addStationSoundThreadRunning and self.enableSoundOverrides:
            self.addStationSoundThreadRunning = True
            uthread.new(self.AddIncursionStationSoundIfApplicableThread).context = 'incursionSvc::AddIncursionStationSoundIfApplicableThread'

    def AddIncursionStationSoundIfApplicableThread(self):
        count = 0
        success = False
        while success == False and count < 60:
            blue.synchro.SleepWallclock(1000)
            count += 1
            if session.stationid is None:
                success = True
                break
            try:
                if not self.stationAudioPlaying:
                    activeScene = sm.GetService('sceneManager').GetRegisteredScene('hangar')
                    stringToMatch = 'invisible_sound_locator_'
                    soundLocator = FindSoundLocatorThatStartsWith(activeScene, stringToMatch)
                    addedSound = self.GetSoundUrlByKey('hangar')
                    if addedSound is not None and soundLocator is not None:
                        ReplaceHangarSound(soundLocator, addedSound)
                        self.stationAudioPlaying = True
                        success = True
            except:
                self.LogInfo('Could not add incursion station sound trying again in 1 second')

        if success == False:
            self.LogError('Incursion station audio could not be added after 60 tries')
        self.addStationSoundThreadRunning = False


def FindSoundLocatorThatStartsWith(scene, startingString):
    for transform in scene.objects:
        if transform.name.startswith(startingString):
            return transform


def ReplaceHangarSound(soundLocator, soundEvent):
    if not soundLocator.observers:
        return
    for objects in soundLocator.observers:
        objects.observer.SendEvent('fade_out')

    soundLocator.observers[0].observer.SendEvent(soundEvent[6:])
