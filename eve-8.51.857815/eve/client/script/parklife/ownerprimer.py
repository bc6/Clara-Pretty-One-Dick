#Embedded file name: eve/client/script/parklife\ownerprimer.py
import service
import uthread

class OwnerPrimer(service.Service):
    """
    Prime the owners on DoBallsAdded so we don't have to do it
    all over the place. Make sure all primings are protected by a
    semaphore so we don't send further prime requests for the
    
    Don't prime individual additions, since there is no gain in it.
    """
    __guid__ = 'svc.ownerprimer'
    __notifyevents__ = ['DoBallsAdded']

    def Run(self, *etc):
        service.Service.Run(self, *etc)
        sm.FavourMe(self.DoBallsAdded)
        self.waitingowners = {}

    def DoBallsAdded(self, *args, **kw):
        import stackless
        import blue
        t = stackless.getcurrent()
        timer = t.PushTimer(blue.pyos.taskletTimer.GetCurrent() + '::ownerprimer')
        try:
            return self.DoBallsAdded_(*args, **kw)
        finally:
            t.PopTimer(timer)

    def DoBallsAdded_(self, entries):
        if len(entries) < 2:
            return
        uthread.new(self.DoBallsAdded_thread, entries).context = 'ownerprimer::DoBallsAdded'

    def DoBallsAdded_thread(self, entries):
        tmp = {}
        for ball, slimItem in entries:
            if slimItem is not None and slimItem.ownerID is not None:
                tmp[slimItem.ownerID] = None

        cfg.eveowners.Prime(tmp.keys())
