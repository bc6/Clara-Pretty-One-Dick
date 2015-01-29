#Embedded file name: carbon/common/script/net\cachedObject.py
import binascii
import zlib
import blue
import uthread
from timerstuff import ClockThis
import carbon.common.script.net.machobase as macho
import sys

class CachedObject:
    """
        The CachedObject class is a wrapper around an object that is cachable.
    
        Cachable objects may live on the proxy, sol server, and/or client machines.
    
        They may be temporary or persistant objects, and may be cached per user, globally,
        or per session.
    """
    __guid__ = 'util.CachedObject'
    __passbyvalue__ = 1
    __persistvar__ = ['__objectID__',
     '__nodeID__',
     '__objectVersion__',
     '__shared__']

    def __init__(self, shared, objectID, cachedObject, objectVersion = None):
        """
            shared is true if and only if this is an object that is generally speaking
                shared by multiple users, and thus worth keeping around in cache on
                proxies.
            objectID must be a unique, persistable, comparable identifier that
                totally uniquely identifies cachedObject.
            objectVersion is added to objectID.  Basically, objectID+objectVersion
                says "it's this object, and this particular version of it."  Only the
                most recently received version of an object is stored in cache, replacing
                any previous version.
            cachedObject is the actual object that is going to be cached.  It must be
                passable by value.
        """
        self.__shared__ = shared
        self.__objectID__ = objectID
        self.__nodeID__ = sm.GetService('machoNet').GetNodeID()
        self.__cachedObject__ = cachedObject
        self.__compressed__ = 0
        self.__thePickle__ = None
        self.__objectVersion__ = (blue.os.GetWallclockTimeNow(), objectVersion)
        if (self.__shared__ or objectVersion is None) and macho.mode != 'client':
            self.__thePickle__ = blue.marshal.Save(cachedObject)
            if len(self.__thePickle__) > 170:
                try:
                    t = ClockThis('machoNet::util.CachedObject::compress', zlib.compress, self.__thePickle__, 1)
                except zlib.error as e:
                    raise RuntimeError('Compression Failure: ' + strx(e))

                if len(t) < len(self.__thePickle__):
                    self.__thePickle__ = t
                    self.__compressed__ = 1
            if objectVersion is None:
                self.__objectVersion__ = (self.__objectVersion__[0], binascii.crc_hqx(self.__thePickle__, macho.version + 170472))

    def __getstate__(self):
        """
            Not really doing much interesting other than what is expected.  The magic
            is in setstate.
        """
        ret = [ getattr(self, attr) for attr in self.__persistvar__ ]
        if ret[-1]:
            ret = ret[:-1]
        return tuple(ret)

    def __str__(self):
        try:
            ret = []
            for each in self.__persistvar__ + ['__thePickle__', '__compressed__']:
                if each == '__thePickle__':
                    ret.append(len(each))
                else:
                    ret.append(self.__dict__[each])

            return '<CachedObject %s>' % str(ret)
        except StandardError:
            sys.exc_clear()
            return '<CachedObject ?>'

    def __repr__(self):
        return str(self)

    def __setstate__(self, state):
        """
            Does the usual sheise, but also updates our cache and causes the object to be
            fetched over the wire in the background if appropriate.
        """
        for i in xrange(len(self.__persistvar__)):
            if i >= len(state):
                if self.__persistvar__[i] == '__shared__':
                    setattr(self, self.__persistvar__[i], 1)
                else:
                    raise RuntimeError('Cached Object format version mismatch')
            else:
                setattr(self, self.__persistvar__[i], state[i])

        self.__cachedObject__ = None
        self.__thePickle__ = None
        self.__compressed__ = 0

    def __getattr__(self, key):
        """
            acquires the object in local cache, if not already here, and forwards the call
        """
        if key == '__getinitargs__':
            raise AttributeError(key, "CachedObject's cannot define __getinitargs__")
        self.__UpdateCache()
        c = self.__cachedObject__
        if c is None:
            raise ReferenceError('The specified object is no longer available in cache')
        return getattr(c, key)

    def __getitem__(self, key):
        """
            acquires the object in local cache, if not already here, and forwards the call
        """
        self.__UpdateCache()
        c = self.__cachedObject__
        if c is None:
            raise ReferenceError('The specified object is no longer available in cache')
        return c[key]

    def __UpdateCache(self):
        """
            If we haven't obtained the cached object yet: gets  it from local "objectCaching" service, via self.__objectID__
        """
        if self.__cachedObject__ is not None:
            return
        if '__semaphore__' not in self.__dict__:
            s = uthread.Semaphore(('cachedObject',
             self.__objectID__,
             self.__objectVersion__,
             self.__nodeID__))
            self.__semaphore__ = s
        with self.__semaphore__:
            if self.__cachedObject__ is None:
                self.__cachedObject__ = sm.GetService('objectCaching').GetCachableObject(self.__shared__, self.__objectID__, self.__objectVersion__, self.__nodeID__).GetObject()
        if '__semaphore__' in self.__dict__:
            if self.__semaphore__.IsCool():
                del self.__semaphore__

    def GetCachedObject(self):
        self.__UpdateCache()
        if self.__cachedObject__ is None:
            raise ReferenceError('The specified object is no longer available in cache')
        return self.__cachedObject__

    def GetObjectID(self):
        return self.__objectID__

    def MachoGetCachedObjectGuts(self):
        """
            Helper function for machoNet.  When pickling this object, machoNet acquires
            the gut's of this object, and stores them if it doesn't have the object already in cache.
        
            __shared__ objects are cached on the server/proxy forever.
        
            other objects are cached on the sol server until the client's machoNet has responded, telling
            the sol server whether or not it desires the object.
        
            All cached objects are stored on the client forever, but persisted as well.  The client may
            have some maximum disk space for cache allocated, in which case if you hit that limit some
            hopefully-intelligent means of cache maintenance will kick in.
        
            machoNet will internally perform object propagation.  Note that the cached object will end
            up on the client, even if the client doesn't call anything on it.  It is generally assumed
            that if you're passing data to the client in this fashion, the client will be using it.
        
            (Otherwise I'd have to keep these objects in RAM on the sol servers forever, which sucks)
        """
        return (self.__shared__,
         self.__objectID__,
         self.__objectVersion__,
         self.__nodeID__,
         self.__cachedObject__,
         self.__thePickle__,
         self.__compressed__)
