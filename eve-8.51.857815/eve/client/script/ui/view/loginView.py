#Embedded file name: eve/client/script/ui/view\loginView.py
"""
login screen view
"""
from viewstate import View
from eve.client.script.ui.login.loginII import Login

class LoginView(View):
    """
    The base class for a view. It consists of a UI root container and a scene.
    The view is registered for notify event by the view manager and will receive them while active or visible
    """
    __guid__ = 'viewstate.LoginView'
    __notifyevents__ = []
    __dependencies__ = []
    __layerClass__ = Login
    __progressText__ = None

    def __init__(self):
        View.__init__(self)

    def UnloadView(self):
        """Used for cleaning up after the view has served its purpose"""
        View.UnloadView(self)
