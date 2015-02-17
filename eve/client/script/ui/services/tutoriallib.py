#Embedded file name: eve/client/script/ui/services\tutoriallib.py
from collections import namedtuple

class TutorialColor:
    __guid__ = 'tutorial.TutorialColor'
    HINT_FRAME = (32 / 255.0,
     223 / 255.0,
     159 / 255.0,
     1.0)
    WINDOW_FRAME = (89 / 255.0,
     89 / 255.0,
     89 / 255.0,
     1.0)
    BACKGROUND = (0, 0, 0, 0.8)


class TutorialConstants:
    __guid__ = 'tutorial.TutorialConstants'
    NUM_BLINKS = 3


TutorialPageState = namedtuple('TutorialPageState', 'tutorialID, pageNo, pageID, pageCount, sequenceID, VID, pageActionID')
