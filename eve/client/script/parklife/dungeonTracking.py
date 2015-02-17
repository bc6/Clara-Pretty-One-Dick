#Embedded file name: eve/client/script/parklife\dungeonTracking.py
import service
import localization
from eve.common.script.sys.rowset import Rowset

class DungeonTracking(service.Service):
    """
    Tracks what distribution/escalating path dungeons have been entered since last
    location session change
    """
    __guid__ = 'svc.dungeonTracking'
    __notifyevents__ = ['ProcessSessionChange', 'OnDistributionDungeonEntered', 'OnEscalatingPathDungeonEntered']

    def __init__(self):
        service.Service.__init__(self)
        self.distributionDungeonsEntered = None
        self.escalatingPathDungeonsEntered = None

    def Run(self, memStream = None):
        service.Service.Run(self, memStream)

    def ProcessSessionChange(self, isRemote, session, change):
        if change.has_key('locationid'):
            self.distributionDungeonsEntered = None
            self.escalatingPathDungeonsEntered = None

    def OnDistributionDungeonEntered(self, row):
        if self.distributionDungeonsEntered is None:
            self.distributionDungeonsEntered = Rowset(row.header)
        self.distributionDungeonsEntered.append(row)

    def OnEscalatingPathDungeonEntered(self, row):
        if self.escalatingPathDungeonsEntered is None:
            self.escalatingPathDungeonsEntered = Rowset(row.header)
        if row.dungeonNameID:
            row.name = localization.GetByMessageID(row.dungeonNameID)
        self.escalatingPathDungeonsEntered.append(row)

    def GetDistributionDungeonsEntered(self):
        return self.distributionDungeonsEntered

    def GetEscalatingPathDungeonsEntered(self):
        return self.escalatingPathDungeonsEntered
