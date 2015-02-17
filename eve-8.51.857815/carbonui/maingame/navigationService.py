#Embedded file name: carbonui/maingame\navigationService.py
import carbon.common.script.sys.service as service
import carbonui.const as uiconst
import uthread
import blue

class CoreNavigationService(service.Service):
    __guid__ = 'svc.navigation'
    __notifyevents__ = ['OnSessionChanged', 'OnMapShortcut']

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)
        self.hasControl = True
        self.hasFocus = False
        self.navKeys = None
        self.lastKeyRunning = False
        self.keyDownCookie = None
        self.keyUpCookie = None
        self.appfocusCookie = None
        self.lastStrafe = None
        self.lastRotate = None
        self.keyPoller = None
        self.cameraClient = sm.GetService('cameraClient')

    def Stop(self, stream):
        service.Service.Stop(self)

    def HasControl(self):
        return self.hasFocus and self.hasControl

    def GetConfigValue(self, data, name, default):
        """
        Returns the specified configration value using the app specific config systems
        """
        return default

    def OnSessionChanged(self, isRemote, sess, change):
        if 'worldspaceid' in change:
            oldworldspaceid = change['worldspaceid'][0]
            worldspaceid = change['worldspaceid'][1]
            if oldworldspaceid:
                self.UnRegisterKeyEvents()
            if worldspaceid:
                self.RegisterKeyEvents()

    def RecreatePlayerMovement(self):
        """
        This function must be reimplemented by an application specific navigation service.
        It takes care of actually performing movement as a result of the input provided.
        """
        raise NotImplementedError(self.RecreatePlayerMovement.__doc__)

    def CheckKeyState(self):
        """
        Try to update avatar movement by polling keystate. We are avoiding the command
        service here because the command service gives execution control back to the 
        scheduler 3(!) times which is just causing too much uncertainity in terms of
        responsiveness.
        """
        while True:
            if self.state == service.SERVICE_RUNNING:
                if self.hasControl:
                    self.RecreatePlayerMovement()
            elif self.state == service.SERVICE_STOPPED:
                return
            blue.synchro.Yield()

    def RegisterKeyEvents(self):
        self.keyPoller = uthread.new(self.CheckKeyState)
        self.keyPoller.context = 'EveNavigationService::CheckKeyState'
        self.keyDownCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_KEYDOWN, self.OnGlobalKeyDownCallback)
        self.keyUpCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_KEYUP, self.OnGlobalKeyUpCallback)
        self.appfocusCookie = uicore.event.RegisterForTriuiEvents(uiconst.UI_ACTIVE, self.OnGlobalAppFocusChange)

    def UnRegisterKeyEvents(self):
        if self.keyPoller is not None:
            self.keyPoller.kill()
            self.keyPoller = None
        if self.keyDownCookie:
            uicore.event.UnregisterForTriuiEvents(self.keyDownCookie)
            self.keyDownCookie = None
        if self.keyUpCookie:
            uicore.event.UnregisterForTriuiEvents(self.keyUpCookie)
            self.keyUpCookie = None
        if self.appfocusCookie:
            uicore.event.UnregisterForTriuiEvents(self.appfocusCookie)
            self.appfocusCookie = None

    def _UpdateMovement(self, vkey):
        """
        This function must be reimplemented by an application specific navigation service.
        It takes care of translating the incoming vkey to movement or navigation related
        commands which are then picked up by RecreatePlayerMovement.
        """
        raise NotImplementedError(self._UpdateMovement.__doc__)

    def OnGlobalKeyDownCallback(self, *args, **kwds):
        return True

    def OnGlobalKeyUpCallback(self, *args, **kwds):
        self.RecreatePlayerMovement()
        return True

    def OnGlobalAppFocusChange(self, *args, **kwds):
        self.RecreatePlayerMovement()
        return True

    def UpdateMovement(self, direction):
        navKeys = self.PrimeNavKeys()
        vkey = list(navKeys)[direction]
        return self._UpdateMovement(vkey)

    def IsPlayerReady(self):
        return True

    def OnMapShortcut(self, *args):
        """
        We need to update our movement keys. There is a bunch of information coming in
        from the event which we can safely ignore at the moment.
        """
        self.PrimeNavKeys()
