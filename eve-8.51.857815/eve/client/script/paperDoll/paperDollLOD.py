#Embedded file name: eve/client/script/paperDoll\paperDollLOD.py
import blue
import trinity
import uthread
import weakref
import log
import locks
import time
from eve.common.script.paperDoll.paperDollConfiguration import PerformanceOptions
LoadingStubPath = 'res:/Graphics/Character/Global/LowLODs/Female/BasicFemale/BasicFemale.red'

class LodQueue(object):
    """
    queue lod change requests with weakrefs and all that
    """
    __guid__ = 'paperDoll.LodQueue'
    instance = None
    magicLOD = 99

    class QueueEntry:

        def __init__(self, avatarBluePythonWeakRef, dollWeakref, factoryWeakref, lodWanted):
            self.avatar = avatarBluePythonWeakRef
            self.doll = dollWeakref
            self.factory = factoryWeakref
            self.lodWanted = lodWanted
            self.timeAddToQueue = time.time()
            self.timeUpdateStarted = 0

    def __init__(self):
        self.queue = []
        self.inCallback = False
        self.updateEvent = locks.Event(name='LodQueueEvent')
        self.__freezeQueue = False
        uthread.new(LodQueue.QueueMonitorThread, weakref.ref(self))
        self.queueSizeStat = blue.statistics.Find('paperDoll/queueSize')
        if not self.queueSizeStat:
            self.queueSizeStat = blue.CcpStatisticsEntry()
            self.queueSizeStat.name = 'paperDoll/queueSize'
            self.queueSizeStat.type = 1
            self.queueSizeStat.resetPerFrame = False
            self.queueSizeStat.description = 'The length of the LOD switching queue'
            blue.statistics.Register(self.queueSizeStat)
        self.queueActiveUpStat = blue.statistics.Find('paperDoll/queueActiveUp')
        if not self.queueActiveUpStat:
            self.queueActiveUpStat = blue.CcpStatisticsEntry()
            self.queueActiveUpStat.name = 'paperDoll/queueActiveUp'
            self.queueActiveUpStat.type = 1
            self.queueActiveUpStat.resetPerFrame = False
            self.queueActiveUpStat.description = 'Number of LOD switches to higher quality in progress'
            blue.statistics.Register(self.queueActiveUpStat)
        self.queueActiveDownStat = blue.statistics.Find('paperDoll/queueActiveDown')
        if not self.queueActiveDownStat:
            self.queueActiveDownStat = blue.CcpStatisticsEntry()
            self.queueActiveDownStat.name = 'paperDoll/queueActiveDown'
            self.queueActiveDownStat.type = 1
            self.queueActiveDownStat.resetPerFrame = False
            self.queueActiveDownStat.description = 'Number of LOD switches to lower quality in progress'
            blue.statistics.Register(self.queueActiveDownStat)

    def getFreezeQueue(self):
        return self.__freezeQueue

    def setFreezeQueue(self, freeze):
        self.__freezeQueue = freeze
        LodQueue.OnDollUpdateDoneStatic()

    freezeQueue = property(getFreezeQueue, setFreezeQueue)

    def __del__(self):
        self.updateEvent.set()

    @staticmethod
    def OnDollUpdateDoneStatic():
        if LodQueue.instance is None:
            return
        LodQueue.instance.updateEvent.set()

    @staticmethod
    def QueueMonitorThread(weakSelf):
        """
        Updates the queue, then tries to process as many waiting requests as
        possible to hit the max-allowed-update-at-the-same-time limit.
        We then wait until we get a signal that the situation might have changed and
        we need to start over -- either from a "doll update done" callback, or from a
        "new stuff added to queue" call.
        """
        while weakSelf():
            weakSelf().updateEvent.wait()
            wakeUpTime = time.time()
            self = weakSelf()
            if self is None:
                break
            self.updateEvent.clear()
            busyUp, busyDown = self.UpdateQueue(wakeUpTime)
            if not self.__freezeQueue:
                maxBusyUp = PerformanceOptions.maxLodQueueActiveUp
                maxBusyDown = PerformanceOptions.maxLodQueueActiveDown
                scan = 0
                max = len(self.queue)
                while busyDown < maxBusyDown and busyUp < maxBusyUp and scan < max:
                    doll = self.queue[scan].doll()
                    if doll is not None and not doll.busyUpdating:
                        doll = self.queue[scan].doll()
                        goingUp = True
                        if doll is not None:
                            goingUp = self.queue[scan].lodWanted < doll.overrideLod
                        if self.ProcessRequest(self.queue[scan], allowUp=busyUp < maxBusyUp):
                            if goingUp:
                                busyUp = busyUp + 1
                            else:
                                busyDown = busyDown + 1
                    scan = scan + 1

            self.queueActiveUpStat.Set(busyUp)
            self.queueActiveDownStat.Set(busyDown)

    def UpdateQueue(self, wakeUpTime):
        """
        Go through the entire queue and
        1. count how many dolls are busy updating
        2. remove any entries that have a dead doll
        3. remove any entries that have a doll whose lod matches what we want, and is not updating
                (which might happen if we go back to a lod that we started with, without having had
                 a chance to load up the intermediate one).
        Returns: (busyCountUp, busyCountDown) -- a pair of how many dolls are busy going to a better resp.
        worse LOD.
        """
        i = 0
        busyUp = 0
        busyDown = 0
        while i < len(self.queue):
            doll = self.queue[i].doll()
            factory = self.queue[i].factory()
            avatar = self.queue[i].avatar.object
            if doll is None:
                self.queue.pop(i)
            elif doll.busyUpdating:
                if doll.previousLOD != LodQueue.magicLOD and doll.previousLOD <= self.queue[i].lodWanted:
                    busyDown = busyDown + 1
                else:
                    busyUp = busyUp + 1
                i = i + 1
            elif doll.overrideLod == self.queue[i].lodWanted:
                q = self.queue.pop(i)
                if PerformanceOptions.logLodPerformance:
                    log.LogInfo('LOD switch to', q.lodWanted, 'took', wakeUpTime - q.timeUpdateStarted, 'secs; wait in queue', q.timeUpdateStarted - q.timeAddToQueue, 'secs')
            else:
                i = i + 1

        self.queueSizeStat.Set(len(self.queue))
        return (busyUp, busyDown)

    def AddToQueue(self, avatarBluePythonWeakRef, dollWeakref, factoryWeakref, lodWanted):
        """
        Incoming lod-switch request.
        
        If it's already in the queue, update the requested values; if it's being updated, refresh.
        Else, add it, and if it's the only entry in the queue, kick it off right away.
        
        Avatar, doll and factory are stored as weak references, and are automatically wrapped
        into blue and python weakrefs 
        """
        if type(avatarBluePythonWeakRef) != blue.BluePythonWeakRef:
            avatarBluePythonWeakRef = blue.BluePythonWeakRef(avatarBluePythonWeakRef)
        if type(dollWeakref) != weakref.ref:
            dollWeakref = weakref.ref(dollWeakref)
        if type(factoryWeakref) != weakref.ref:
            factoryWeakref = weakref.ref(factoryWeakref)
        for i in xrange(len(self.queue)):
            q = self.queue[i]
            if q.doll() == dollWeakref() and q.factory() == factoryWeakref() and q.avatar.object == avatarBluePythonWeakRef.object:
                q.lodWanted = lodWanted
                if q.doll().busyUpdating:
                    q.doll().Update(q.factory(), q.avatar.object)
                break
        else:
            entry = self.QueueEntry(avatarBluePythonWeakRef, dollWeakref, factoryWeakref, lodWanted)
            self.queue.append(entry)

        self.updateEvent.set()

    def ProcessRequest(self, queueEntry, allowUp):
        """
        Look at the given queue entry and see if it needs any work.
        The answer is 'no' (return False) if any of the weak refs died, or if the lod we want is already
        what's there, or if we'd be exceeding some limit.
        
        Otherwise, make the calls on the doll, set up the callback, and call Update.
        """
        doll = queueEntry.doll()
        factory = queueEntry.factory()
        avatar = queueEntry.avatar.object
        if doll is None or factory is None or avatar is None:
            return False
        if queueEntry.lodWanted == doll.overrideLod:
            return False
        if queueEntry.lodWanted < doll.overrideLod and not allowUp:
            return False
        doll.overrideLod = queueEntry.lodWanted
        doll.AddUpdateDoneListener(LodQueue.OnDollUpdateDoneStatic)
        queueEntry.timeUpdateStarted = time.time()
        doll.Update(factory, avatar)
        return True


def SetupLODFromPaperdoll(avatar, doll, factory, animation, loadStub = True):
    """
    Example reference code: set up the builders to lazily piece together a paperdoll as needed.
    Arguments:
    avatar - avatar belonging to this doll; usually DOLL_MAP[doll]
    doll - doll to work with, which has been completely set up except for the visualmodel part
    factory - factory to use for the build parts, usually it's DOLL_FACTORY
    animation - the animation to use for the skeleton, usually it's GWDOLL_MAP[doll]
    Returns:
    no return value
    """
    if doll is None or avatar is None:
        return
    stub = None
    if loadStub:
        if type(avatar) == trinity.Tr2IntSkinnedObject:
            stub = blue.resMan.LoadObject(LoadingStubPath)
    if hasattr(stub, 'visualModel'):
        stub = stub.visualModel

    class InPlaceBuilder:
        """
        Helper class to hang on to a bunch of weakreferences to avatar, doll and factory, so that
        when the LOD system requests high/med/low, we can answer that request by changing the
        overridelod value on a visualmodel that's shared between all 3 lods, and Update()ing the doll.
        
        This is totally different from 3 LODs cranking out 3 completely separate visualmodels.
        The advantages over sharing are that the doll can be much smarter in how it moves the quality up/down
        (decoupling mesh and geometry updates, recycling textures until a new version is baked, etc), and it
        avoids a lot of bugs with modifiers not being LOD aware (even if we have 3 visual models, we still
        only have one doll).
        It also nicely recycles all the work that went into making doll updates fast, and asynchronous.
        
        To make this work, we need an OnSelected notification to drive the doll. If we just changed the
        lod from inside OnCreate, we'd be in trouble when LOD goes back and forth -- OnCreate would only be
        called (if a LOD doesn't time-out), and overridelod wouldn't be changed in subsequent LOD changes, 
        since trinity sees a cached object in the builder.
        
        The only disadvantage to all this is that switching LOD is now never free: there is no cached copy of
        the visualmodel as it was for a different lod.  However caching still happens on the per-mesh, per-redfile,
        per-texture level in trinity itself.  So the only cost in case of rapid switching is getting all those
        resources from resman cache, recompositing, and rebaking blendshapes.  The doll can also cache textures.
        """

        def __init__(self, avatar, doll, factory, stub):
            self.avatar = blue.BluePythonWeakRef(avatar)
            self.doll = weakref.ref(doll)
            self.factory = weakref.ref(factory)
            doll.overrideLod = LodQueue.magicLOD

            def MakeBuilder(lod):
                lodBuilder = blue.BlueObjectBuilderPython()
                lodBuilder.SetCreateMethod(lambda objectMarker, callingProxy: self.DoCreate(callingProxy, lod))
                lodBuilder.SetSelectedHandler(lambda objectMarker, callingProxy: self.OnSelected(callingProxy, lod))
                proxy = blue.BlueObjectProxy()
                proxy.builder = lodBuilder
                return proxy

            avatar.highDetailModel = MakeBuilder(0)
            avatar.mediumDetailModel = MakeBuilder(1)
            avatar.lowDetailModel = MakeBuilder(2)
            factory.AppendMeshesToVisualModel(avatar.visualModel, stub.meshes)

        def DoCreate(self, callingProxy, lod):
            if self.avatar.object is None:
                return
            return self.avatar.object.visualModel

        def OnSelected(self, callingProxy, lod):
            doll = self.doll()
            factory = self.factory()
            avatar = self.avatar.object
            if doll is None or factory is None or avatar is None:
                return
            if doll.overrideLod != lod:
                if LodQueue.instance is None:
                    doll.overrideLod = lod
                    doll.Update(factory, avatar)
                else:
                    LodQueue.instance.AddToQueue(self.avatar, self.doll, self.factory, lod)

    simpleBuilder = InPlaceBuilder(avatar, doll, factory, stub)


def AbortAllLod(avatar):
    """
    When an avatar is no longer needed, you can call this method to explicitly cancel all async LOD buildup that
    may still be in progress.  This can be more efficient than just letting go of the avatar pointer.
    """
    if avatar is None:
        return
    if avatar.highDetailModel is not None:
        avatar.highDetailModel.object = None
    if avatar.mediumDetailModel is not None:
        avatar.mediumDetailModel.object = None
    if avatar.lowDetailModel is not None:
        avatar.lowDetailModel.object = None


import carbon.common.script.util.autoexport as autoexport
exports = autoexport.AutoExports('paperDoll', globals())
