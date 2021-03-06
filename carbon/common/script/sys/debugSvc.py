#Embedded file name: carbon/common/script/sys\debugSvc.py
import service
import sys
import traceback
import random
import macho
import base
import marshal
import cStringIO
import code
import pprint
import log
import blue
from collections import OrderedDict
import evecrypto.crypto as Crypto

class Utf8IO(object):
    """This will work once we move to 2.6, giving print a proper destination encoding """
    encoding = 'utf-8'

    def __init__(self):
        self._sio = cStringIO.StringIO()

    def __getattr__(self, attr):
        return getattr(self._sio, attr)


class debugSvc(service.Service):
    __guid__ = 'svc.debug'
    __displayname__ = 'Debug Service'
    __exportedcalls__ = {'Exec': [service.ROLE_PROGRAMMER],
     'Eval': [service.ROLE_PROGRAMMER],
     'Log': [service.ROLE_PROGRAMMER],
     'GetLogEvents': [service.ROLE_PROGRAMMER]}
    __notifyevents__ = ['OnRemoteExecute', 'OnDebugLog']
    __dependencies__ = ['machoNet']

    def Run(self, memStream = None):
        self.logEvents = {}

    def GetOptions(self):
        """ 
            This fucntion will return the options for the console web page. This produces a list of all the Solnodes, proxys, and conected sessions.
        """
        ret = OrderedDict()
        if boot.role == 'server':
            ret.update({'all': 'All Proxy and Sol Servers',
             'remote': 'Any Proxy',
             'local': 'Locally',
             'proxies': 'All Proxies',
             'servers': 'All Sol Servers'})
            for nodeID in sm.services['machoNet'].GetConnectedProxyNodes():
                transport = sm.services['machoNet'].GetTransportOfNode(nodeID)
                ret[nodeID] = 'Proxy %d (%s)' % (nodeID, transport.transport.address)

            for nodeID in sm.services['machoNet'].GetConnectedSolNodes():
                transport = sm.services['machoNet'].GetTransportOfNode(nodeID)
                ret[nodeID] = 'Sol %d (%s)' % (nodeID, transport.transport.address)

        else:
            ret.update({'all': 'All Proxy and Sol Servers',
             'remote': 'Any Proxy',
             'local': 'Locally',
             'proxies': 'All Proxies',
             'servers': 'All Sol Servers'})
            for nodeID in sm.services['machoNet'].GetConnectedProxyNodes():
                transport = sm.services['machoNet'].GetTransportOfNode(nodeID)
                ret[nodeID] = 'Proxy %d (%s)' % (nodeID, transport.transport.address)

            for nodeID in sm.services['machoNet'].GetConnectedSolNodes():
                transport = sm.services['machoNet'].GetTransportOfNode(nodeID)
                ret[nodeID] = 'Sol %d (%s)' % (nodeID, transport.transport.address)

        for s in base.GetSessions():
            clientID = getattr(s, 'clientID', None)
            if clientID and clientID / 10000000000L:
                charID = getattr(s, 'charid', None)
                userID = getattr(s, 'userid', None)
                if charID:
                    ret[-clientID] = self.GetClientDisplayString(clientID, charID)
                elif userID:
                    ret[-clientID] = 'Client #%d (user #%d)' % (clientID, userID)
                else:
                    ret[-clientID] = 'Client #%d' % clientID

        return ret

    def GetClientDisplayString(self, clientID, charID):
        """
            Return the display string for the options for this ClientId, CharId pair. The default is to display the charID number
            Derived classes can customize this display witht he Name of the character.
        """
        return 'Client #%d (char #%d)' % (clientID, charID)

    def Eval(self, code = None, signedCode = None, marshaledCode = None, **params):
        """
            This will evaluate code on the target on this Node.
        """
        if macho.mode == 'client':
            return
        if macho.mode == 'client' and signedCode is None:
            raise RuntimeError('Eval Failed - Must sign code for clients')
        if marshaledCode is not None:
            code = marshal.loads(marshaledCode)
        if signedCode is not None:
            marshaledCode, verified = Crypto.Verify(signedCode)
            if not verified:
                raise RuntimeError('Eval Failed - Signature Verification Failure')
            code = marshal.loads(marshaledCode)
        if not hasattr(session, 'debugContext'):
            session.__dict__['debugContext'] = {'__name__': 'debugContext',
             '__builtins__': __builtins__}
        session.debugContext.update(params)
        return eval(code, session.debugContext)

    def OnRemoteExecute(self, signedCode):
        """
            Execute a remote bit of signed code on this node, 
            this can be done from a machonet chain event.
        """
        if macho.mode != 'client':
            raise RuntimeError('OnRemoteExecute can only be called on the client')
        marshaledCode, verified = Crypto.Verify(signedCode)
        if not verified:
            raise RuntimeError('OnRemoteExecute Failed - Signature Verification Failure')
        code = marshal.loads(marshaledCode)
        self._Exec(code, {})

    def OnDebugLog(self, txt, lvl, isClient):
        """
        Allows log lines to be placed into the log remotely
        """
        if isClient and not macho.mode == 'client':
            return
        self.Log(txt, lvl)

    def Exec(self, code = None, signedCode = None, node = None, console = False, noprompt = False, **params):
        """ Execute a peice of signed code on this node """
        if macho.mode == 'client':
            return
        svc = None
        if node is not None:
            try:
                lnode = node.lower()
            except AttributeError:
                pass
            else:
                if lnode == 'remote':
                    if boot.role == 'server':
                        svc, many = self.session.ConnectToRemoteService('debug', random.choice(sm.services['machoNet'].GetConnectedProxyNodes())), False
                    else:
                        svc, many = self.session.ConnectToRemoteService('debug'), False
                elif lnode == 'proxies':
                    svc, many = self.session.ConnectToAllProxyServerServices('debug'), True
                elif lnode == 'servers':
                    svc, many = self.session.ConnectToAllSolServerServices('debug'), True
                elif lnode == 'all':
                    svc, many = self.session.ConnectToAllServices('debug'), True
                elif lnode == 'local':
                    svc = 0

            try:
                lnode = long(node)
            except ValueError:
                pass
            else:
                if lnode < 0:
                    svc, many = self.session.ConnectToClientService('debug', 'clientID', -lnode), False
                else:
                    svc, many = self.session.ConnectToRemoteService('debug', lnode), False

            if svc is None:
                raise RuntimeError('Exec failed: Invalid node %s' % repr(node))
        if not svc:
            if macho.mode == 'client' and signedCode is None:
                raise RuntimeError('Exec Failed - Must sign code for clients')
            if signedCode is not None:
                code, verified = Crypto.Verify(signedCode)
                if not verified:
                    raise RuntimeError('Exec Failed - Signature Verification Failure')
            if console:
                return self._ExecConsole(code, noprompt)
            else:
                return self._Exec(code, params)
        else:
            noprompt = many
            ret = svc.Exec(code, signedCode, None, console, noprompt, **params)
            if many:
                ret2 = dict([ (each[1], each[2]) for each in ret ])
                return pprint.pformat(ret2) + '\n'
            return ret

    def _Exec(self, code, params):
        """ 
            Do the code execution and return the results as a buffer
        """
        buffdude = cStringIO.StringIO()
        temp = (sys.stdout, sys.stderr)
        sys.stdout = buffdude
        sys.stderr = buffdude
        try:
            if not hasattr(session, 'debugContext'):
                session.__dict__['debugContext'] = {'__name__': 'debugContext',
                 '__builtins__': __builtins__}
            session.debugContext.update(params)
            exec code in session.debugContext
        except:
            traceback.print_exc()
            sys.exc_clear()
        finally:
            sys.stdout, sys.stderr = temp

        return buffdude.getvalue()

    def Log(self, txt, lvl):
        """
            Allows remote logging events to be written into the 'general' log channel
            If we are on a client it will add an additional log line with the session dump
            The log line is stored internally in a history cache
        """
        txt = str(txt)
        lvl = int(lvl)
        pst = ''
        if macho.mode == 'client':
            pre = '[ Debug ]'
            pst = repr(session)
        else:
            nodeID = sm.GetService('machoNet').GetNodeID()
            pre = '[ Debug ] - Node %s - ' % nodeID
        log.general.Log('%s %s' % (pre, txt), lvl)
        if pst:
            log.general.Log(pst, lvl)
        self.logEvents[blue.os.GetWallclockTimeNow()] = txt

    def GetLogEvents(self):
        return self.logEvents

    def _ExecConsole(self, text, noprompt):
        """ 
            Do the code execution and return the results as a buffer
        """
        buffdude = Utf8IO()
        temp = (sys.stdout, sys.stderr)
        sys.stdout = sys.stderr = buffdude
        try:
            if not hasattr(session, 'debugConsole'):
                session.debugConsole = code.InteractiveConsole()
            console = session.debugConsole
            if '\n' in text:
                symbol = 'exec'
                if not text.endswith('\n'):
                    text += '\n'
            else:
                symbol = 'single'
            if noprompt:
                console.push(text, symbol)
            else:
                print text
                incomplete = console.push(text, symbol)
                print '...' if incomplete else '>>>',
            if not noprompt:
                print '',
        finally:
            sys.stdout, sys.stderr = temp

        return buffdude.getvalue()
