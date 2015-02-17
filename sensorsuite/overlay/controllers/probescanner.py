#Embedded file name: sensorsuite/overlay/controllers\probescanner.py
from eveexceptions.exceptionEater import ExceptionEater
from inventorycommon.const import groupCosmicAnomaly, groupCosmicSignature
import localization
from probescanning.const import probeScanGroupAnomalies, probeScanGroupSignatures
from sensorsuite.error import InvalidClientStateError
from sensorsuite.overlay import sitetype
from sensorsuite.overlay.anomalies import AnomalySiteData
from sensorsuite.overlay.signatures import SignatureSiteData
from sensorsuite.overlay.sitetype import SIGNATURE
from utillib import KeyVal
import logging
logger = logging.getLogger(__name__)

def GetSitesAsProbeResults(sites):
    results = []
    for site in sites:
        data = site.position if site.GetSiteType() == sitetype.ANOMALY else site.deviation
        pos = None if site.GetSiteType() == sitetype.ANOMALY else site.position
        results.append(KeyVal(id=site.targetID, certainty=site.signalStrength, prevCertainty=site.signalStrength, groupID=site.groupID, strengthAttributeID=site.scanStrengthAttribute, scanGroupID=probeScanGroupAnomalies if site.GetSiteType() == sitetype.ANOMALY else probeScanGroupSignatures, data=data, pos=pos, dungeonName=localization.GetByMessageID(site.dungeonNameID), dungeonNameID=site.dungeonNameID, typeID=groupCosmicAnomaly if site.GetSiteType() == sitetype.ANOMALY else groupCosmicSignature))

    return results


def SiteDataFromScanResult(result):
    if result.scanGroupID == probeScanGroupAnomalies:
        return AnomalySiteData(result.id, result.pos, result.id, None, result.dungeonNameID, None, None)
    else:
        return SignatureSiteData(result.id, result.pos, result.id, None, None, result.certainty, dungeonNameID=result.dungeonNameID)


class ProbeScannerController:

    def __init__(self, scanSvc, michelle, siteController):
        self.scanSvc = scanSvc
        self.michelle = michelle
        self.siteController = siteController

    def UpdateProbeResultBrackets(self):
        """
        Here we need to update the scan result with the latest signature scan results
        """
        updateSigData = set()
        for sigData in self.siteController.siteMaps.IterSitesByKey(SIGNATURE):
            with ExceptionEater('Updating signature overlay bracket'):
                result = self.scanSvc.GetResultForTargetID(sigData.targetID)
                if result is None:
                    continue
                if sigData.dungeonNameID is None:
                    dungeonNameID = result.get('dungeonNameID', None)
                    if dungeonNameID is not None:
                        sigData.dungeonNameID = dungeonNameID
                        updateSigData.add(sigData)
                if sigData.factionID is None:
                    factionID = result.get('factionID', None)
                    if factionID is not None:
                        sigData.factionID = factionID
                        updateSigData.add(sigData)
                if sigData.scanStrengthAttribute is None:
                    strengthAttributeID = result.get('strengthAttributeID', None)
                    if strengthAttributeID is not None:
                        sigData.scanStrengthAttribute = strengthAttributeID
                        updateSigData.add(sigData)
                if result['certainty'] > sigData.signalStrength and isinstance(result['data'], tuple):
                    sigData.signalStrength = result['certainty']
                    if result['certainty'] >= 1.0:
                        sigData.position = result['data']
                        bp = self.michelle.GetBallpark()
                        if bp is None:
                            raise InvalidClientStateError('ballpark not found')
                        if self.siteController.spaceLocations.ContainsSite(sigData.siteID):
                            ball = self.siteController.spaceLocations.GetBySiteID(sigData.siteID).ballRef()
                            bp.SetBallPosition(ball.id, *sigData.position)
                            self.siteController.NotifySiteChanged(sigData)
                    updateSigData.add(sigData)
            if updateSigData:
                for sigData_ in updateSigData:
                    self.UpdateScanData(sigData_)

    def UpdateScanData(self, sigData):
        bracket = self.siteController.spaceLocations.GetBracketBySiteID(sigData.siteID)
        if bracket:
            bracket.UpdateScanData()

    def GetCosmicAnomalyItemIDFromTargetID(self, targetID):
        for site in self.siteController.siteMaps.IterSitesByKey(sitetype.ANOMALY):
            if site.targetID == targetID:
                return site.siteID

    def GetAllSites(self):
        return GetSitesAsProbeResults(self.siteController.siteMaps.IterSitesByKeys(sitetype.SIGNATURE, sitetype.ANOMALY))

    def InjectSiteScanResults(self, sites):
        probeResults = GetSitesAsProbeResults(sites)
        self.scanSvc.InjectSitesAsScanResults(probeResults)
