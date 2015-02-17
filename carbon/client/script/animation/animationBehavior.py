#Embedded file name: carbon/client/script/animation\animationBehavior.py
"""
Base class for animation controller behaviors.
Contains base functionality and Corified versions of common functions needed.
"""

class AnimationBehavior(object):
    __guid__ = 'animation.animationBehavior'

    def Update(self, controller):
        """
        Implemented in derived classes, what do I do when the animation controller tells me to update?
        """
        pass

    def Reset(self):
        """
        Implemented in derived classes.
        """
        pass

    def OnAdd(self, controller):
        """
        Implemented in derived classes.
        Used for custom behavior for when this behavior is added to a controller
        """
        pass
