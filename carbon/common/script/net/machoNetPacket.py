#Embedded file name: carbon/common/script/net\machoNetPacket.py
"""
Implements a macho packet for machoNet
"""
import types
import carbon.common.script.sys.service as service
import carbon.common.script.net.machobase as machobase
from carbon.common.script.net.machoNetAddress import MachoAddress
globals().update(service.consts)
import log
import const

class MachoPacket():
    """
        A MachoPacket represents a single message crossing the wire.  It's only
        used as a base class for message type declarations.
    """
    __guid__ = 'macho.MachoPacket'
    __intorstringtype__ = (types.IntType, types.StringType, types.UnicodeType)
    __bizzarrerouters__ = (const.cluster.MACHONETMSG_TYPE_SESSIONCHANGENOTIFICATION,
     const.cluster.MACHONETMSG_TYPE_SESSIONINITIALSTATENOTIFICATION,
     const.cluster.MACHONETMSG_TYPE_PING_REQ,
     const.cluster.MACHONETMSG_TYPE_PING_RSP)

    def __init__(self, *args, **keywords):
        """
            Our constructor, which takes whatever parameters the message type
            declaration allows and gobbles up both keyword and normal arguments
            as provided.
        """
        self.userID = None
        self.compressedPart = 0
        self.source = MachoAddress()
        self.destination = MachoAddress()
        self.contextKey = None
        self.applicationID = None
        self.languageID = None
        self.oob = {}
        dtc = 0
        for each in keywords.iterkeys():
            if each != 'donttypecheck':
                setattr(self, each, keywords[each])
            else:
                dtc = 1

        self.command = self.__machodesc__['command']
        if not dtc:
            for each in self.__machodesc__['params']:
                if each[-1:] != '?':
                    if not hasattr(self, each):
                        raise TypeError('%s requires %s to be specified' % (self.__class__.__name__, each))

        self.pickleSize = 0

    def __getstate__(self):
        params = self.__machodesc__['params']
        body = [None] * len(params)
        for i in range(len(params)):
            if params[i].endswith('?'):
                tmp = params[i][:-1]
                if hasattr(self, tmp):
                    body[i] = getattr(self, tmp)
                else:
                    body.pop(-1)
                break
            else:
                body[i] = getattr(self, params[i])

        oob = None
        if self.oob or self.compressedPart:
            oob = self.oob
        if self.compressedPart:
            oob['compressedPart'] = self.compressedPart
        return (self.command,
         self.source,
         self.destination,
         self.userID,
         tuple(body),
         oob,
         self.contextKey,
         self.applicationID,
         self.languageID)

    def __setstate__(self, state):
        self.command, self.source, self.destination, self.userID, body, self.oob, self.contextKey, self.applicationID, self.languageID = state
        if self.oob is None:
            self.oob = {}
        self.compressedPart = self.oob.get('compressedPart', 0)
        params = self.__machodesc__['params']
        l = len(params)
        if len(body) < l:
            l = len(body)
        for i in range(l):
            if params[i].endswith('?'):
                tmp = params[i][:-1]
            else:
                tmp = params[i]
            setattr(self, tmp, body[i])

    def Response(self, *args, **keywords):
        """
            Returns a proper response to this message, if there is such a thing.
        
            Both keywords and normal arguments are supported.  The last argument may
            be optional.  See the message type declaration for details.
        """
        if not self.__machodesc__.has_key('response'):
            raise AttributeError(self.__class__.__name__, 'Response', 'There is no such thing as a response to a %s' % self.__class__.__name__)
        theResponse = apply(self.__machodesc__['response'], (), {'donttypecheck': 1})
        theResponse.source = self.destination
        theResponse.destination = self.source
        theResponse.userID = self.userID
        theResponse.contextKey = None
        theResponse.applicationID = None
        theResponse.languageId = None
        responseParams = theResponse.__machodesc__['params']
        i = 0
        for each in responseParams:
            if each.endswith('?'):
                if len(args) > i:
                    setattr(theResponse, each[:-1], args[i])
                break
            else:
                if len(args) <= i:
                    break
                setattr(theResponse, each, args[i])
            i = i + 1

        for each in keywords.iterkeys():
            if each not in responseParams:
                raise TypeError('%s.Response does not take %s as a parameter' % (self.__class__.__name__, each))
            setattr(theResponse, each, keywords[each])

        for each in responseParams:
            if not each.endswith('?') and not hasattr(theResponse, each):
                raise TypeError('%s.Response requires %s as a parameter, but it was not specified' % (self.__class__.__name__, each))

        return theResponse

    def ErrorResponse(self, code, payload):
        """
            returns an error response message for this dude, using the provided code and
            payload
        """
        theResponse = ErrorResponse(originalCommand=self.command, code=code, payload=payload)
        theResponse.source = self.destination
        theResponse.destination = self.source
        theResponse.userID = self.userID
        theResponse.contextKey = None
        theResponse.applicationID = None
        theResponse.languageID = None
        return theResponse

    def SetPickle(self, thePickle):
        """
            Sets the pickle, for forwarding and size stuff
        """
        self.__dict__['thePickle'] = thePickle
        self.__dict__['pickleSize'] = len(self.thePickle)

    def GetPickle(self):
        """
            Acquires a pickle for this message.  On the proxy, unless the message has actually
            been changed since it was read from the wire, there is no need to re-pickle.  The
            pickling function that is passed in is used to ensure that there is proper object
            caching performed.  Note that on the proxy, this doesn't really have to happen,
            since there isn't an object in the packet if this is a cached object.
        """
        if not hasattr(self, 'thePickle'):
            self.__dict__['thePickle'] = machobase.Dumps(self)
            self.__dict__['pickleSize'] = len(self.thePickle)
        return self.thePickle

    def GetPickleSize(self, machoNet):
        """
            returns the pickle size.
        """
        if not self.pickleSize:
            self.GetPickle()
        return self.pickleSize

    def Changed(self):
        """
            Call this if you change something in this message, in case it get's forwarded on.
        """
        if hasattr(self, 'thePickle'):
            delattr(self, 'thePickle')

    def RoutesTo(self, towhat):
        """
            Returns true if and only if 'towhat' is considered the destination of this message
            for any bizzarre reasons
        """
        if self.command in self.__bizzarrerouters__:
            return 1
        if self.command == const.cluster.MACHONETMSG_TYPE_AUTHENTICATION_REQ and machobase.mode == 'proxy':
            return 0
        return self.destination.RoutesTo(towhat, self.source)

    def __setattr__(self, attr, value):
        """
            Does the usual stuff, plus marks the message as changed if appropriate to ensure
            that old pickles are not forwarded
        """
        if hasattr(self, 'thePickle'):
            if hasattr(self, attr):
                curr = getattr(self, attr)
                if type(curr) not in self.__intorstringtype__ or type(value) not in self.__intorstringtype__ or curr != value:
                    self.Changed()
            else:
                self.Changed()
        self.__dict__[attr] = value

    def __repr__(self):
        try:
            if self.__guid__ == 'macho.AuthenticationReq':
                return 'Packet::AuthenticationReq(%s,%s,%s,%s,%s)' % (self.source,
                 self.destination,
                 self.clientinfo,
                 self.userName,
                 getattr(self, 'address', None))
            self.GetPickle()
            if len(self.thePickle) > 1500000:
                return 'Packet::%s (%s,%s,GENOCIDAL PAYLOAD(%d bytes),%s, %s)' % (self.__class__.__name__,
                 self.source,
                 self.destination,
                 len(self.thePickle),
                 self.oob,
                 self.contextKey)
            if len(self.thePickle) > 1000000:
                return 'Packet::%s (%s,%s,MURDEROUS PAYLOAD(%d bytes),%s, %s)' % (self.__class__.__name__,
                 self.source,
                 self.destination,
                 len(self.thePickle),
                 self.oob,
                 self.contextKey)
            if len(self.thePickle) > 100000:
                return 'Packet::%s (%s,%s,GARGANTUAN PAYLOAD(%d bytes),%s, %s)' % (self.__class__.__name__,
                 self.source,
                 self.destination,
                 len(self.thePickle),
                 self.oob,
                 self.contextKey)
            if len(self.thePickle) > 10000:
                return 'Packet::%s (%s,%s,HUGE PAYLOAD(%d bytes),%s, %s)' % (self.__class__.__name__,
                 self.source,
                 self.destination,
                 len(self.thePickle),
                 self.oob,
                 self.contextKey)
            if len(self.thePickle) > 1000:
                return 'Packet::%s (%s,%s,LARGE PAYLOAD(%d bytes),%s, %s)' % (self.__class__.__name__,
                 self.source,
                 self.destination,
                 len(self.thePickle),
                 self.oob,
                 self.contextKey)
            try:
                l = len(self.thePickle)
                params = []
                for each in self.__machodesc__['params']:
                    if each[-1:] == '?':
                        tmp = each[:-1]
                        if hasattr(self, tmp):
                            params.append(getattr(self, tmp))
                    else:
                        params.append(getattr(self, each))

                if hasattr(self, 'strayload'):
                    return 'Packet::%s (%s,%s,%s bytes,%s,%s, %s)' % (self.__class__.__name__,
                     self.source,
                     self.destination,
                     l,
                     self.strayload,
                     self.oob,
                     self.contextKey)
                return 'Packet::%s (%s,%s,%s bytes,%s,%s, %s)' % (self.__class__.__name__,
                 self.source,
                 self.destination,
                 l,
                 params,
                 self.oob,
                 self.contextKey)
            except Exception:
                log.LogException()
                return 'Packet::%s (CRAPPY TUPLE)' % self.__class__.__name__

        except Exception:
            log.LogException()
            return 'Packet containing crappy data'

    __str__ = __repr__


class ErrorResponse(MachoPacket):
    __guid__ = 'macho.ErrorResponse'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_ERRORRESPONSE,
     'params': ['originalCommand', 'code', 'payload']}


class IdentificationRsp(MachoPacket):
    __guid__ = 'macho.IdentificationRsp'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_IDENTIFICATION_RSP,
     'params': ['accepted',
                'nodeID',
                'others',
                'isProxy',
                'isApp',
                'serviceMask']}


class IdentificationReq(MachoPacket):
    __guid__ = 'macho.IdentificationReq'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_IDENTIFICATION_REQ,
     'params': ['nodeID',
                'myaddress',
                'others',
                'isProxy',
                'isApp',
                'serviceMask'],
     'response': IdentificationRsp}


class CallRsp(MachoPacket):
    __guid__ = 'macho.CallRsp'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_CALL_RSP,
     'params': ['payload']}


class CallReq(MachoPacket):
    __guid__ = 'macho.CallReq'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_CALL_REQ,
     'params': ['payload?'],
     'response': CallRsp}


class TransportClosed(MachoPacket):
    __guid__ = 'macho.TransportClosed'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_TRANSPORTCLOSED,
     'params': ['clientID', 'isRemote']}


class Notification(MachoPacket):
    __guid__ = 'macho.Notification'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_NOTIFICATION,
     'params': ['payload?']}


class SessionChangeNotification(MachoPacket):
    __guid__ = 'macho.SessionChangeNotification'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_SESSIONCHANGENOTIFICATION,
     'params': ['sid', 'change', 'nodesOfInterest?']}


class SessionInitialStateNotification(MachoPacket):
    __guid__ = 'macho.SessionInitialStateNotification'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_SESSIONINITIALSTATENOTIFICATION,
     'params': ['sid', 'sessionType', 'initialstate']}


class PingRsp(MachoPacket):
    __guid__ = 'macho.PingRsp'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_PING_RSP,
     'params': ['times']}


class PingReq(MachoPacket):
    __guid__ = 'macho.PingReq'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_PING_REQ,
     'response': PingRsp,
     'params': ['times']}


class MovementNotification(MachoPacket):
    __guid__ = 'macho.MovementNotification'
    __machodesc__ = {'command': const.cluster.MACHONETMSG_TYPE_MOVEMENTNOTIFICATION,
     'params': ['payload']}
