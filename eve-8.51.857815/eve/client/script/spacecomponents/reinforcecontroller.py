#Embedded file name: eve/client/script/spacecomponents\reinforcecontroller.py
"""
Controller for the activate component countdown UI.
"""
from eve.client.script.spacecomponents.countercontroller import BaseCounterController
from spacecomponents.client.messages import MSG_ON_REINFORCE_TIMER_UPDATED
from spacecomponents.common.componentConst import REINFORCE_CLASS
import blue
import logging
logger = logging.getLogger(__name__)
REINFORCE_TIMER_COLOR = (1.0, 0.2, 0.3, 1.0)

class ReinforceCounterController(BaseCounterController):
    __componentClass__ = REINFORCE_CLASS
    __counterColor__ = REINFORCE_TIMER_COLOR
    __counterLabel__ = 'UI/Inflight/SpaceComponents/Reinforce/TimerLabel'
    __timerFunc__ = blue.os.GetWallclockTime
    __countsDown__ = True
    __soundInitialEvent__ = 'counter_reinforced_play'
    __soundFinishedEvent__ = 'bounty_open_play'

    def __init__(self, *args):
        BaseCounterController.__init__(self, *args)
        self.componentRegistry.SubscribeToItemMessage(self.itemID, MSG_ON_REINFORCE_TIMER_UPDATED, self.UpdateTimerState)

    def UpdateTimerState(self, instance, slimItem):
        if slimItem.component_reinforce is not None:
            if not instance.isReinforced:
                if self.timer is not None:
                    logger.debug('%s Removing timer for %s', self.__class__.__name__, slimItem.itemID)
                    self.RemoveTimer()
            elif self.timer is None:
                logger.debug('%s Adding timer for %s', self.__class__.__name__, slimItem.itemID)
                self.AddTimer(instance.reinforceTimestamp, instance.attributes.durationSeconds)
