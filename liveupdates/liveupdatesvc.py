#Embedded file name: liveupdates\liveupdatesvc.py
"""Live update service for EVE.
Should just be a very simple wrapper around
the common liveupdate functionality.

Perhaps some of this (module finding behavior?)
will move into the common library once DUST is hooked up to this system.
"""
import carbon.common.script.sys.service as service
from . import LiveUpdaterClientMixin

class LiveUpdateSvc(service.Service):
    __guid__ = 'svc.LiveUpdateSvc'
    __notifyevents__ = ['OnLiveClientUpdate']

    def __init__(self):
        self.liveUpdater = LiveUpdaterClientMixin()
        service.Service.__init__(self)

    def Enabled(self):
        return False

    def OnLiveClientUpdate(self, payload):
        if self.Enabled():
            self.liveUpdater.HandlePayload(payload)
