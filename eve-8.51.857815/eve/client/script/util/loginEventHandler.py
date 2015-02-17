#Embedded file name: eve/client/script/util\loginEventHandler.py
import blue

class LoginEventHandler:
    __notifyevents__ = ['OnClientStageChanged', 'OnNewState']

    def __init__(self):
        self.events = {}
        self.defaults = None
        sm.RegisterNotify(self)

    def OnClientStageChanged(self, what):
        self.events[what] = True

    def OnNewState(self, bp):
        self.events['newstate'] = True

    def WaitForEvent(self, what):
        """Waits for a single event. See WaitForEvents below."""
        while what not in self.events or not self.events[what]:
            blue.synchro.Yield()

        self.events[what] = False

    def WaitForEula(self):
        """ Wait for the client to be ready to login """
        self.WaitForEvent('login')

    def WaitForCharsel(self):
        viewState = sm.GetService('viewState')
        while not viewState.IsViewActive('charsel'):
            blue.synchro.Yield()


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('loginEventHandler', locals())
