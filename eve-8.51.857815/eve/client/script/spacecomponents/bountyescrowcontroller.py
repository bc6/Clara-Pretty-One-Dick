#Embedded file name: eve/client/script/spacecomponents\bountyescrowcontroller.py
"""
Controller for the activate component countdown UI.
"""
from carbon.common.lib import const
from eve.client.script.spacecomponents.countercontroller import BaseCounterController
from spacecomponents.client.messages import MSG_ON_BOUNTYESCROW_TIMER_UPDATED
from spacecomponents.common.componentConst import BOUNTYESCROW_CLASS
import spacecomponents.common.components.bountyEscrow as bountyEscrow
import blue
import logging
logger = logging.getLogger(__name__)
BOUNTYESCROW_TIMER_COLOR = (1.0, 1.0, 1.0, 1.0)

class BountyEscrowCounterController(BaseCounterController):
    __componentClass__ = BOUNTYESCROW_CLASS
    __counterColor__ = BOUNTYESCROW_TIMER_COLOR
    __counterLabel__ = 'UI/Inflight/SpaceComponents/BountyEscrow/TimerLabel'
    __timerFunc__ = blue.os.GetSimTime
    __countsDown__ = False
    __soundInitialEvent__ = 'counter_bounty_play'
    __soundFinishedEvent__ = 'bounty_open_play'

    def __init__(self, *args):
        BaseCounterController.__init__(self, *args)
        self.componentRegistry.SubscribeToItemMessage(self.itemID, MSG_ON_BOUNTYESCROW_TIMER_UPDATED, self.UpdateTimerState)

    def ESSUnlocking(self, slimItem):
        if slimItem.unlockState is not None:
            if slimItem.unlockState is not None and slimItem.unlockState[0] == 'unlocking':
                return True
        return False

    def ESSSpawningTags(self, slimItem):
        if slimItem.unlockState is not None and slimItem.unlockState[0] == 'spawningTags':
            return True
        return False

    def ESSLocked(self, slimItem):
        if slimItem.unlockState is not None and slimItem.unlockState[0] == 'locked':
            return True
        return False

    def _TryRemoveTimer(self):
        if self.timer is not None:
            self.RemoveTimer()

    def UpdateTimerState(self, instance, slimItem):
        state = slimItem.unlockState
        if state is not None:
            if bountyEscrow.IsUnlocking(state):
                if self.timer is None and instance.unlockTimestamp and instance.unlockSeconds:
                    self.AddTimer(instance.unlockTimestamp + int(instance.unlockSeconds) * const.SEC, int(instance.unlockSeconds))
                    return
        self._TryRemoveTimer()
