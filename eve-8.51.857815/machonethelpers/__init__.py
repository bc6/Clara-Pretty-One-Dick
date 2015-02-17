#Embedded file name: machonethelpers\__init__.py
from carbon.common.lib.cluster import SERVICE_CLUSTERSINGLETON

class RemoteCallHelper(object):
    """
    Helper to connect to remote service based on how it resolve
    """

    def __init__(self, machoNet):
        self.machoNet = machoNet

    def GetRemoteSolarSystemBoundService(self, serviceName, solarSystemID):
        nodeID = self.machoNet.GetNodeFromAddress('beyonce', solarSystemID)
        return self.machoNet.ConnectToRemoteService(serviceName, nodeID)

    def GetClusterSingletonService(self, serviceName, numMod):
        nodeID = self.machoNet.GetNodeFromAddress(SERVICE_CLUSTERSINGLETON, numMod)
        return self.machoNet.ConnectToRemoteService(serviceName, nodeID)
