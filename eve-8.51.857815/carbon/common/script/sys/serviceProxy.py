#Embedded file name: carbon/common/script/sys\serviceProxy.py
import zlib
import types
import inspect
import random
import uthread

class ServiceProxy(object):
    """
    A wrapper class for accessing a remote service via a local proxy. This is
    a formalization of the proxy pattern similar to that used by the market.
    
    To use a service proxy there are a couple of requirements:
    
     - Every exported call accesible via the proxy MUST have a method parameter
       which defines the distribution over the cluster. You can still have methods
       which don't but the proxy will not be able to call them, you call them as 
       normal services.
    
     - The service MAY define a __serviceproxyresolve__ class variable which defines
       the default method argument name used when determining the nodeID to call.
    
     - The service may also define a per method override using the "resolve"
       keyword in the __exportedcalls__ dictionary.
    
    The format of the resolve parameter is:
    
        (serviceMask, methodArgumentName)
    
    examples:
    
        # You can specify a default resolve for all exported methods
        __serviceproxyresolve__ = (const.cluster.SERVICE_DISTRICT, "districtID")
    
        # You can override the default and define a different resolve per method
        __exportedcalls__ =  {
            "AttackDistrict" : { "resolve":(const.cluster.SERVICE_DISTRICT, "districtID") },
        }
    
    The second resolve parameter may also be given one of the following valid constants:
    
        const.cluster.NODE_ANY
        const.cluster.NODE_ANY_PROXY
        const.cluster.NODE_ANY_SERVER
        const.cluster.NODE_ALL
        const.cluster.NODE_ALL_PROXY
        const.cluster.NODE_ALL_SERVER
    
    You can then use a service proxy by:
    
        service.ServiceProxy("districtManager", session).AttackDistrict(districtID, ...)
    
    or if you prefer via the session helper:
    
        session.ServiceProxy("districtManager").AttackDistrict(districtID, ...)
    """
    __guid__ = 'service.ServiceProxy'
    _methods = {}

    def __init__(self, serviceName, session):
        """
        ServiceProxy accepts a machonet session and the name of a service to proxy. The
        matching service should have at least one method exported with the resolve parameter
        defined.
        """
        self._serviceName = serviceName
        self._session = session
        if serviceName not in self._methods or prefs.clusterMode == 'LOCAL':
            self._methods[serviceName] = self._WrapService(serviceName)
        for methodName, method in self._methods[serviceName].iteritems():
            setattr(self, methodName, types.MethodType(method, self, self.__class__))

    def __repr__(self):
        return '<ServiceProxy service=%s session=%s>' % (str(self._serviceName), str(self._session))

    def _WrapService(self, serviceName):
        """
        Inspects the service class referenced by serviceName and creates methods on the proxy class
        with matching names and arguments.
        """
        import svc
        serviceClass = getattr(svc, sm.GetServiceImplementation(serviceName))
        defaultResolve = getattr(serviceClass, '__serviceproxyresolve__', None)
        exportedCalls = getattr(serviceClass, '__exportedcalls__', {})
        exportedCalls = [ (k, v) for k, v in exportedCalls.iteritems() if isinstance(v, dict) ]
        wrappedMethods = {}
        for methodName, definition in exportedCalls:
            resolve = definition.get('resolve', defaultResolve)
            if resolve is not None:
                wrappedMethods[methodName] = self._WrapServiceMethod(methodName, getattr(serviceClass, methodName), resolve)

        return wrappedMethods

    def _WrapServiceMethod(self, methodName, method, resolve):
        """
        Creates new methods on the servcie proxy class which look like the methods on the remote
        service (including docs and function signature). Adds the additional layer which performs
        the node redirection based on one of the method arguments.
        """
        resolveConst, resolveArgument = resolve
        argspec = inspect.getargspec(method)
        if isinstance(resolveArgument, str):
            resolveArgumentIndex = argspec[0].index(resolveArgument) - 1
        elif isinstance(resolveArgument, int) and resolveArgument in const.cluster.NODES:
            resolveArgumentIndex = None
        else:
            raise RuntimeError("Resolve argument '%s' for ServiceProxy '%s' is invalid" % (str(resolveArgument), self))

        def wrapped(self, *args, **kwargs):
            """
            This is the actual method wrapper that will execute when we call an exported method on
            this ServiceProxy. It handles the runtime step of getting the resolveValue out of the
            provided arguments, looking up the right nodeID and executing the remote call with
            the session object.
            """
            try:
                if resolveArgumentIndex is None:
                    resolveValue = resolveArgument
                else:
                    resolveValue = kwargs.get(resolveArgument, args[resolveArgumentIndex])
                    if isinstance(resolveValue, basestring):
                        resolveValue = zlib.crc32(resolveValue)
                    elif resolveValue is None:
                        resolveValue = 0
            except ValueError:
                raise RuntimeError("ServiceProxy could not find the resolve argument '%s' for the method '%s'" % (str(resolveArgument), methodName))

            if resolveArgument == const.cluster.NODE_ALL:
                nodes = self._GetNodesFromServiceID(resolveConst, server=True, proxy=True)
            elif resolveArgument == const.cluster.NODE_ALL_SERVER:
                nodes = self._GetNodesFromServiceID(resolveConst, server=True)
            elif resolveArgument == const.cluster.NODE_ALL_PROXY:
                nodes = self._GetNodesFromServiceID(resolveConst, proxy=True)
            elif resolveArgument == const.cluster.NODE_ANY:
                nodes = random.choice(self._GetNodesFromServiceID(resolveConst, server=True, proxy=True))
            elif resolveArgument == const.cluster.NODE_ANY_SERVER:
                nodes = random.choice(self._GetNodesFromServiceID(resolveConst, server=True))
            elif resolveArgument == const.cluster.NODE_ANY_PROXY:
                nodes = random.choice(self._GetNodesFromServiceID(resolveConst, proxy=True))
            else:
                machoNet = sm.GetService('machoNet').session.ConnectToSolServerService('machoNet')
                serviceMod = const.cluster.SERVICE_MODS.get(resolveConst, const.cluster.SERVICE_MOD_DEFAULT)
                nodes = machoNet.GetNodeFromAddress(resolveConst, resolveValue % serviceMod)
            return ServiceProxyCall(self._session, self._serviceName, methodName, nodes)(*args, **kwargs)

        execdict = {'wrapped': wrapped}
        exec 'def %s%s: return wrapped(%s)' % (methodName, inspect.formatargspec(*argspec), ', '.join(argspec[0])) in execdict
        wrapped = execdict.get(methodName, wrapped)
        setattr(wrapped, '__doc__', method.__doc__)
        setattr(wrapped, '__name__', method.__name__)
        return wrapped

    def _GetNodesFromServiceID(self, serviceID, server = False, proxy = False):
        """
        Returns a complete list of nodeIDs running the service indicated by serviceID.
        """
        machoNet = sm.GetService('machoNet')
        serviceMask = 1 << serviceID - 1
        nodes = machoNet.ResolveServiceMaskToNodeIDs(serviceMask)
        if serviceMask & machoNet.serviceMask:
            nodes.add(machoNet.GetNodeID())
        if proxy == False:
            nodes = [ nodeID for nodeID in nodes if nodeID < const.maxNodeID ]
        if server == False:
            nodes = [ nodeID for nodeID in nodes if nodeID >= const.maxNodeID ]
        if not len(nodes):
            raise RuntimeError('ServiceProxy::GetNodesFromServiceID found no nodes for serviceID=%s (server=%s, proxy=%s)' % (serviceID, server, proxy))
        return list(nodes)


class ServiceProxyCall(object):
    """
    A callable object wrapper used by ServiceProxy for connecting to a remote service on one
    or many nodes. You can provide either a single nodeID and get a single response from the
    call, or by providing a list of nodes this will thread out multiple calls and wait for all
    of the responses before returning.
    """
    __guid__ = 'service.ServiceProxyCall'

    def __init__(self, session, serviceName, methodName, nodes):
        self._session = session
        self._serviceName = serviceName
        self._methodName = methodName
        self._nodes = nodes

    def __call__(self, *args, **kwargs):
        if not isinstance(self._nodes, (list, set, tuple)):
            return self._CallNode(self._nodes, *args, **kwargs)
        calls = [ (self._CallNode, [nodeID] + list(args), kwargs) for nodeID in self._nodes ]
        return uthread.parallel(calls)

    def _CallNode(self, nodeID, *args, **kwargs):
        service = self._session.ConnectToRemoteService(self._serviceName, nodeID=nodeID)
        return getattr(service, self._methodName)(*args, **kwargs)
