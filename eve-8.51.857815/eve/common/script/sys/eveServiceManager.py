#Embedded file name: eve/common/script/sys\eveServiceManager.py
import carbon.common.script.sys.service as service

class DustNotEnabledError(Exception):
    __guid__ = 'exceptions.DustNotEnabledError'
    __persistvars__ = []

    def __init__(self):
        self.args = []

    def __repr__(self):
        return 'DUST is not currently enabled.  Please set enableDust=1 in your prefs to use DUST functionality.'


class FakeDustService(object):
    __dependencies__ = []
    __notifyevents__ = []
    __startupdependencies__ = []

    def __init__(self, serviceName):
        self.__guid__ = 'svc.' + serviceName
        self.state = service.SERVICE_STOPPED

    def __getattr__(self, key):
        """
        These fake services won't actually have any functionality, which is fine,
        since the whole point is that we don't want any DUST functionality available
        if the flag isn't set.  In fact, all code that would call to them should be
        guarded by the flag also.  In case it isn't, this case will provide a
        meaningful error indicating what is wrong.
        """
        raise DustNotEnabledError()

    Run = lambda *args: None
    LogInfo = lambda *args: None
    GetHtmlState = lambda *args: 'Fake, dust not enabled'
    GetServiceState = lambda *args: 'Faked'
    isLogInfo = 0
    isLogWarning = 0

    def SetLogInfo(self, b):
        pass

    def SetLogNotice(self, b):
        pass

    def SetLogWarning(self, b):
        pass
