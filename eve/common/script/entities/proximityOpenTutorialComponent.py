#Embedded file name: eve/common/script/entities\proximityOpenTutorialComponent.py
"""
Tutorial component that contains information relevant for triggering
tutorials associated with entities.
"""

class ProximityOpenTutorialComponent:
    __guid__ = 'tutorial.ProximityOpenTutorialComponent'

    def __init__(self):
        self.tutorialID = None
        self.radius = None
