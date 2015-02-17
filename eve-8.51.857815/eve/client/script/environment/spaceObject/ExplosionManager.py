#Embedded file name: eve/client/script/environment/spaceObject\ExplosionManager.py
import blue
import log
import trinity
import uthread
import geo2
import math
from collections import deque
import telemetry
import evecamera.utils as camutils
import evegraphics.settings as gfxsettings
SECOND = 10000000

class Singleton(type):
    """
    Standard way of making a singleton using a metaclass. This class
    makes sure you always get the same instance when instantiating.
    """

    def __init__(cls, mcs, bases, dic):
        super(Singleton, cls).__init__(mcs, bases, dic)
        cls.instance = None

    def __call__(cls, *args, **kw):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance


class PooledExplosion:
    """
    Handles pooled copies of an explosion resource to avoid unneccessary loading and copying.
    Manages references to explosion so we know when we can trash the pool.
    """

    def __init__(self, path):
        self.path = path
        self.refCount = 0
        self.timestamp = -1
        self.timeoutCountdown = 0
        self.total = 1
        self.active = 0
        self.maxActiveTick = 0
        self.inactive = 1
        self.maxRecentUsed = deque([1], 30)
        self.totalLoads = 1
        self.pool = [trinity.Load(self.path)]
        self.effectDuration = self.pool[0].duration
        if self.effectDuration == -1:
            self.effectDuration = 10
        self.effectDuration = self.effectDuration * SECOND

    def GetDuration(self):
        return self.effectDuration

    def AddRef(self, count):
        self.refCount += count

    def DecRef(self, count):
        self.refCount -= count

    def _AddActive(self, count):
        self.active += count
        self.maxActiveTick = max(self.maxActiveTick, self.active)

    def Pop(self):
        """
        Returns an instance of the pooled resource
        """
        self._AddActive(1)
        if self.inactive > 0:
            self.inactive -= 1
            return self.pool.pop()
        self.total += 1
        self.totalLoads += 1
        return trinity.Load(self.path)

    def Push(self, explosion):
        """
        Returns the object to this pool
        """
        self.pool.append(explosion)
        self._AddActive(-1)
        self.inactive += 1

    def PrunePool(self, timestamp):
        """
        Return true if this pool has expired
        """
        if self.refCount > 0:
            self.timestamp = -1
        self.maxRecentUsed.append(self.maxActiveTick)
        self.maxActiveTick = 0
        recentMax = max(self.maxRecentUsed)
        if recentMax < self.total:
            recentMax = min(self.total - recentMax, 4)
            self.total -= recentMax
            self.inactive -= recentMax
            del self.pool[:recentMax]
        if self.refCount <= 0:
            if self.timestamp < 0:
                self.timestamp = timestamp
            if timestamp - self.timestamp > 15 * SECOND:
                return True
        return False


class ExplosionManager(object):
    """
    Basic idea: We have a list that will fill up and new explosions
    will push oldest ones out.
    We also prune the list with the age of the explosions.
    """
    __metaclass__ = Singleton

    def __init__(self, limit = 100):
        self.queue = []
        self.pooledExplosions = {}
        self.ageLimit = 20 * SECOND
        self.limit = limit
        self.running = True
        self.Start()

    def Run(self):
        while self.running:
            blue.synchro.SleepSim(1000)
            self._Prune()

    def Preload(self, path, count = 1):
        """
        Notifies the manager that we may need the explosion in the near future.
        """
        if path not in self.pooledExplosions:
            self.pooledExplosions[path] = PooledExplosion(path)
        self.pooledExplosions[path].AddRef(count)

    def Cancel(self, path, count = 1):
        """
        Let the explosion manager know we're no longer interested in this explosion.
        Should be called by objects that call Preload if they don't call GetExplosion.
        """
        if path not in self.pooledExplosions:
            log.LogWarn('ExplosionManager::Cancel ' + path + ' not loaded.')
            return
        self.pooledExplosions[path].DecRef(count)

    @telemetry.ZONE_METHOD
    def GetExplosion(self, path, scale = 1.0, preloaded = False, callback = None):
        """
        Returns an explosion loaded from path
        """
        if path not in self.pooledExplosions:
            if preloaded:
                log.LogWarn('ExplosionManager::GetExplosion ' + path + ' not loaded.')
            self.Preload(path)
        elif not preloaded:
            self.pooledExplosions[path].AddRef(1)
        explosion = self.pooledExplosions[path].Pop()
        explosion.scaling = (scale, scale, scale)
        explosion.Start()
        self._Append(callback, explosion, self.pooledExplosions[path])
        return explosion

    def GetBoundingSphereRadius(self, path):
        """
        Returns the attribute value for a preloaded explosion
        """
        if path not in self.pooledExplosions:
            log.LogWarn('ExplosionManager::GetBoundingSphereRadius ' + path + ' not loaded.')
            self.Preload(path)
        return getattr(self.pooledExplosions[path].resource, 'boundingSphereRadius', -1)

    def _Append(self, callback, model, pool):
        """
        Created a timestamp and adds an item to the end of the queue.
        The delay is in blue time.
        """
        delay = pool.GetDuration()
        if delay > self.ageLimit:
            delay = self.ageLimit
        stamp = blue.os.GetSimTime() + delay
        self.queue.append((stamp,
         callback,
         model,
         pool))
        if len(self.queue) > self.limit:
            self._Delete(self.queue.pop(0))

    def _Prune(self):
        """
        Sorts the list and then goes throught it and deletes the oldest items.
        The sorting guarantees that the oldest are at the start of the queue.
        """
        if not len(self.queue) and not len(self.pooledExplosions):
            return
        now = blue.os.GetSimTime()
        if len(self.queue):
            self.queue.sort()
            while True:
                blue.synchro.Yield()
                now = blue.os.GetSimTime()
                if not len(self.queue) or not self.running:
                    break
                if self.queue[0][0] < now:
                    self._Delete(self.queue.pop(0))
                else:
                    break

        delKeys = []
        for val in self.pooledExplosions.itervalues():
            if val.PrunePool(now):
                delKeys.append(val.path)

        for key in delKeys:
            del self.pooledExplosions[key]

    def _Delete(self, item):
        """
        Calls the CleanupExplosion callback of the item. Returns the model back to it's queue.
        """
        if item is not None:
            stamp, callback, model, pool = item
            if model is None:
                log.LogError('ExplosionManager::_Delete item has no model')
            if pool is None:
                log.LogError('ExplosionManager::_Delete item has no pool')
            if callback is not None:
                callback(model)
            model.Stop()
            model.loadedCallback = None
            pool.Push(model)
            pool.DecRef(1)

    def GetCount(self):
        return len(self.queue)

    def SetLimit(self, limit):
        self.limit = limit

    def Inspect(self):
        print self.queue

    def Start(self):
        self.running = True
        uthread.new(self.Run)

    def Stop(self):
        self.running = False


def GetLodLevel(position, radius):
    cam = sm.GetService('sceneManager').GetRegisteredCamera('default')
    if cam is None:
        return 1
    distance = geo2.Vec3Length(geo2.Vec3Subtract((cam.pos.x, cam.pos.y, cam.pos.z), position))
    vp = trinity.device.viewport
    aspectRatio = vp.GetAspectRatio()
    fov = cam.fieldOfView / camutils.GetARZoomMultiplier(aspectRatio)
    lodQuality = gfxsettings.Get(gfxsettings.GFX_LOD_QUALITY)
    boundingSize = radius / (math.tan(fov / 2) * distance) * vp.height
    if boundingSize < 192 / lodQuality:
        return 1
    return 0


exports = {'util.ExplosionManager': ExplosionManager,
 'util.GetLodLevel': GetLodLevel}
