#Embedded file name: eve/client/script/ui/services\voucherCache.py
import service
import blue
from carbon.common.script.sys.service import SERVICE_RUNNING
from eveexceptions.exceptionEater import ExceptionEater
import uthread
import localization

class VoucherCache(service.Service):
    __exportedcalls__ = {'GetVoucher': [],
     'OnAdd': []}
    __guid__ = 'svc.voucherCache'
    __notifyevents__ = ['ProcessSessionChange']
    __servicename__ = 'voucherCache'
    __displayname__ = 'Voucher Cache Service'

    def __init__(self):
        service.Service.__init__(self)
        self.data = {}
        self.names = {}

    def Run(self, memStream = None):
        self.LogInfo('Starting Voucher Cache Service')
        self.data = {}
        self.names = {}
        self.ReleaseVoucherSvc()
        self.nameQueue = uthread.Channel('voucherCache._NameFetcher')
        uthread.new(self._NameFetcher, self.nameQueue)

    def Stop(self, memStream = None):
        self.ReleaseVoucherSvc()

    def ProcessSessionChange(self, isremote, session, change):
        if 'charid' in change:
            self.ReleaseVoucherSvc()

    def GetVoucherSvc(self):
        if hasattr(self, 'moniker') and self.moniker is not None:
            return self.moniker
        self.moniker = sm.RemoteSvc('voucher')
        return self.moniker

    def ReleaseVoucherSvc(self):
        if hasattr(self, 'moniker') and self.moniker is not None:
            self.moniker = None
            self.data = {}
            self.names = {}

    def GetVoucher(self, voucherID):
        while eve.session.mutating:
            self.LogInfo('GetVoucher - hang on session is mutating')
            blue.pyos.synchro.SleepWallclock(1)

        if not self.data.has_key(voucherID):
            voucher = self.GetVoucherSvc().GetObject(voucherID)
            if voucher is None:
                return
            self.data[voucherID] = voucher
            try:
                name, _desc = sm.GetService('addressbook').UnzipMemo(voucher.GetDescription())
                self.names[voucherID] = name
            except:
                self.LogWarn('Was trying to get a name from a voucher but I failed', voucherID)

        return self.data[voucherID]

    def OnAdd(self, vouchers):
        for voucher in vouchers:
            self.data[voucher.itemID] = voucher
            self.names[voucher.itemID] = voucher.text

    def PrimeVoucherNames(self, voucherIDs):
        uthread.Lock(self, 'PrimeVoucherNames')
        try:
            unprimed = []
            for voucherID in voucherIDs:
                if voucherID not in self.names:
                    unprimed.append(voucherID)

            if unprimed:
                vouchers = self.GetVoucherSvc().GetNames(unprimed)
                for voucher in vouchers:
                    unprimed.remove(voucher.voucherID)
                    self.names[voucher.voucherID] = voucher.text

                for voucherID in unprimed:
                    self.names[voucherID] = localization.GetByLabel('UI/Common/Bookmark')

        finally:
            uthread.UnLock(self, 'PrimeVoucherNames')

    def GetVoucherName(self, voucherID):
        """
        Get a voucher name, first looking in local cache and then if not found will call the server.
        Uses _NameFetcher so that multiple name requests can be batched up in a single server call
        rather than having multiple calls for one name at a time.
        """
        if voucherID in self.names:
            return self.names[voucherID]
        responseChannel = uthread.Channel(('GetVoucherNameWithWait', voucherID))
        self.nameQueue.send((voucherID, responseChannel))
        return responseChannel.receive()

    def _NameFetcher(self, nameQueue):
        """
        Waits for incoming name requests, then fetches them from the server in a single call.
        Results are returned by sending back to the requester's channel.
        """
        while self.state == SERVICE_RUNNING:
            with ExceptionEater('voucherCache._NameFetcher'):
                requests = {}
                voucherID, responseChannel = nameQueue.receive()
                requests[voucherID] = responseChannel
                while nameQueue.balance:
                    voucherID, responseChannel = nameQueue.receive()
                    requests[voucherID] = responseChannel

                self.PrimeVoucherNames(requests.keys())
                for voucherID, responseChannel in requests.iteritems():
                    responseChannel.send(self.names[voucherID])
