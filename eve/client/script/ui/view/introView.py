#Embedded file name: eve/client/script/ui/view\introView.py
from eve.client.script.ui.login.intro import Intro
from viewstate import View
import trinity

class IntroView(View):
    """
    The base class for a view. It consists of a UI root container and a scene.
    The view is registered for notify event by the view manager and will receive them while active or visible
    """
    __guid__ = 'viewstate.IntroView'
    __notifyevents__ = []
    __dependencies__ = []
    __layerClass__ = Intro

    def __init__(self):
        View.__init__(self)

    def LoadView(self, **kwargs):
        pass

    def UnloadView(self):
        """Used for cleaning up after the view has served its purpose"""
        pass
