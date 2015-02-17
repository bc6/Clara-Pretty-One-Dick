#Embedded file name: carbon/common/script/net\addressCache.py
"""
Cache cluster addresses, it knows on which node a particular bound object is running.
This is basically a cache, it has no knowledge of how services are started or any
details on the mechanics to contact them.
"""

class AddressCache:
    __guid__ = 'gps.AddressCache'

    def __init__(self):
        self._addressCache = {}

    def Get(self, service, address):
        """
        Return the NodeID of a node running this service.
        Returns None if no node is running this service or we don't know which
        node is running it.
        """
        try:
            return self._addressCache[service, address]
        except KeyError:
            return None

    def Set(self, service, address, nodeID):
        """
        Set which node runs this particular service/address.
        Returns True if service/address had not been set to a node before.
        """
        key = (service, address)
        result = not self._addressCache.has_key(key)
        self._addressCache[key] = nodeID
        return result

    def Remove(self, service, address):
        """
        Remove which node runs this particluar bound object.
        Returns True if removed.
        """
        try:
            del self._addressCache[service, address]
            return True
        except KeyError:
            return False

    def RemoveAllForNode(self, nodeID):
        """
        In case of node death.  This removes all ServiceNode mappings for this node.
        """
        to_be_removed = []
        for k, v in self._addressCache.iteritems():
            if v == nodeID:
                to_be_removed.append(k)

        for k in to_be_removed:
            del self._addressCache[k]

    def GetSize(self):
        """
        Returns size of the address cache.
        """
        return len(self._addressCache)

    def Clear(self):
        """
        Clear out all cached addresses.
        """
        self._addressCache.clear()

    def GetNodeAddressMap(self):
        """
        Returns a map of nodeid to list of addresses (for debugging purposes)
        """
        nodeMap = {}
        for k, v in self._addressCache.iteritems():
            if v in nodeMap:
                nodeMap[v].append(k)
            else:
                nodeMap[v] = [k]

        return nodeMap
