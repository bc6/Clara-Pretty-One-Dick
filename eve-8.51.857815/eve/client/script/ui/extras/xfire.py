#Embedded file name: eve/client/script/ui/extras\xfire.py
"""
xFire is a third party application similar to msn which allows its users to monitor what their friends (and friends of friends) are playing.
This service allows us to send in information to be displayed to xFire friends of the user. Information sent now is the number of EVE players
at loggin time. Any information can be passed in here in (string)Key (string)Value format. The service updates the displayed user information
seen by friends in xFire every 10 minutes by default.
It is possible to update this information more frequently by setting the xfiredelay value in prefs.ini to some lower value. However xFire also
Throttles its updates to at least a minute interval.
"""
import service
import blue
import ctypes
import uthread
import sys
import extensions

class XFire(service.Service):
    __guid__ = 'svc.xfire'

    def __init__(self, *args):
        service.Service.__init__(self)
        self.messages = {}
        self.delay = prefs.GetValue('xfiredelay', 6000) * 1000
        self.xFireGameClient = extensions.GetXFireGameClient()
        self.state = service.SERVICE_RUNNING
        uthread.new(self.RunXFireLoop)

    def AddKeyValue(self, k, v):
        self.LogInfo('AddKeyValue', k, v)
        self.messages[k] = v

    def RemoveKeyValue(self, k):
        self.LogInfo('RemoveKeyValue', k)
        if self.messages.has_key(k):
            del self.messages[k]

    def RunXFireLoop(self):
        if not self.IsXFireLoaded():
            self.LogInfo('xFire is not loaded.')
            return
        while self.state == service.SERVICE_RUNNING:
            self.LogInfo('RunXFireLoop Running...')
            try:
                self.DoUpdateXFire()
            except Exception as e:
                self.LogError('RunXFireLoop Error: ', e)
                sys.exc_clear()

            blue.pyos.synchro.SleepWallclock(self.delay)

    def IsXFireLoaded(self):
        return self.xFireGameClient.IsLoaded()

    def DoUpdateXFire(self):
        self.LogInfo('DoUpdateXFire')
        self.xFireGameClient.SetClientData(self.messages)
        k = []
        v = []
        for key, val in self.messages.items():
            k.append(key)
            v.append(val)

        if k:
            cp = ctypes.c_char_p * len(k)
            k_cp = cp(*k)
            v_cp = cp(*v)
            self.LogInfo('Sending', len(k), ' key/val pairs to xFire...')
