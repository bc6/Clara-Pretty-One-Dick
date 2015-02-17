#Embedded file name: eve/client/script/ui/inflight\warpableResultBracket.py
from eve.client.script.ui.inflight.bracket import SimpleBracket
from inventorycommon.const import groupCosmicAnomaly
from sensorsuite.overlay.controllers.probescanner import SiteDataFromScanResult

class WarpableResultBracket(SimpleBracket):

    def GetMenu(self):
        scanSvc = sm.GetService('scanSvc')
        scanResult = SiteDataFromScanResult(self.result)
        if self.result.groupID == groupCosmicAnomaly:
            return scanSvc.GetScanResultMenuWithoutIgnore(scanResult)
        else:
            return scanSvc.GetScanResultMenuWithIgnore(scanResult, self.result.groupID)
