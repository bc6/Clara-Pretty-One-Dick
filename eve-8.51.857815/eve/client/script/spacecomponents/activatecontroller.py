#Embedded file name: eve/client/script/spacecomponents\activatecontroller.py
"""
Controller for the activate component countdown UI.
"""
from eve.client.script.spacecomponents.countercontroller import BaseCounterController
from spacecomponents.client.messages import MSG_ON_ACTIVATE_TIMER_UPDATED
from spacecomponents.common.componentConst import ACTIVATE_CLASS
import blue
import logging
logger = logging.getLogger(__name__)
ACTIVATE_TIMER_COLOR = (0.2, 1.0, 0.3, 1.0)

class ActivateCounterController(BaseCounterController):
    __componentClass__ = ACTIVATE_CLASS
    __counterColor__ = ACTIVATE_TIMER_COLOR
    __counterLabel__ = 'UI/Inflight/SpaceComponents/Activate/TimerLabel'
    __timerFunc__ = blue.os.GetSimTime
    __countsDown__ = False
    __soundInitialEvent__ = 'counter_activate_play'
    __soundFinishedEvent__ = 'bounty_open_play'

    def __init__(self, *args):
        BaseCounterController.__init__(self, *args)
        self.componentRegistry.SubscribeToItemMessage(self.itemID, MSG_ON_ACTIVATE_TIMER_UPDATED, self.UpdateTimerState)

    def UpdateTimerState(self, instance, slimItem):
        if slimItem.component_activate is not None:
            if instance.isActive:
                if self.timer is not None:
                    logger.debug('%s Removing timer for %s', self.__class__.__name__, slimItem.itemID)
                    self.RemoveTimer()
                    instance.UnsubscribeFromMessage(MSG_ON_ACTIVATE_TIMER_UPDATED, self.UpdateTimerState)
            elif self.timer is None:
                logger.debug('%s Adding timer for %s', self.__class__.__name__, slimItem.itemID)
                self.AddTimer(instance.activeTimestamp, instance.attributes.durationSeconds)
