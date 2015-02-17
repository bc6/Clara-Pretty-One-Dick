#Embedded file name: carbon/common/script/net\moniker.py
"""
The usual moniker stuff
"""
import weakref
import cPickle
import uthread
import base
import sys
from carbon.common.script.sys.service import ROLE_SERVICE
import macho
import log
allMonikers = weakref.WeakKeyDictionary({})

class Moniker():
    """
    Represents a proxy to a remote object. All calls to the proxy are forwarded to the actual remote object. 
    The node to which the calls are forwarded to are determined by the service name and the value of the bindParams parameter.
    The value of the bindParams is passed to the MachoResolveObject function on the service specified, which returns the nodeID the acutal remote belongs to.
    """
    __guid__ = 'util.Moniker'
    __passbyvalue__ = 1
    __persistvar__ = ['__serviceName',
     '__nodeID',
     '__bindParams',
     '__sessionCheck']

    def __init__(self, serviceName = None, bindParams = None, nodeID = None, quicky = 0):
        """
        Creates a new moniker to a remove object
        """
        global allMonikers
        self.__serviceName = serviceName
        self.__bindParams = bindParams
        self.__nodeID = nodeID
        self.__quicky = quicky
        self.__sessionCheck = None
        self.boundObject = None
        allMonikers[self] = 1

    def __del__(self):
        self.__ClearBoundObject()

    def __str__(self):
        if self.__class__ == Moniker:
            name = 'Generic'
        else:
            name = self.__class__.__name__
        args = (name,
         self.__serviceName,
         self.__nodeID,
         self.__bindParams)
        return '%s moniker on service %s, node %s, params %s' % args

    def SetSessionCheck(self, sessionCheck):
        """
        Sets the session check dictionary, which is a dictionaery of name:value pairs which have to be valid for the lifetime of this moniker
        """
        self.__sessionCheck = sessionCheck

    def __PerformSessionCheck(self):
        """
        If the session check dictionary has been set, checks whether the values in there match the current session values. 
        If any value does not match a RunTimeError is thrown
        """
        if self.__sessionCheck:
            for attribute, expected in self.__sessionCheck.iteritems():
                if session:
                    current = getattr(session, attribute, None)
                else:
                    current = None
                if current != expected or not expected and current:
                    log.LogTraceback('__PerformSessionCheck:  Monikers session has changed. Traceback=', toAlertSvc=0, severity=log.LGWARN)
                    raise RuntimeError('MonikerSessionCheckFailure', {'attribute': attribute,
                     'expected': expected,
                     'current': current,
                     'serviceName': self.__serviceName,
                     'bindParams': self.__bindParams})

    def ToURLString(self):
        import binascii
        return binascii.b2a_hex(cPickle.dumps((self.__serviceName, self.__bindParams), 1))

    def FromURLString(self, s):
        import binascii
        b = binascii.a2b_hex(s)
        self.__serviceName, self.__bindParams = cPickle.loads(b)

    def __getstate__(self):
        ret = []
        for each in self.__persistvar__:
            ret.append(self.__dict__['_Moniker' + each])

        return tuple(ret)

    def __setstate__(self, state):
        for i in xrange(len(self.__persistvar__)):
            self.__dict__['_Moniker' + self.__persistvar__[i]] = state[i]

        if self.__nodeID is not None:
            sm.services['machoNet'].SetNodeOfAddress(self.__serviceName, self.__bindParams, self.__nodeID)
        self.boundObject = None
        self.__quicky = 2
        allMonikers[self] = 1

    __remobsuppmeth__ = ('RegisterObjectChangeHandler', 'UnRegisterObjectChangeHandler')

    def __getattr__(self, key):
        if key in self.__remobsuppmeth__:
            self.Bind()
            return getattr(self.boundObject, key)
        elif not key[0].isupper():
            if key.startswith('__'):
                raise AttributeError(key)
            self.Bind()
            return getattr(self.boundObject, key)
        else:
            return MonikerCallWrap(self, key)

    def __ClearBoundObject(self, disconnectDelay = 30):
        if self.boundObject is not None and isinstance(self.boundObject, base.ObjectConnection):
            try:
                self.boundObject.DisconnectObject(disconnectDelay)
            except AttributeError:
                pass

        self.boundObject = None

    def Bind(self, sess = None, call = None):
        """
            Binds the moniker, performing the first call as well if the params are specified,
            using the given session.  If no session is specified, a service session is used.
        """
        localKeywords = ('machoTimeout', 'noCallThrottling')
        done = {}
        while 1:
            try:
                if self.__bindParams is None:
                    raise RuntimeError("Thou shall not use None as a Moniker's __bindParams")
                if '__semaphoreB__' not in self.__dict__:
                    self.__semaphoreB__ = uthread.Semaphore(('moniker::Bind', self.__serviceName, self.__bindParams))
                self.__semaphoreB__.acquire()
                try:
                    if not self.boundObject:
                        if self.__nodeID is None:
                            self.__ResolveImpl(0, sess)
                        if sess is None:
                            if session and base.IsInClientContext():
                                sess = session
                            elif session and session.role == ROLE_SERVICE:
                                sess = session.GetActualSession()
                            else:
                                sess = base.GetServiceSession('util.Moniker')
                        else:
                            sess = sess.GetActualSession()
                        if self.__nodeID == sm.GetService('machoNet').GetNodeID():
                            service = sess.ConnectToService(self.__serviceName)
                            self.boundObject = service.MachoGetObjectBoundToSession(self.__bindParams, sess)
                        else:
                            remotesvc = sess.ConnectToRemoteService(self.__serviceName, self.__nodeID)
                            self.__PerformSessionCheck()
                            if call is not None and call[2]:
                                c2 = {k:v for k, v in call[2].iteritems() if k not in localKeywords}
                                call = (call[0], call[1], c2)
                            self.boundObject, retval = remotesvc.MachoBindObject(self.__bindParams, call)
                            self.boundObject.persistantObjectID = (self.__serviceName, self.__bindParams)
                            return retval
                finally:
                    done[self.__serviceName, self.__bindParams] = 1
                    self.__semaphoreB__.release()

                if call is not None:
                    return self.MonikeredCall(call, sess)
                return
            except UpdateMoniker as e:
                if (e.serviceName, e.bindParams) in done:
                    log.LogException()
                    raise RuntimeError('UpdateMoniker referred us to the same location twice', (e.serviceName, e.bindParams))
                else:
                    self.__bindParams = e.bindParams
                    self.__serviceName = e.serviceName
                    self.__nodeID = e.nodeID
                    self.Unbind()
                    sys.exc_clear()

    def MonikeredCall(self, call, sess):
        """
            INTERNAL:
        
            Performs a call using the given call params and session, binding and resolving
            and reacting to update moniker and reference error as appropriate.
        """
        retry = 0
        while 1:
            try:
                self.__PerformSessionCheck()
                if self.boundObject is None:
                    return self.Bind(sess, call)
                try:
                    return apply(getattr(self.boundObject, call[0]), call[1], call[2])
                except UpdateMoniker as e:
                    self.__bindParams = e.bindParams
                    self.__serviceName = e.serviceName
                    self.__nodeID = e.nodeID
                    self.Unbind()
                    sys.exc_clear()

            except UserError as e:
                if e.msg == 'UnMachoDestination' and not retry:
                    retry = 1
                    self.Unresolve()
                    sys.exc_clear()
                    continue
                raise
            except UnMachoDestination:
                if not retry:
                    retry = 1
                    self.Unresolve()
                    sys.exc_clear()
                    continue
                raise

    def IsRunning(self):
        """
            A hax helper, that tells the caller whether or not the moniker in question
            is running, in some bizzarre manner.
        """
        return self.__ResolveImpl(1)

    def QuickResolve(self):
        """
            Resolves the dude, if possible, by using only info available in RAM.  Used
            before sending over the wire.
        """
        if self.__nodeID is None and self.__serviceName in sm.services:
            self.__nodeID = self.__ResolveImpl(self.__quicky)

    def Resolve(self, sess = None):
        """
            resolves the object.  Happy happy.  Afterwards, self.__nodeID is valid.
        """
        return self.__ResolveImpl(0, sess)

    def __ResolveImpl(self, justQuery, sess = None):
        """
        Determines and remembers and/or returns the ID of the node hosting the object to which self is bound.
        """
        if '__semaphoreR__' not in self.__dict__:
            self.__semaphoreR__ = uthread.Semaphore(('moniker::Resolve', self.__serviceName, self.__bindParams))
        self.__semaphoreR__.acquire()
        try:
            if self.__nodeID is not None:
                return self.__nodeID
            if macho.mode == 'client' or base.IsInClientContext():
                self.__nodeID = sm.services['machoNet'].GuessNodeIDFromAddress(self.__serviceName, self.__bindParams)
                if self.__nodeID is not None:
                    return self.__nodeID
                if not self.__nodeID:
                    self.__nodeID = sm.services['machoNet']._addressCache.Get(self.__serviceName, self.__bindParams)
                    if self.__nodeID is not None:
                        return self.__nodeID
            if sess is None:
                if session and session.role == ROLE_SERVICE:
                    sess = session.GetActualSession()
                else:
                    sess = base.GetServiceSession('util.Moniker')
            else:
                sess = sess.GetActualSession()
            if justQuery == 2:
                service = sm.services.get(self.__serviceName, None)
                if service is None:
                    return
            else:
                service = sess.ConnectToAnyService(self.__serviceName)
            self.__nodeID = service.MachoResolveObject(self.__bindParams, justQuery)
            if self.__nodeID is None and not justQuery:
                raise RuntimeError('Resolution failure:  ResolveObject returned None')
            if macho.mode == 'client' or base.IsInClientContext():
                sm.services['machoNet'].SetNodeOfAddress(self.__serviceName, self.__bindParams, self.__nodeID)
            return self.__nodeID
        finally:
            self.__semaphoreR__.release()

    def Unresolve(self):
        while 1:
            self.Unbind()
            if '__semaphoreR__' not in self.__dict__:
                self.__semaphoreR__ = uthread.Semaphore(('moniker::Resolve', self.__serviceName, self.__bindParams))
            self.__semaphoreR__.acquire()
            try:
                if self.boundObject is None:
                    self.__nodeID = None
                    sm.services['machoNet'].SetNodeOfAddress(self.__serviceName, self.__bindParams, None)
                    return
            finally:
                self.__semaphoreR__.release()

    def Unbind(self, disconnectDelay = 30):
        """
            R.I.P.
        
            Bound Object
        
            Died of natural causes
        
            Params:
                disconnectDelay - time until the session actually detaches from the boundObject.
        """
        if '__semaphoreB__' not in self.__dict__:
            self.__semaphoreB__ = uthread.Semaphore(('moniker::Bind', self.__serviceName, self.__bindParams))
        self.__semaphoreB__.acquire()
        try:
            self.__ClearBoundObject(disconnectDelay)
        finally:
            self.__semaphoreB__.release()

    def GetNodeID(self):
        """
            returns the nodeID that this moniker runs on.  Generally speaking, this is used for evil haxs
        """
        if self.__nodeID is None:
            self.__ResolveImpl(0)
        return self.__nodeID

    def GetSelfLocal(self):
        if self.GetNodeID() == sm.services['machoNet'].GetNodeID():
            self.Bind()
            return self.boundObject.__object__
        raise RuntimeError('You are not local %d != %d' % (self.GetNodeID(), sm.services['machoNet'].GetNodeID()))


class MonikerCallWrap():

    def __init__(self, moniker, key):
        self.moniker = moniker
        self.key = key
        if key[0] != key[0].upper():
            raise RuntimeError("This moniker has no attribute '%s'. Moniker: %s" % (key, moniker))

    def __call__(self, *args, **kw):
        try:
            return self.moniker.MonikeredCall((self.key, args, kw), None)
        finally:
            self.__dict__.clear()


class UpdateMoniker(StandardError):
    __guid__ = 'util.UpdateMoniker'
    __passbyvalue__ = 1

    def __init__(self, serviceName = None, bindParams = None, nodeID = None):
        Exception.__init__(self, 'Update')
        self.serviceName = serviceName
        self.nodeID = nodeID
        self.bindParams = bindParams


def GetWorldSpace(worldSpaceID):
    moniker = Moniker('worldSpaceServer', worldSpaceID)
    return moniker


exports = {'util.allMonikers': allMonikers,
 'moniker.GetWorldSpace': GetWorldSpace}
