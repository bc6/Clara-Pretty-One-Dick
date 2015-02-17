#Embedded file name: eve/client/script/incarna/animation/behaviours\walkTypeBehaviour.py
"""
Implements the response to slope detection for the Incarna animation network
"""
from carbon.client.script.animation.animationBehavior import AnimationBehavior
import blue
WALK_FLAT = 0
WALK_DOWN = -1
WALK_UP = 1
WALK_END_DELAY = int(0.15 * const.SEC)

class WalkTypeBehaviour(AnimationBehavior):
    """
    Implements the response to slope detection for the Incarna animation network
    """
    __guid__ = 'animation.walkTypeBehaviour'

    def __init__(self):
        AnimationBehavior.__init__(self)
        self.previousWalkVersion = WALK_FLAT
        self.returnToWalkFlatTime = 0.0

    def Update(self, controller):
        """
        Based on the slope detection heuristic pass in appropriate control parameters
        to the animation network. Also does some handling of dirty results coming from the
        heuristic.
        """
        walkVersion = WALK_FLAT
        if controller.slopeType is const.INCARNA_STEPS_UP:
            walkVersion = WALK_UP
        elif controller.slopeType is const.INCARNA_STEPS_DOWN:
            walkVersion = WALK_DOWN
        if walkVersion is not WALK_FLAT:
            self.returnToWalkFlatTime = blue.os.GetWallclockTime() + WALK_END_DELAY
        if blue.os.GetWallclockTime() < self.returnToWalkFlatTime and walkVersion is WALK_FLAT:
            walkVersion = self.previousWalkVersion
        controller.SetControlParameter('Slope', walkVersion)
        self.previousWalkVersion = walkVersion

    def Reset(self):
        """
        Reset behaviour back to start conditions.
        """
        self.previousWalkVersion = WALK_FLAT
        self.returnToWalkFlatTime = 0.0
