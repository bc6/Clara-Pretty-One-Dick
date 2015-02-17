#Embedded file name: eve/client/script/ui/services\reprocessingsvc.py
import service
import util
import moniker
import carbon.client.script.util.lg as lg
import uthread
import sys
import carbonui.const as uiconst
import form
import localization
import inventorycommon.const as invconst

class ReprocessingSvc(service.Service):
    __exportedcalls__ = {'ReprocessDlg': [],
     'GetReprocessingSvc': [],
     'GetOptionsForItemTypes': []}
    __guid__ = 'svc.reprocessing'
    __notifyevents__ = ['ProcessSessionChange', 'DoSessionChanging']
    __servicename__ = 'reprocessing'
    __displayname__ = 'Reprocessing Service'
    __dependencies__ = ['settings']

    def __init__(self):
        service.Service.__init__(self)
        self.optionsByItemType = {}
        self.crits = {}
        self.oreEfficiency = None
        self.efficiency = None

    def LogInfo(self, *args):
        lg.Info(self.__guid__, *args)

    def Run(self, memStream = None):
        self.LogInfo('Starting Reprocessing Service')
        self.ReleaseReprocessingSvc()

    def Stop(self, memStream = None):
        self.ReleaseReprocessingSvc()

    def __EnterCriticalSection(self, k, v = None):
        if (k, v) not in self.crits:
            self.crits[k, v] = uthread.CriticalSection((k, v))
        self.crits[k, v].acquire()

    def __LeaveCriticalSection(self, k, v = None):
        self.crits[k, v].release()
        if (k, v) in self.crits and self.crits[k, v].IsCool():
            del self.crits[k, v]

    def ProcessSessionChange(self, isremote, session, change):
        if 'charid' in change or 'stationid2' in change:
            self.ReleaseReprocessingSvc()

    def DoSessionChanging(self, isRemote, session, change):
        if 'charid' in change or 'stationid2' in change:
            sm.StopService(self.__guid__[4:])

    def GetReprocessingSvc(self):
        if hasattr(self, 'moniker') and self.moniker is not None:
            return self.moniker
        self.moniker = moniker.GetReprocessingManager()
        return self.moniker

    def ReleaseReprocessingSvc(self):
        if hasattr(self, 'moniker') and self.moniker is not None:
            self.moniker = None

    def ReprocessDlg(self, items = None):
        uthread.new(self.uthread_ReprocessDlg, items)

    def uthread_ReprocessDlg(self, items):
        self.__EnterCriticalSection('reprocessingDlg')
        try:
            uicore.cmd.OpenReprocessingPlant(items)
        finally:
            self.__LeaveCriticalSection('reprocessingDlg')

    def GetOptionsForItemTypes(self, itemtypes):
        typesToGet = {}
        for typeID in itemtypes.iterkeys():
            if not self.optionsByItemType.has_key(typeID):
                typesToGet[typeID] = 0

        if len(typesToGet):
            types = util.GetReprocessingOptions(typesToGet)
            for typeID in types.iterkeys():
                option = types[typeID]
                self.optionsByItemType[typeID] = option

        out = {}
        for typeID in itemtypes.iterkeys():
            if self.optionsByItemType.has_key(typeID):
                out[typeID] = self.optionsByItemType[typeID]

        return out
