#Embedded file name: eve/client/script/spacecomponents\countercontroller.py
"""
Base Controller for component countdown UI.
"""
import uthread
from eve.client.script.ui.control.countdownTimer import CountdownTimer, TIMER_RUNNING_OUT_NO_ANIMATION
import localization
import blue
import logging
logger = logging.getLogger(__name__)

class BaseCounterController(object):
    __componentClass__ = 'None'
    __counterColor__ = (1.0, 1.0, 1.0, 1.0)
    __counterLabel__ = ''
    __timerFunc__ = blue.os.GetWallclockTime
    __countsDown__ = False
    __soundInitialEvent__ = None
    __soundLoopPlayEvent__ = None
    __soundLoopStopEvent__ = None
    __soundFinishedEvent__ = None

    def __init__(self, bracket, componentRegistry, slimItem):
        logger.debug('%s created for item %s', self.__class__.__name__, slimItem.itemID)
        self.itemID = slimItem.itemID
        self.bracket = bracket
        self.componentRegistry = componentRegistry
        self.timer = None
        self.endTime = None
        self.CreateTimerIfAppropriate(slimItem)

    def CreateTimerIfAppropriate(self, slimItem):
        instance = self.componentRegistry.GetComponentForItem(slimItem.itemID, self.__componentClass__)
        self.UpdateTimerState(instance, slimItem)

    def AddTimer(self, endTime, duration):
        self.endTime = endTime
        self.timer = CountdownTimer(name='ComponentCounter', parent=self.bracket, color=self.__counterColor__, countsDown=self.__countsDown__, timerFunc=self.__timerFunc__, timerRunningOutAnimation=TIMER_RUNNING_OUT_NO_ANIMATION)
        self.PlayInitialSound()
        self.timer.SetSoundLoop(self.__soundLoopPlayEvent__, self.__soundLoopStopEvent__)
        self.timer.SetExpiryTime(endTime, long(duration * const.SEC))
        self.bracket.SetSubLabelCallback(self.UpdateTimerLabel)

    def RemoveTimer(self):
        if self.timer:
            uthread.new(self.timer.EndAnimation)
            self.timer = None
            self.bracket.SetSubLabelCallback(None)
            self.PlayEndSound()

    def UpdateTimerState(self, instance, slimItem):
        raise NotImplementedError('You need to implement the specific component logic')

    def UpdateTimerLabel(self):
        if self.timer is None:
            self.bracket.displaySubLabel = None
            return
        timeLeft = long(max(0, self.endTime - self.__timerFunc__()))
        return u'{label}: {time}'.format(label=localization.GetByLabel(self.__counterLabel__), time=localization.formatters.FormatTimeIntervalShortWritten(timeLeft, showFrom='day', showTo='second'))

    def GetHorizontalLabelPixelOffset(self):
        if self.timer is None:
            return 0
        return 6

    def PlayEndSound(self):
        if self.__soundFinishedEvent__ is not None:
            sm.GetService('audio').SendUIEvent(self.__soundFinishedEvent__)

    def PlayInitialSound(self):
        if self.__soundInitialEvent__ is not None:
            sm.GetService('audio').SendUIEvent(self.__soundInitialEvent__)
