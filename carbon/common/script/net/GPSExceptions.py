#Embedded file name: carbon/common/script/net\GPSExceptions.py
import blue
import eve.common.script.net.eveMachoNetVersion as eveMachoVersion
import exceptions

class GPSException(StandardError):
    __guid__ = 'exceptions.GPSException'

    def __init__(self, *args):
        super(GPSException, self).__init__(*args)
        self.reason = args[0] if args else None

    def __repr__(self):
        return '<%s: reason=%r, args[1:]=%r>' % (self.__class__.__name__, self.reason, self.args[1:])


class GPSTransportClosed(GPSException):
    __guid__ = 'exceptions.GPSTransportClosed'

    def __init__(self, reason = None, reasonCode = None, reasonArgs = {}, machoVersion = None, version = None, build = None, codename = None, region = None, origin = None, loggedOnUserCount = None, exception = None):
        args = (reason, exception) if exception else (reason,)
        super(GPSTransportClosed, self).__init__(*args)
        self.machoVersion = machoVersion or eveMachoVersion.machoVersion
        self.version = version or boot.version
        self.build = build or boot.build
        self.codename = str(codename or boot.codename)
        self.region = str(region or boot.region)
        self.loggedOnUserCount = loggedOnUserCount or 'machoNet' in sm.services and sm.services['machoNet'].GetClusterSessionCounts('EVE:Online')[0]
        self.origin = origin or boot.role
        self.clock = blue.os.GetWallclockTimeNow()
        self.reasonCode = reasonCode
        self.reasonArgs = reasonArgs

    def GetCloseArgs(self):
        args = {'reason': getattr(self, 'reason', None),
         'reasonCode': getattr(self, 'reasonCode', None),
         'reasonArgs': getattr(self, 'reasonArgs', None),
         'exception': self}
        return args


class GPSRemoteTransportClosed(GPSTransportClosed):
    __guid__ = 'exceptions.GPSRemoteTransportClosed'


class GPSBadAddress(GPSException):
    __guid__ = 'exceptions.GPSBadAddress'


class GPSAddressOccupied(GPSException):
    __guid__ = 'exceptions.GPSAddressOccupied'


import __builtin__
__builtin__.GPSException = GPSException
__builtin__.GPSTransportClosed = GPSTransportClosed
__builtin__.GPSBadAddress = GPSBadAddress
__builtin__.GPSAddressOccupied = GPSAddressOccupied
exceptions.GPSException = GPSException
exceptions.GPSRemoteTransportClosed = GPSRemoteTransportClosed
exceptions.GPSTransportClosed = GPSTransportClosed
exceptions.GPSBadAddress = GPSBadAddress
exceptions.GPSAddressOccupied = GPSAddressOccupied
