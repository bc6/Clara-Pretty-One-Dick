#Embedded file name: eve/client/script/ui/view\fadeFromCharRecustomToCQTransition.py
from eve.client.script.ui.view.fadeToCQTransition import FadeToCQTransition

class FadeFromCharRecustomToCQTransition(FadeToCQTransition):
    """
    Fade to background image and back state transition.
    This does everything FadeToCQTransition does but it cant be reopened
    because the char customization invalidates the entire CEF thing and it
    needs to be reloaded for the scene transition between those two to work
    """
    __guid__ = 'viewstate.FadeFromCharRecustomToCQTransition'

    def __init__(self, fadeTimeMS = 1000, fadeInTimeMS = None, fadeOutTimeMS = None, **kwargs):
        FadeToCQTransition.__init__(self, **kwargs)
        self.allowReopen = False
