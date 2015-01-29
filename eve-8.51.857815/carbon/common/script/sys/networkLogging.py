#Embedded file name: carbon/common/script/sys\networkLogging.py
import service
import blue

class NetworkLogging(service.Service):
    """
    A service which takes care of managing network logging
    """
    __guid__ = 'svc.networkLogging'
    __displayname__ = 'Network Logging'
    __exportedcalls__ = {'StartNetworkLogging': [service.ROLE_SERVICE],
     'StopNetworkLogging': [service.ROLE_SERVICE],
     'GetLoggingState': [service.ROLE_SERVICE]}

    def StartNetworkLogging(self, server, port, threshold):
        """
        Start network logging on this node
        """
        if server and port:
            return blue.EnableNetworkLogging(server, int(port), boot.role, int(threshold))

    def StopNetworkLogging(self):
        """
        Stops network logging on this node
        """
        return blue.DisableNetworkLogging()

    def GetLoggingState(self):
        """
        Returns the network logging state of this node
        """
        return blue.GetNetworkLoggingState()
