#Embedded file name: carbon/client/script/entities\netStateClient.py
"""
A module for handling the replication of generic, low-frequency, CEF state changes.

Provides:
class NetStateClient - see the NetStateClient docstring for more info.

See also:
netStateServer.py
"""
import service

class NetStateClient(service.Service):
    """A CEF state-replication helper service.
    
    Provides a convenience layer to assist with replicating generic, low-frequency,
    entity state changes (via their constituent components).
    
    Co-operates with NetStateServer
    """
    __guid__ = 'svc.netStateClient'
    __notifyevents__ = ['OnReceiveNetState']

    def Run(self, *etc):
        self.IsVerboseMode = True

    def _LogVerbose(self, *args, **keywords):
        """Sent a message to the logging system, but only if we are in verbose mode."""
        if self.IsVerboseMode:
            self.LogInfo(args, keywords)

    def _ApplyEntityUpdates(self, ent, entityUpdates):
        for compName, componentUpdates in entityUpdates:
            component = getattr(ent, compName)
            self._ApplyComponentUpdates(component, componentUpdates)

    def _ApplyComponentUpdates(self, component, componentUpdates):
        for attrName, val in componentUpdates.iteritems():
            setattr(component, attrName, val)

    def OnReceiveNetState(self, entityID, entityUpdates):
        """Event handler for incoming <entityUpdates> from the NetStateServer."""
        receivingEntity = self.entityService.FindEntityByID(entityID)
        self._LogVerbose('OnReceiveNetState for', receivingEntity, 'ID:', entityID, 'with:', entityUpdates)
        self._ApplyEntityUpdates(receivingEntity, entityUpdates)
