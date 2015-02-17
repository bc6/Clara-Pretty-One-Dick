#Embedded file name: stacklesslib/replacements\socket.py
from __future__ import absolute_import
import asyncore
from collections import deque
import gc
import logging
import select
import socket as stdsocket
import sys
import time
import types
import weakref
import stackless
VALUE_MAX_NONBLOCKINGREAD_SIZE = 1000000
VALUE_MAX_NONBLOCKINGREAD_CALLS = 100
asyncore.socket_map = weakref.WeakValueDictionary()
try:
    from errno import EALREADY, EINPROGRESS, EWOULDBLOCK, ECONNRESET, ENOTCONN, ESHUTDOWN, EINTR, EISCONN, EBADF, ECONNABORTED, ECONNREFUSED
except Exception:
    EALREADY = 37
    EINPROGRESS = 36
    EWOULDBLOCK = 35
    ECONNRESET = 54
    ENOTCONN = 57
    ESHUTDOWN = 58
    EINTR = 4
    EISCONN = 56
    EBADF = 9
    ECONNABORTED = 53
    ECONNREFUSED = 61

if '__all__' in stdsocket.__dict__:
    __all__ = stdsocket.__all__
    for k, v in stdsocket.__dict__.iteritems():
        if k in __all__:
            globals()[k] = v
        elif k == 'EBADF':
            globals()[k] = v

else:
    for k, v in stdsocket.__dict__.iteritems():
        if k.upper() == k:
            globals()[k] = v

    error = stdsocket.error
    timeout = stdsocket.timeout
    getaddrinfo = stdsocket.getaddrinfo
_fileobject = stdsocket._fileobject
managerRunning = False
poll_interval = 0.05

def ManageSockets():
    global poll_interval
    global managerRunning
    try:
        while len(asyncore.socket_map):
            asyncore.poll(poll_interval)
            _schedule_func()

    finally:
        managerRunning = False


def StartManager():
    global managerRunning
    if not managerRunning:
        managerRunning = True
        return stackless.tasklet(ManageSockets)()


_schedule_func = stackless.schedule
_manage_sockets_func = StartManager
_sleep_func = None
_timeout_func = None
_channel_refs = weakref.WeakSet()

def make_channel():
    c = stackless.channel()
    _channel_refs.add(c)
    return c


def can_timeout():
    return _sleep_func is not None or _timeout_func is not None


def stacklesssocket_manager(mgr):
    global _manage_sockets_func
    _manage_sockets_func = mgr


def socket(*args, **kwargs):
    import sys
    if 'socket' in sys.modules and sys.modules['socket'] is not stdsocket:
        raise RuntimeError("Use 'stacklesssocket.install' instead of replacing the 'socket' module")


_realsocket_old = stdsocket._realsocket
_socketobject_old = stdsocket._socketobject

class _socketobject_new(_socketobject_old):

    def __init__(self, family = AF_INET, type = SOCK_STREAM, proto = 0, _sock = None):
        if _sock is None:
            _sock = _realsocket_old(family, type, proto)
            _sock = _fakesocket(_sock)
            _manage_sockets_func()
        _socketobject_old.__init__(self, family, type, proto, _sock)
        if not isinstance(self._sock, _fakesocket):
            raise RuntimeError('bad socket')

    def accept(self):
        sock, addr = self._sock.accept()
        sock = _fakesocket(sock)
        sock.wasConnected = True
        return (_socketobject_new(_sock=sock), addr)

    accept.__doc__ = _socketobject_old.accept.__doc__


def make_blocking_socket(family = AF_INET, type = SOCK_STREAM, proto = 0):
    """
    Sometimes you may want to create a normal Python socket, even when
    monkey-patching is in effect.  One use case might be when you are trying to
    do socket operations on the last runnable tasklet, if these socket
    operations are on small writes on a non-connected UDP socket then you
    might as well just use a blocking socket, as the effect of blocking
    is negligible.
    """
    _sock = _realsocket_old(family, type, proto)
    return _socketobject_old(_sock=_sock)


def install(pi = None):
    global poll_interval
    if stdsocket._realsocket is socket:
        raise StandardError('Still installed')
    stdsocket._realsocket = socket
    stdsocket.socket = stdsocket.SocketType = stdsocket._socketobject = _socketobject_new
    if pi is not None:
        poll_interval = pi


def uninstall():
    stdsocket._realsocket = _realsocket_old
    stdsocket.socket = stdsocket.SocketType = stdsocket._socketobject = _socketobject_old


READY_TO_SCHEDULE_TAG = '_SET_ASIDE'

def ready_to_schedule(flag):
    """
    There may be cases where it is desirable to have socket operations happen before
    an application starts up its framework, which would then poll asyncore.  This
    function is intended to allow all sockets to be switched between working
    "stacklessly" or working directly on their underlying socket objects in a
    blocking manner.
    
    Note that sockets created while this is in effect lack attribute values that
    asyncore or this module may have set if the sockets were created in a full
    monkey patched manner.
    """

    def reroute_wrapper(funcName):

        def reroute_call(self, *args, **kwargs):
            if READY_TO_SCHEDULE_TAG not in _fakesocket.__dict__:
                return
            return getattr(self.socket, funcName)(*args, **kwargs)

        return reroute_call

    def update_method_referrers(methodName, oldClassMethod, newClassMethod):
        """
        The instance methods we need to update are stored in slots on instances of
        socket._socketobject (actually our replacement subclass _socketobject_new).
        """
        for referrer1 in gc.get_referrers(oldClassMethod):
            if isinstance(referrer1, types.MethodType):
                for referrer2 in gc.get_referrers(referrer1):
                    if isinstance(referrer2, _socketobject_new):
                        setattr(referrer2, methodName, types.MethodType(newClassMethod, referrer1.im_self, referrer1.im_class))

    if flag:
        if READY_TO_SCHEDULE_TAG not in _fakesocket.__dict__:
            return
        del _fakesocket.__dict__[READY_TO_SCHEDULE_TAG]
    else:
        _fakesocket.__dict__[READY_TO_SCHEDULE_TAG] = None
    for attributeName in dir(_realsocket_old):
        if not attributeName.startswith('_'):
            storageAttributeName = attributeName + '_SET_ASIDE'
            if flag:
                storedValue = _fakesocket.__dict__.pop(storageAttributeName, None)
                if storedValue is not None:
                    rerouteValue = _fakesocket.__dict__[attributeName]
                    _fakesocket.__dict__[attributeName] = storedValue
                    update_method_referrers(attributeName, rerouteValue, storedValue)
            else:
                if attributeName in _fakesocket.__dict__:
                    _fakesocket.__dict__[storageAttributeName] = _fakesocket.__dict__[attributeName]
                _fakesocket.__dict__[attributeName] = reroute_wrapper(attributeName)


if sys.version_info[0] == 2 and sys.version_info[1] == 6:

    class asyncore_dispatcher(asyncore.dispatcher):

        def handle_connect_event(self):
            err = self.socket.getsockopt(stdsocket.SOL_SOCKET, stdsocket.SO_ERROR)
            if err != 0:
                raise stdsocket.error(err, asyncore._strerror(err))
            super(asyncore_dispatcher, self).handle_connect_event()


else:
    asyncore_dispatcher = asyncore.dispatcher

class _fakesocket(asyncore_dispatcher):
    connectChannel = None
    acceptChannel = None
    wasConnected = False
    _timeout = None
    _blocking = True
    lastReadChannelRef = None
    lastReadTally = 0
    lastReadCalls = 0

    def __init__(self, realSocket):
        if not isinstance(realSocket, _realsocket_old):
            raise StandardError('An invalid socket passed to fakesocket %s' % realSocket.__class__)
        asyncore_dispatcher.__init__(self, realSocket)
        self.readQueue = deque()
        self.writeQueue = deque()
        self.sendToBuffers = deque()
        if can_timeout():
            self._timeout = stdsocket.getdefaulttimeout()

    def receive_with_timeout(self, channel):
        if self._timeout is not None:
            if _timeout_func is not None:
                _timeout_func(self._timeout, channel, (timeout, 'timed out'))
            elif _sleep_func is not None:
                stackless.tasklet(self._manage_receive_with_timeout)(channel)
            else:
                raise NotImplementedError('should not be here')
            try:
                ret = channel.receive()
            except BaseException as e:
                raise e

            return ret
        else:
            return channel.receive()

    def _manage_receive_with_timeout(self, channel):
        if channel.balance < 0:
            _sleep_func(self._timeout)
            if channel.balance < 0:
                channel.send_exception(timeout, 'timed out')

    def __del__(self):
        self.close()

    def __getattr__(self, attr):
        if not hasattr(self, 'socket'):
            raise AttributeError("socket attribute unset on '" + attr + "' lookup")
        return getattr(self.socket, attr)

    def readable(self):
        if self.socket.type == SOCK_DGRAM:
            return True
        if len(self.readQueue):
            return True
        if self.acceptChannel is not None and self.acceptChannel.balance < 0:
            return True
        if self.connectChannel is not None and self.connectChannel.balance < 0:
            return True
        return False

    def writable(self):
        if self.socket.type != SOCK_DGRAM and not self.connected:
            return True
        if len(self.writeQueue):
            return True
        if len(self.sendToBuffers):
            return True
        return False

    def accept(self):
        self._ensure_non_blocking_read()
        if not self.acceptChannel:
            self.acceptChannel = make_channel()
        return self.receive_with_timeout(self.acceptChannel)

    def connect(self, address):
        """
        If a timeout is set for the connection attempt, and the timeout occurs
        then it is the responsibility of the user to close the socket, should
        they not wish the connection to potentially establish anyway.
        """
        asyncore_dispatcher.connect(self, address)
        if self.socket.type != SOCK_DGRAM and not self.connected:
            if not self.connectChannel:
                self.connectChannel = make_channel()
                self.connectChannel.preference = 1
            self.receive_with_timeout(self.connectChannel)

    def _send(self, data, flags):
        self._ensure_connected()
        channel = make_channel()
        channel.preference = 1
        self.writeQueue.append((channel, flags, data))
        return self.receive_with_timeout(channel)

    def send(self, data, flags = 0):
        return self._send(data, flags)

    def sendall(self, data, flags = 0):
        while len(data):
            nbytes = self._send(data, flags)
            if nbytes == 0:
                raise Exception('completely unexpected situation, no data sent')
            data = data[nbytes:]

    def sendto(self, sendData, sendArg1 = None, sendArg2 = None):
        if sendArg2 is not None:
            flags = sendArg1
            sendAddress = sendArg2
        else:
            flags = 0
            sendAddress = sendArg1
        waitChannel = None
        for idx, (data, address, channel, sentBytes) in enumerate(self.sendToBuffers):
            if address == sendAddress:
                self.sendToBuffers[idx] = (data + sendData,
                 address,
                 channel,
                 sentBytes)
                waitChannel = channel
                break

        if waitChannel is None:
            waitChannel = make_channel()
            self.sendToBuffers.append((sendData,
             sendAddress,
             waitChannel,
             0))
        return self.receive_with_timeout(waitChannel)

    def _recv(self, methodName, args, sizeIdx = 0):
        self._ensure_non_blocking_read()
        if self._fileno is None:
            return ''
        if len(args) >= sizeIdx + 1:
            generalArgs = list(args)
            generalArgs[sizeIdx] = 0
            generalArgs = tuple(generalArgs)
        else:
            generalArgs = args
        while True:
            channel = None
            if self.lastReadChannelRef is not None and self.lastReadTally < VALUE_MAX_NONBLOCKINGREAD_SIZE and self.lastReadCalls < VALUE_MAX_NONBLOCKINGREAD_CALLS:
                channel = self.lastReadChannelRef()
                self.lastReadChannelRef = None
            if channel is None:
                channel = make_channel()
                channel.preference = -1
                self.lastReadTally = self.lastReadCalls = 0
                self.readQueue.append([channel, methodName, args])
            else:
                self.readQueue[0][1:] = (methodName, args)
            try:
                ret = self.receive_with_timeout(channel)
            except stdsocket.error as e:
                if isinstance(e, stdsocket.error) and e.args[0] == EWOULDBLOCK:
                    continue
                else:
                    raise

            break

        self.lastReadChannelRef = weakref.ref(channel)
        if isinstance(ret, types.StringTypes):
            recvlen = len(ret)
        elif methodName == 'recvfrom':
            recvlen = len(ret[0])
        elif methodName == 'recvfrom_into':
            recvlen = ret[0]
        else:
            recvlen = ret
        self.lastReadTally += recvlen
        self.lastReadCalls += 1
        return ret

    def recv(self, *args):
        if self.socket.type != SOCK_DGRAM and not self.connected:
            if not self.wasConnected:
                raise error(ENOTCONN, 'Socket is not connected')
        return self._recv('recv', args)

    def recv_into(self, *args):
        if self.socket.type != SOCK_DGRAM and not self.connected:
            if not self.wasConnected:
                raise error(ENOTCONN, 'Socket is not connected')
        return self._recv('recv_into', args, sizeIdx=1)

    def recvfrom(self, *args):
        return self._recv('recvfrom', args)

    def recvfrom_into(self, *args):
        return self._recv('recvfrom_into', args, sizeIdx=1)

    def close(self):
        if self._fileno is None:
            return
        asyncore_dispatcher.close(self)
        self.connected = False
        self.accepting = False
        while self.acceptChannel and self.acceptChannel.balance < 0:
            self.acceptChannel.send_exception(stdsocket.error, EBADF, 'Bad file descriptor')

        while self.connectChannel and self.connectChannel.balance < 0:
            self.connectChannel.send_exception(stdsocket.error, ECONNREFUSED, 'Connection refused')

        self._clear_queue(self.writeQueue, stdsocket.error, ECONNRESET)
        self._clear_queue(self.readQueue)

    def _clear_queue(self, queue, *args):
        for t in queue:
            if t[0].balance < 0:
                if len(args):
                    t[0].send_exception(*args)
                else:
                    t[0].send('')

        queue.clear()

    def fileno(self):
        return self.socket.fileno()

    def _is_non_blocking(self):
        return not self._blocking or self._timeout == 0.0

    def _ensure_non_blocking_read(self):
        if self._is_non_blocking():
            r, w, e = select.select([self], [], [], 0.0)
            if not r:
                raise stdsocket.error(EWOULDBLOCK, 'The socket operation could not complete without blocking')

    def _ensure_connected(self):
        if not self.connected:
            if not self.wasConnected:
                raise error(ENOTCONN, 'Socket is not connected')
            raise error(EBADF, 'Bad file descriptor')

    def setblocking(self, flag):
        self._blocking = flag

    def gettimeout(self):
        return self._timeout

    def settimeout(self, value):
        if value and not can_timeout():
            raise RuntimeError('This is a stackless socket - to have timeout support you need to provide a sleep function')
        self._timeout = value

    def handle_accept(self):
        if self.acceptChannel and self.acceptChannel.balance < 0:
            t = asyncore.dispatcher.accept(self)
            if t is None:
                return
            t[0].setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            stackless.tasklet(self.acceptChannel.send)(t)

    def handle_connect(self):
        if self.socket.type != SOCK_DGRAM:
            if self.connectChannel and self.connectChannel.balance < 0:
                self.wasConnected = True
                self.connectChannel.send(None)

    def handle_close(self):
        self.connected = False
        self.accepting = False
        if self.connectChannel is not None:
            self.close()

    def handle_expt(self):
        if False:
            import traceback
            print 'handle_expt: START'
            traceback.print_exc()
            print 'handle_expt: END'
        self.close()

    def handle_error(self):
        self.close()

    def handle_read(self):
        """
            This will be called once per-poll call per socket with data in its buffer to be read.
        
            If you call poll once every 30th of a second, then you are going to be rate limited
            in terms of how fast you can read incoming data by the packet size they arrive in.
            In order to deal with the worst case scenario, advantage is taken of how scheduling
            works in order to keep reading until there is no more data left to read.
        
            1.  This function is called indicating data is present to read.
            2.  The desired amount is read and a send call is made on the channel with it.
            3.  The function is blocked on that action and the tasklet it is running in is reinserted into the scheduler.
            4.  The tasklet that made the read related socket call is awakened with the given data.
            5.  It returns the data to the function that made that call.
            6.  The function that made the call makes another read related socket call.
                a) If the call is similar enough to the last call, then the previous channel is retrieved.
                b) Otherwise, a new channel is created.
            7.  The tasklet that is making the read related socket call is blocked on the channel.
            8.  This tasklet that was blocked sending gets scheduled again.
                a) If there is a tasklet blocked on the channel that it was using, then goto 2.
                b) Otherwise, the function exits.
        
            Note that if this function loops indefinitely, and the scheduler is pumped rather than
            continuously run, the pumping application will stay in its pump call for a prolonged
            period of time potentially starving the rest of the application for CPU time.
        
            An attempt is made in _recv to limit the amount of data read in this manner to a fixed
            amount and it lets this function exit if that amount is exceeded.  However, this it is
            up to the user of Stackless to understand how their application schedules and blocks,
            and there are situations where small reads may still effectively loop indefinitely.
        """
        if not len(self.readQueue):
            return
        channel, methodName, args = self.readQueue[0]
        fn = getattr(self.socket, methodName)
        while channel.balance < 0:
            args = self.readQueue[0][2]
            try:
                result = fn(*args)
            except Exception as e:
                if isinstance(e, stdsocket.error) and e.args[0] in [ECONNRESET,
                 ENOTCONN,
                 ESHUTDOWN,
                 ECONNABORTED]:
                    self.handle_close()
                    result = ''
                elif channel.balance < 0:
                    channel.send_exception(e.__class__, *e.args)

            if channel.balance < 0:
                channel.send(result)

        if len(self.readQueue) and self.readQueue[0][0] is channel:
            del self.readQueue[0]

    def handle_write(self):
        """
        This function still needs work WRT UDP.
        """
        if len(self.writeQueue):
            channel, flags, data = self.writeQueue[0]
            del self.writeQueue[0]

            def asyncore_send(self, data, flags = 0):
                try:
                    result = self.socket.send(data, flags)
                    return result
                except stdsocket.error as why:
                    if why.args[0] == EWOULDBLOCK:
                        return 0
                    channel.send_exception(why.__class__, *why.args)
                    if why.args[0] in (ECONNRESET,
                     ENOTCONN,
                     ESHUTDOWN,
                     ECONNABORTED):
                        self.handle_close()
                    return 0

            nbytes = asyncore_send(self, data, flags)
            if channel.balance < 0:
                channel.send(nbytes)
        elif len(self.sendToBuffers):
            data, address, channel, oldSentBytes = self.sendToBuffers[0]
            sentBytes = self.socket.sendto(data, address)
            totalSentBytes = oldSentBytes + sentBytes
            if len(data) > sentBytes:
                self.sendToBuffers[0] = (data[sentBytes:],
                 address,
                 channel,
                 totalSentBytes)
            else:
                del self.sendToBuffers[0]
                stackless.tasklet(channel.send)(totalSentBytes)


if False:

    def dump_socket_stack_traces():
        import traceback
        for skt in asyncore.socket_map.values():
            for k, v in skt.__dict__.items():
                if isinstance(v, stackless.channel) and v.queue:
                    i = 0
                    current = v.queue
                    while i == 0 or v.queue is not current:
                        print '%s.%s.%s' % (skt, k, i)
                        traceback.print_stack(v.queue.frame)
                        i += 1


if __name__ == '__main__':
    import struct
    testAddress = ('127.0.0.1', 3000)
    info = -12345678
    data = struct.pack('i', info)
    dataLength = len(data)

    def TestTCPServer(address):
        global data
        print 'server listen socket creation'
        listenSocket = stdsocket.socket(AF_INET, SOCK_STREAM)
        listenSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        listenSocket.bind(address)
        listenSocket.listen(5)
        NUM_TESTS = 2
        i = 1
        while i < NUM_TESTS + 1:
            print 'server connection wait', i
            currentSocket, clientAddress = listenSocket.accept()
            print 'server', i, 'listen socket', currentSocket.fileno(), 'from', clientAddress
            if i == 1:
                print 'server closing (a)', i, 'fd', currentSocket.fileno(), 'id', id(currentSocket)
                currentSocket.close()
                print 'server closed (a)', i
            elif i == 2:
                print 'server test', i, 'send'
                currentSocket.send(data)
                print 'server test', i, 'recv'
                if currentSocket.recv(4) != '':
                    print 'server recv(1)', i, 'FAIL'
                    break
                if currentSocket.recv(4) != '':
                    print 'server recv(2)', i, 'FAIL'
                    break
            else:
                print 'server closing (b)', i, 'fd', currentSocket.fileno(), 'id', id(currentSocket)
                currentSocket.close()
            print 'server test', i, 'OK'
            i += 1

        if i != NUM_TESTS + 1:
            print 'server: FAIL', i
        else:
            print 'server: OK', i
        print 'Done server'


    def TestTCPClient(address):
        global info
        global dataLength
        clientSocket = stdsocket.socket()
        clientSocket.connect(address)
        print 'client connection (1) fd', clientSocket.fileno(), 'id', id(clientSocket._sock), 'waiting to recv'
        if clientSocket.recv(5) != '':
            print 'client test', 1, 'FAIL'
        else:
            print 'client test', 1, 'OK'
        clientSocket = stdsocket.socket()
        clientSocket.connect(address)
        print 'client connection (2) fd', clientSocket.fileno(), 'id', id(clientSocket._sock), 'waiting to recv'
        s = clientSocket.recv(dataLength)
        if s == '':
            print 'client test', 2, 'FAIL (disconnect)'
        else:
            t = struct.unpack('i', s)
            if t[0] == info:
                print 'client test', 2, 'OK'
            else:
                print 'client test', 2, 'FAIL (wrong data)'
        print 'client exit'


    def TestMonkeyPatchUrllib(uri):
        install()
        try:
            import urllib
            f = urllib.urlopen(uri)
            if not isinstance(f.fp._sock, _fakesocket):
                raise AssertionError('failed to apply monkeypatch, got %s' % f.fp._sock.__class__)
            s = f.read()
            if len(s) != 0:
                print 'Fetched', len(s), 'bytes via replaced urllib'
            else:
                raise AssertionError('no text received?')
        finally:
            uninstall()


    def TestMonkeyPatchUDP(address):
        install()
        try:

            def UDPServer(address):
                listenSocket = stdsocket.socket(AF_INET, SOCK_DGRAM)
                listenSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                listenSocket.bind(address)
                print 'waiting to receive'
                rdata = ''
                while len(rdata) < 512:
                    data, address = listenSocket.recvfrom(4096)
                    print 'received', data, len(data)
                    rdata += data

            def UDPClient(address):
                clientSocket = stdsocket.socket(AF_INET, SOCK_DGRAM)
                print 'sending 512 byte packet'
                sentBytes = clientSocket.sendto('-' + '*' * 510 + '-', address)
                print 'sent 512 byte packet', sentBytes

            stackless.tasklet(UDPServer)(address)
            stackless.tasklet(UDPClient)(address)
            stackless.run()
        finally:
            uninstall()


    if 'notready' in sys.argv:
        sys.argv.remove('notready')
        ready_to_schedule(False)
    if len(sys.argv) == 2:
        if sys.argv[1] == 'client':
            print 'client started'
            TestTCPClient(testAddress)
            print 'client exited'
        elif sys.argv[1] == 'slpclient':
            print 'client started'
            stackless.tasklet(TestTCPClient)(testAddress)
            stackless.run()
            print 'client exited'
        elif sys.argv[1] == 'server':
            print 'server started'
            TestTCPServer(testAddress)
            print 'server exited'
        elif sys.argv[1] == 'slpserver':
            print 'server started'
            stackless.tasklet(TestTCPServer)(testAddress)
            stackless.run()
            print 'server exited'
        else:
            print 'Usage:', sys.argv[0], '[client|server|slpclient|slpserver]'
        sys.exit(1)
    else:
        print '* Running client/server test'
        install()
        try:
            stackless.tasklet(TestTCPServer)(testAddress)
            stackless.tasklet(TestTCPClient)(testAddress)
            stackless.run()
        finally:
            uninstall()

        print '* Running urllib test'
        stackless.tasklet(TestMonkeyPatchUrllib)('http://python.org/')
        stackless.run()
        print '* Running udp test'
        TestMonkeyPatchUDP(testAddress)
        print 'result: SUCCESS'
