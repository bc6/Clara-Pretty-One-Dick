#Embedded file name: eve/devtools/script\svc_gridload.py
import blue, uthread
import log
import service
from service import Service

class GridLoadSimulationTool(service.Service):
    """ 
    Inherit from service.Service, and do some boilerplate setup. 
    """
    __guid__ = 'svc.GridLoadSimulationTool'
    __servicename__ = 'GridLoadSimulationTool'
    __displayname__ = 'Grid Load Simulation Tool'
    __exportedcalls__ = {}

    def __init__(self):
        """
        Calls the base class constructor
        """
        service.Service.__init__(self)

    def Run(self, memStream = None):
        """
        State constant assignment and base class Run() call
        """
        self.state = service.SERVICE_START_PENDING
        Service.Run(self, memStream)
        self.numInQueue = 0
        self.pcQueue = uthread.Queue(0)
        self.semaphore = uthread.Semaphore('spawnTestSema', 1, True)
        self.go = False
        self.hasStarted = False
        self.state = service.SERVICE_RUNNING

    def Stop(self, memStream = None):
        """
        State constant for service shutdown and base class Stop() call
        """
        self.state = service.SERVICE_STOP_PENDING
        Service.Stop(self, memStream)
        self.state = service.SERVICE_STOPPED

    def StartTest(self, initNumObjsToSpawn, spawnCountPerTick, unspawnCountPerTick, spawnTickIntervalInMS, unspawnTickIntervalInMS, spawningCharID = 0):
        """
        This function starts a simulation run.
        
        Sets several instance variables to keep track of state, including a semaphore and 
        a producer-consumer queue. It then spawns a producer and a consumer thread to do
        the spawning and despawning work separately. 
         
        Params:
            initNumObjsToSpawn ........ The number of objects to initially spawn
            spawnCountPerTick .......... The number of objects to spawn at each addition tick
            unspawnCountPerTick ........ The number to unspawn at each removal tick
        
            spawnTickIntervalInMS ..... The rate at which to add objects in milleseconds
            unspawnTickIntervalInMS ... The rate at which to remove objects in milleseconds
            spawningCharID ............ Owning character ID of the spawned object
        """
        self.numInQueue = 0
        self.go = True
        self.hasStarted = False
        self.prodThread = uthread.new(self.spawnRunner, spawningCharID, initNumObjsToSpawn, spawnCountPerTick, unspawnCountPerTick, spawnTickIntervalInMS)
        self.consumeThread = uthread.new(self.unspawnRunner, unspawnCountPerTick, unspawnTickIntervalInMS)

    def StopTest(self):
        """
        Stops simulating load.   All spawned objects will be removed.
        
        It does this by spawning a stopping thread to go corral
        self.consumeThread and self.prodThread
        """
        uthread.new(self.StopRunner)

    def spawnRunner(self, spawningCharID, initNumObjs, spawnCountPerTick, unspawnCountPerTick, tickIntervalInMS):
        """
        Function run by the actual spawning thread. First spawns the initial number of 
        objects specified, then begins spawning on its specified interval. Once it spawns 
        objects, it puts lists of their ItemIDs onto self.pcQueue. The size of these lists 
        is dependent upon unspawnCountPerTick, so that the unspawnRunner can eat cleanly off 
        of the queue. If the number of items spawned  is greater than unspawnCountPerTick we 
        leave the (spawnCountPerTick % unspawnCountPerTick) extras in the scope of this thread 
        to be added to self.pcQueue after the next wake. Sleeps for the specified duration 
        after a spawning loop. Mutually excludes on self.semaphore while spawning.
        
        If self.go is set to False by the stopping thread, then this thread unspawns any 
        ItemIDs left in its local scope, then returns
        
        params:
            self ...................... An instance method.
            spawningCharID ............ Owning char of all spawned objects.
            initNumObjs ............... Initial number of objects to spawn before beginning 
                                        the intervals
            spawnCountPerTick .......... Number of items to spawn at each interval, above caveats
            unspawnCountPerTick ........ Number of items to unspawn at each interval, passed
                                        into the spawning thread so that we put cleanly 
                                        despawnable lists onto self.pcQueue for unspawnRunner to get.
            tickIntervalInMS .......... Duration that this thread sleeps between spawning runs.
        """
        typeIDtoSpawn = 638
        baseName = 'spawnLoadTestObj_'
        itemIDList = []
        stdDev = 0.0
        self.semaphore.acquire()
        for i in xrange(initNumObjs):
            cmdStr = '/spawn %s stddev=%s name="%s%s" ' % (typeIDtoSpawn,
             stdDev,
             baseName,
             i)
            id = sm.GetService('slash').SlashCmd(cmdStr)
            itemIDList.append(id)
            if len(itemIDList) == unspawnCountPerTick:
                self.pcQueue.non_blocking_put(itemIDList)
                self.numInQueue = self.numInQueue + unspawnCountPerTick
                itemIDList = []

        self.hasStarted = True
        self.semaphore.release()
        log.LogInfo('Finished setting up the, feel free to call StopTest().')
        while True:
            blue.pyos.synchro.SleepWallclock(tickIntervalInMS)
            if not self.go:
                for id in itemIDList:
                    cmdStr = '/unspawn %s' % id
                    sm.GetService('slash').SlashCmd(cmdStr)

                return
            self.semaphore.acquire()
            for i in xrange(spawnCountPerTick):
                cmdStr = '/spawn %s stddev=%s name="%s%s" ' % (typeIDtoSpawn,
                 stdDev,
                 baseName,
                 i)
                id = sm.GetService('slash').SlashCmd(cmdStr)
                itemIDList.append(id)
                if len(itemIDList) == unspawnCountPerTick:
                    self.pcQueue.non_blocking_put(itemIDList)
                    self.numInQueue = self.numInQueue + unspawnCountPerTick
                    itemIDList = []

            self.semaphore.release()

    def unspawnRunner(self, unspawnCountPerTick, tickIntervalInMS):
        """
        Function run by the unspawnspawnCountPerTick thread. Eats off of self.pcQueue, despawning the 
        lists of ItemIDs that it finds there. Mutually excludes on self.semaphore while despawning.
        
        If self.go is set to False by the stopping thread, then this thread unspawns any 
        ItemIDs left in self.pcQueue
        
        Params:
            self ...................... An instance method.
            unspawnCountPerTick ........ Number of items to unspawn at each interval, also the 
                                        size of the list that this thread eats off of self.pcQueue
            tickIntervalInMS .......... Duration that this thread sleeps after despawning 
                                        its allotted number of objects
        """
        while True:
            blue.pyos.synchro.SleepWallclock(tickIntervalInMS)
            if not self.hasStarted:
                continue
            if not self.go:
                while True:
                    cleanUpList = self.pcQueue.get()
                    self.semaphore.acquire()
                    for id in cleanUpList:
                        cmdStr = '/unspawn %s' % id
                        sm.GetService('slash').SlashCmd(cmdStr)

                    self.numInQueue = self.numInQueue - len(cleanUpList)
                    self.semaphore.release()

            else:
                listToDespawn = self.pcQueue.get()
                self.semaphore.acquire()
                for id in listToDespawn:
                    cmdStr = '/unspawn %s' % id
                    sm.GetService('slash').SlashCmd(cmdStr)

                self.numInQueue = self.numInQueue - len(listToDespawn)
                self.semaphore.release()

    def StopRunner(self):
        """
        Stopping threaded function called by StopTest. Sets the self.go state variable to 
        signal the other two threads to die. SpawnRunner (self.prodThread) takes care of 
        itself, but unspawnRunner (self.consumeThread) can block for various reasons, but 
        especially when it's done its cleanup work, and the self.pcQueue() is empty. This 
        thread waits on self.consumeThread to finish before it kills it.
        """
        while True:
            self.semaphore.acquire()
            if not self.hasStarted:
                self.semaphore.release()
                blue.pyos.synchro.SleepWallclock(1000)
                continue
            self.go = False
            self.semaphore.release()
            blue.pyos.synchro.SleepWallclock(1000)
            if self.consumeThread.alive:
                if self.consumeThread.blocked:
                    self.semaphore.acquire()
                    if self.numInQueue == 0:
                        self.semaphore.release()
                        self.consumeThread.kill()
                        return
                    self.semaphore.release()
                    blue.pyos.synchro.SleepWallclock(1000)
            else:
                return
