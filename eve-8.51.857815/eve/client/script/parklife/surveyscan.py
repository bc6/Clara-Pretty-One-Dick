#Embedded file name: eve/client/script/parklife\surveyscan.py
import service
import form
import sys
import uthread
import blue
import telemetry

class SurveyScanSvc(service.Service):
    """
    Keep and show the results of survey scans.
    """
    __guid__ = 'svc.surveyScan'
    __exportedcalls__ = {'Clear': []}
    __notifyevents__ = ['OnSurveyScanComplete', 'DoBallRemove', 'DoBallsRemove']

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        self.scans = {}
        self.isSettingEntries = False

    @telemetry.ZONE_METHOD
    def DoBallsRemove(self, pythonBalls, isRelease):
        for ball, slimItem, terminal in pythonBalls:
            self.DoBallRemove(ball, slimItem, terminal)

    def DoBallRemove(self, ball, slimItem, terminal):
        if ball.id in self.scans:
            del self.scans[ball.id]
            if not self.isSettingEntries:
                self.isSettingEntries = True
                uthread.pool('SurveyScanSvc::SetEntriesDelayed', self.SetEntriesDelayed)

    def SetEntriesDelayed(self):
        """
            wait for 2 seconds before actually doing it to give others 
            a time to get their DoBallRemove()'s in the same call
        """
        blue.pyos.synchro.SleepSim(2000)
        wnd = form.SurveyScanView.GetIfOpen()
        if wnd:
            wnd.SetEntries(self.scans)
        self.isSettingEntries = False

    def OnSurveyScanComplete(self, l):
        try:
            for ballID, typeID, quantity in l:
                self.scans[ballID] = (typeID, quantity)

            wnd = form.SurveyScanView.Open()
            if wnd:
                wnd.SetEntries(self.scans)
        except:
            import traceback
            traceback.print_exc()
            sys.exc_clear()

    def GetWnd(self, create = 0):
        if create:
            return form.SurveyScanView.Open()
        return form.SurveyScanView.GetIfOpen()

    def Clear(self):
        self.scans = {}
        form.SurveyScanView.CloseIfOpen()
